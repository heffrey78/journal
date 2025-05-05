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
                "INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.title,
                    file_path,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat() if entry.updated_at else None,
                    json.dumps(entry.tags),
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
            query = """SELECT id, title, file_path, created_at, updated_at, tags
                    FROM entries WHERE id = ?"""
            cursor.execute(query, (entry_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Extract metadata
            id, title, file_path, created_at, updated_at, tags_json = row

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
    ) -> List[JournalEntry]:
        """
        Retrieve a list of journal entries, ordered by creation date
        (newest first). Optionally filter by date range and tags.

        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional list of tags for filtering

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
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """
        Perform a simple text search across journal entries.
        Can be filtered by date range and tags.

        Args:
            query: The search query
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional list of tags for filtering
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
