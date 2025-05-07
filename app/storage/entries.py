import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.storage.base import BaseStorage
from app.models import JournalEntry


class EntryStorage(BaseStorage):
    """Handles journal entry storage and retrieval."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize the entry storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._entry_cache = {}
        self._cache_size = 50
        self._init_table()

    def _init_table(self):
        """Initialize the entries table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Check if we need to perform a migration
        cursor.execute("PRAGMA table_info(entries)")
        columns = {row[1] for row in cursor.fetchall()}

        if (
            "folder" not in columns
            or "favorite" not in columns
            or "images" not in columns
        ):
            # Migration needed - create new schema
            cursor.execute("BEGIN TRANSACTION")
            try:
                # Rename old table
                cursor.execute("ALTER TABLE entries RENAME TO entries_old")

                # Create new table with updated schema
                cursor.execute(
                    """
                    CREATE TABLE entries (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT,
                        tags TEXT,
                        folder TEXT,
                        favorite INTEGER DEFAULT 0,
                        images TEXT
                    )
                    """
                )

                # Copy data from old table to new, with defaults for new columns
                cursor.execute(
                    """
                    INSERT INTO entries "
                    "(id, title, file_path, created_at, "
                    "updated_at, tags, folder, favorite, images)
                    SELECT id, title, file_path, created_at, "
                    "updated_at, tags, NULL, 0, '[]'
                    FROM entries_old
                    """
                )

                # Drop old table
                cursor.execute("DROP TABLE entries_old")
                cursor.execute("COMMIT")
                print(
                    "Database migration complete: Added folder, favorite, "
                    "and images fields"
                )
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Database migration failed: {str(e)}")
                # Fall back to creating the original schema if migration fails
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entries (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT,
                        tags TEXT
                    )
                    """
                )
        else:
            # Table exists with all needed columns
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    tags TEXT,
                    folder TEXT,
                    favorite INTEGER DEFAULT 0,
                    images TEXT
                )
                """
            )

        # Create index for folder to improve performance when filtering by folder
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_folder ON entries(folder)"
        )

        # Create index for favorite to improve performance when filtering favorites
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_favorite ON entries(favorite)"
        )

        # Create folders table for empty folders
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                name TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def save_entry(self, entry: JournalEntry) -> str:
        """
        Save a journal entry to both filesystem (as markdown) and SQLite database.

        Args:
            entry: The JournalEntry object to save

        Returns:
            The ID of the saved entry
        """
        # Set updated_at if not set
        if not entry.updated_at:
            entry.updated_at = entry.created_at

        # Save markdown to file
        file_path = os.path.join(self.entries_dir, f"{entry.id}.md")
        with open(file_path, "w") as f:
            f.write(f"# {entry.title}\n\n{entry.content}")

        # Save metadata to SQLite
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.title,
                    file_path,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat() if entry.updated_at else None,
                    json.dumps(entry.tags),
                    entry.folder,
                    1 if entry.favorite else 0,
                    json.dumps(entry.images),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        # Update cache
        self._entry_cache[entry.id] = entry

        return entry.id

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """
        Retrieve a journal entry by its ID.

        Args:
            entry_id: The ID of the entry to retrieve

        Returns:
            JournalEntry object if found, None otherwise
        """
        # Check cache first
        if entry_id in self._entry_cache:
            return self._entry_cache[entry_id]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            query = """SELECT id, title, file_path, created_at, updated_at, tags, "
            "folder, favorite, images
                    FROM entries WHERE id = ?"""
            cursor.execute(query, (entry_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Extract metadata
            (
                id,
                title,
                file_path,
                created_at,
                updated_at,
                tags_json,
                folder,
                favorite,
                images_json,
            ) = row

            # Read content from file
            if not os.path.exists(file_path):
                return None

            with open(file_path, "r") as f:
                content = f.read()
                # Remove the title header from content as it's stored separately
                if content.startswith(f"# {title}"):
                    # Remove whitespace before colon in slice
                    content = content[len(f"# {title}") :]  # noqa: E203
                content = content.strip()

            # Create JournalEntry object
            entry = JournalEntry(
                id=id,
                title=title,
                content=content,
                created_at=datetime.fromisoformat(created_at),
                updated_at=(datetime.fromisoformat(updated_at) if updated_at else None),
                tags=json.loads(tags_json) if tags_json else [],
                folder=folder,
                favorite=bool(favorite),
                images=json.loads(images_json) if images_json else [],
            )

            # Add to cache
            if len(self._entry_cache) >= self._cache_size:
                self._entry_cache.pop(next(iter(self._entry_cache)))
            self._entry_cache[entry_id] = entry

            return entry
        finally:
            conn.close()

    def update_entry(
        self, entry_id: str, update_data: Dict[str, Any]
    ) -> Optional[JournalEntry]:
        """
        Update an existing journal entry with new data.

        Args:
            entry_id: The ID of the entry to update
            update_data: Dictionary containing fields to update

        Returns:
            Updated JournalEntry object if successful, None if entry not found
        """
        # First get the existing entry
        entry = self.get_entry(entry_id)
        if not entry:
            return None

        # Update fields based on provided data
        if "title" in update_data:
            entry.title = update_data["title"]

        if "content" in update_data:
            entry.update_content(update_data["content"])

        if "tags" in update_data:
            entry.tags = update_data["tags"]

        if "folder" in update_data:
            entry.folder = update_data["folder"]

        if "favorite" in update_data:
            entry.favorite = update_data["favorite"]

        if "images" in update_data:
            entry.images = update_data["images"]

        # Always update the updated_at timestamp
        entry.updated_at = datetime.now()

        # Save the updated entry
        self.save_entry(entry)
        return entry

    def get_entries(
        self,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        favorite: Optional[bool] = None,
    ) -> List[JournalEntry]:
        """
        Retrieve a list of journal entries, ordered by creation date
        (newest first). Optionally filter by date range, tags, folder,
        and favorite status.

        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional list of tags for filtering
            folder: Optional folder path for filtering
            favorite: Optional favorite status for filtering

        Returns:
            List of JournalEntry objects
        """
        entries = []
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            query_parts = ["SELECT id FROM entries"]
            params = []
            where_clauses = []

            # Add date range filter if provided
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from.isoformat())

            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to.isoformat())

            # Add tag filter if provided
            if tags and len(tags) > 0:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{json.dumps(tag)[1:-1]}%")
                where_clauses.append(f"({' OR '.join(tag_conditions)})")

            # Add folder filter if provided
            if folder is not None:
                where_clauses.append("folder = ?")
                params.append(folder)

            # Add favorite filter if provided
            if favorite is not None:
                where_clauses.append("favorite = ?")
                params.append(1 if favorite else 0)

            # Build the final query
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))

            query_parts.append("ORDER BY created_at DESC LIMIT ? OFFSET ?")
            params.extend([limit, offset])

            cursor.execute(" ".join(query_parts), tuple(params))
            rows = cursor.fetchall()

            for row in rows:
                entry_id = row[0]
                entry = self.get_entry(entry_id)
                if entry:
                    entries.append(entry)
        finally:
            conn.close()

        return entries

    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a journal entry by its ID.

        Args:
            entry_id: The ID of the entry to delete

        Returns:
            True if the entry was deleted, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Get file path before deleting from database
            cursor.execute("SELECT file_path FROM entries WHERE id = ?", (entry_id,))
            row = cursor.fetchone()

            if not row:
                return False

            file_path = row[0]

            # Delete from database
            cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.commit()

            # Delete file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)

            # Remove from cache if present
            if entry_id in self._entry_cache:
                del self._entry_cache[entry_id]

            return True
        finally:
            conn.close()

    def get_entry_by_title(self, title: str) -> Optional[JournalEntry]:
        """
        Find a journal entry by its title.

        Args:
            title: The title to search for

        Returns:
            JournalEntry object if found, None otherwise
        """
        conn = self.get_db_connection()
        conn.create_function("LOWER", 1, lambda x: x.lower() if x else None)
        cursor = conn.cursor()
        try:
            query = """SELECT id FROM entries WHERE LOWER(title) = ? LIMIT 1"""
            cursor.execute(query, (title.lower(),))
            row = cursor.fetchone()

            if not row:
                return None

            return self.get_entry(row[0])
        finally:
            conn.close()

    def text_search(
        self,
        query: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        favorite: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """
        Perform a simple text search across journal entries.
        Can be filtered by date range, tags, folder, and favorite status.

        Args:
            query: The search query
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional list of tags for filtering
            folder: Optional folder path for filtering
            favorite: Optional favorite status for filtering
            limit: Maximum number of entries to return (default: 100)
            offset: Number of entries to skip for pagination (default: 0)

        Returns:
            List of JournalEntry objects that match the query
        """
        # If query is empty, return entries that match other filters
        if not query.strip():
            return self.get_entries(
                limit=limit,
                offset=offset,
                date_from=date_from,
                date_to=date_to,
                tags=tags,
                folder=folder,
                favorite=favorite,
            )

        entries = []
        conn = self.get_db_connection()
        conn.create_function("LOWER", 1, lambda x: x.lower() if x else None)
        cursor = conn.cursor()

        try:
            # Get all entries
            params = []
            where_clauses = []

            # Add date range filter if provided
            if date_from:
                where_clauses.append("created_at >= ?")
                params.append(date_from.isoformat())

            if date_to:
                where_clauses.append("created_at <= ?")
                params.append(date_to.isoformat())

            # Add tag filter if provided
            if tags and len(tags) > 0:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{json.dumps(tag)[1:-1]}%")
                if tag_conditions:
                    where_clauses.append(f"({' OR '.join(tag_conditions)})")

            # Add folder filter if provided
            if folder is not None:
                where_clauses.append("folder = ?")
                params.append(folder)

            # Add favorite filter if provided
            if favorite is not None:
                where_clauses.append("favorite = ?")
                params.append(1 if favorite else 0)

            # Build query to get all entries meeting filter criteria
            query_sql = "SELECT id, file_path, title, tags FROM entries"
            if where_clauses:
                query_sql += " WHERE " + " AND ".join(where_clauses)

            # Execute query
            cursor.execute(query_sql, tuple(params))
            rows = cursor.fetchall()

            # Process search terms
            search_terms = query.lower().split()

            for row in rows:
                entry_id, file_path, title, tags_json = row

                # Check title for matches
                if any(term in title.lower() for term in search_terms):
                    entry = self.get_entry(entry_id)
                    if entry:
                        entries.append(entry)
                        continue

                # Check tags for matches
                if tags_json:
                    entry_tags = json.loads(tags_json)
                    if any(
                        any(term in tag.lower() for term in search_terms)
                        for tag in entry_tags
                    ):
                        entry = self.get_entry(entry_id)
                        if entry:
                            entries.append(entry)
                        continue

                # Check file content
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        content = f.read().lower()
                        if any(term in content for term in search_terms):
                            entry = self.get_entry(entry_id)
                            if entry:
                                entries.append(entry)

            # Apply pagination after all search results are collected
            paginated_entries = entries[offset : offset + limit]  # noqa: E203

            return paginated_entries
        finally:
            conn.close()

    def _apply_filters(
        self,
        entries: List[JournalEntry],
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[JournalEntry]:
        """
        Apply filters to a list of entries.

        Args:
            entries: List of JournalEntry objects to filter
            tags: Optional list of tags to filter by
            date_from: Optional start date to filter by
            date_to: Optional end date to filter by

        Returns:
            Filtered list of JournalEntry objects
        """
        filtered = entries

        # Filter by tags
        if tags and len(tags) > 0:
            # Split the overly long line into two parts
            filtered = [
                e
                for e in filtered
                if any(tag.lower() in [t.lower() for t in e.tags] for tag in tags)
            ]

        # Filter by date range
        if date_from:
            filtered = [e for e in filtered if e.created_at >= date_from]

        if date_to:
            filtered = [e for e in filtered if e.created_at <= date_to]

        return filtered

    def get_folders(self) -> List[str]:
        """
        Get a list of all unique folders used in the journal.
        This includes both folders that contain entries and empty folders.

        Returns:
            List of folder names/paths
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        folders = set()

        try:
            # Get folders from entries table
            cursor.execute(
                "SELECT DISTINCT folder FROM entries WHERE folder IS NOT NULL"
            )
            for row in cursor.fetchall():
                folders.add(row[0])

            # Get folders from dedicated folders table (if it exists)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='folders'"
            )
            if cursor.fetchone():
                cursor.execute("SELECT name FROM folders")
                for row in cursor.fetchall():
                    folders.add(row[0])

            return list(folders)
        finally:
            conn.close()

    def get_entries_by_folder(
        self,
        folder: str,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[JournalEntry]:
        """
        Get entries in a specific folder, with optional date filtering.

        Args:
            folder: The folder path to filter by
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering

        Returns:
            List of JournalEntry objects in the specified folder
        """
        # URL decoding if needed
        import urllib.parse

        try:
            if "%" in folder:
                folder = urllib.parse.unquote(folder)
        except Exception:
            # If URL decoding fails, just use the original folder name
            pass

        # Return empty list for empty string or None
        if not folder:
            return []

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Check if folder exists in entries table
            cursor.execute("SELECT COUNT(*) FROM entries WHERE folder = ?", (folder,))
            has_entries = cursor.fetchone()[0] > 0

            # If no entries with this folder, check if it's an empty folder
            if not has_entries:
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='folders'"
                )
                if cursor.fetchone():  # Table exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM folders WHERE name = ?", (folder,)
                    )
                    folder_exists = cursor.fetchone()[0] > 0
                    if not folder_exists:
                        # Folder doesn't exist at all
                        return []
                    else:
                        # Folder exists but is empty - explicitly return empty list
                        return []
        finally:
            conn.close()

        # Folder exists with entries, proceed with normal query
        return self.get_entries(
            limit=limit,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            folder=folder,
        )

    def get_entries_by_date(
        self,
        date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """
        Get entries created on a specific date for calendar view.

        Args:
            date: The date to filter by (only year, month, day are used)
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination

        Returns:
            List of JournalEntry objects created on the specified date
        """
        # Extract just the date part and create start/end datetime objects
        start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_date = datetime(date.year, date.month, date.day, 23, 59, 59)

        return self.get_entries(
            limit=limit,
            offset=offset,
            date_from=start_date,
            date_to=end_date,
        )

    def get_favorite_entries(
        self,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> List[JournalEntry]:
        """
        Get favorite entries with optional filtering.

        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional tags to filter by

        Returns:
            List of favorite JournalEntry objects
        """
        return self.get_entries(
            limit=limit,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            tags=tags,
            favorite=True,
        )

    def batch_update_folder(
        self,
        entry_ids: List[str],
        folder: Optional[str],
    ) -> int:
        """
        Update the folder for multiple entries at once.

        Args:
            entry_ids: List of entry IDs to update
            folder: New folder value (None to remove from folders)

        Returns:
            Number of entries successfully updated
        """
        if not entry_ids:
            return 0

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Use placeholders for each ID in the WHERE clause
            placeholders = ", ".join(["?" for _ in entry_ids])

            # Update the folder for all specified entries
            cursor.execute(
                "UPDATE entries SET folder = ?, updated_at = ? "
                f"WHERE id IN ({placeholders})",
                [folder, datetime.now().isoformat()] + entry_ids,
            )

            conn.commit()

            # Return count of updated rows
            updated_count = cursor.rowcount

            # Clear cache for updated entries
            for entry_id in entry_ids:
                if entry_id in self._entry_cache:
                    del self._entry_cache[entry_id]

            return updated_count
        finally:
            conn.close()

    def batch_toggle_favorite(
        self,
        entry_ids: List[str],
        favorite: bool,
    ) -> int:
        """
        Set favorite status for multiple entries at once.

        Args:
            entry_ids: List of entry IDs to update
            favorite: New favorite status

        Returns:
            Number of entries successfully updated
        """
        if not entry_ids:
            return 0

        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Use placeholders for each ID in the WHERE clause
            placeholders = ", ".join(["?" for _ in entry_ids])

            # Update the favorite status for all specified entries
            cursor.execute(
                "UPDATE entries SET favorite = ?, updated_at = ? "
                f"WHERE id IN ({placeholders})",
                [1 if favorite else 0, datetime.now().isoformat()] + entry_ids,
            )

            conn.commit()

            # Return count of updated rows
            updated_count = cursor.rowcount

            # Clear cache for updated entries
            for entry_id in entry_ids:
                if entry_id in self._entry_cache:
                    del self._entry_cache[entry_id]

            return updated_count
        finally:
            conn.close()

    def create_folder(self, folder_name: str) -> bool:
        """
        Create a new folder in the journal system.

        Since folders are implemented as metadata and not actual directories,
        this function adds an entry in a special table to track empty folders.

        Args:
            folder_name: Name of the folder to create

        Returns:
            True if the folder was created successfully, False otherwise
        """
        if not folder_name or folder_name.strip() == "":
            return False

        folder_name = folder_name.strip()
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # First check if the folder already exists in entries
            cursor.execute(
                "SELECT COUNT(*) FROM entries WHERE folder = ?", (folder_name,)
            )
            if cursor.fetchone()[0] > 0:
                # Folder already exists with entries
                return True

            # Check if the folders table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='folders'"
            )
            if not cursor.fetchone():
                # Create the folders table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS folders (
                        name TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL
                    )
                """
                )
                conn.commit()

            # Check if the folder already exists in the folders table
            cursor.execute(
                "SELECT COUNT(*) FROM folders WHERE name = ?", (folder_name,)
            )
            if cursor.fetchone()[0] > 0:
                # Folder already exists in the folders table
                return True

            # Add the folder since it doesn't exist yet
            cursor.execute(
                "INSERT INTO folders (name, created_at) VALUES (?, ?)",
                (folder_name, datetime.now().isoformat()),
            )
            conn.commit()
            return True
        except Exception as e:
            # Log the error properly
            import traceback

            print(f"Error creating folder: {str(e)}")
            print(traceback.format_exc())
            # Rollback any changes
            conn.rollback()
            return False
        finally:
            conn.close()
