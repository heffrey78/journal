import os
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import JournalEntry


class StorageManager:
    """
    Manages the storage of journal entries in both filesystem and SQLite database.

    This implementation focuses on basic storage without vector DB functionality.
    """

    def __init__(self, base_dir="./journal_data"):
        # Setup directory structure
        self.base_dir = base_dir
        self.entries_dir = os.path.join(base_dir, "entries")
        self.db_path = os.path.join(base_dir, "journal.db")

        # Ensure directories exist
        os.makedirs(self.entries_dir, exist_ok=True)

        # Initialize SQLite for metadata
        self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database with the necessary schema."""
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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

        return entry.id

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

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """
        Retrieve a journal entry by its ID.

        Args:
            entry_id: The ID of the entry to retrieve

        Returns:
            JournalEntry object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
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
                # fmt: off
                if content.startswith(f"# {title}"):
                    content = content[len(f"# {title}"):]
                # fmt: on
                content = content.strip()

            # Create JournalEntry object
            return JournalEntry(
                id=id,
                title=title,
                content=content,
                created_at=datetime.fromisoformat(created_at),
                updated_at=(datetime.fromisoformat(updated_at) if updated_at else None),
                tags=json.loads(tags_json) if tags_json else [],
            )
        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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

            return True
        finally:
            conn.close()

    def text_search(
        self,
        query: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> List[JournalEntry]:
        """
        Perform a simple text search across journal entries.
        Can be filtered by date range and tags.

        Args:
            query: The search query
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            tags: Optional list of tags for filtering

        Returns:
            List of JournalEntry objects that match the query
        """
        entries = []
        conn = sqlite3.connect(self.db_path)
        conn.create_function("LOWER", 1, lambda x: x.lower() if x else None)
        cursor = conn.cursor()
        try:
            query_parts = [
                """
                SELECT id FROM entries
                WHERE (LOWER(title) LIKE ? OR id IN (
                    SELECT id FROM entries WHERE EXISTS (
                        SELECT 1 FROM json_each(tags)
                        WHERE LOWER(json_each.value) LIKE ?
                    )
                ))
                """
            ]
            params = [f"%{query.lower()}%", f"%{query.lower()}%"]

            # Add date range filter if provided
            if date_from:
                query_parts.append("AND created_at >= ?")
                params.append(date_from.isoformat())

            if date_to:
                query_parts.append("AND created_at <= ?")
                params.append(date_to.isoformat())

            # Add tag filter if provided
            if tags and len(tags) > 0:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{json.dumps(tag)[1:-1]}%")
                query_parts.append(f"AND ({' OR '.join(tag_conditions)})")

            query_parts.append("ORDER BY created_at DESC")

            cursor.execute(" ".join(query_parts), tuple(params))
            rows = cursor.fetchall()

            # Store matching entries by ID to prevent duplicates
            matching_ids = {row[0] for row in rows}

            # For content search, we need to check the files directly
            cursor.execute("SELECT id, file_path FROM entries")
            all_entries = cursor.fetchall()

            for entry_id, file_path in all_entries:
                # Skip entries we've already matched by title or tag
                if entry_id in matching_ids:
                    entry = self.get_entry(entry_id)
                    if entry:
                        entries.append(entry)
                    continue

                # Check content
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            # Check if entry matches date and tag filters
                            entry = self.get_entry(entry_id)
                            if not entry:
                                continue

                            include = True

                            # Filter by date range
                            if date_from and entry.created_at < date_from:
                                include = False
                            if date_to and entry.created_at > date_to:
                                include = False

                            # Filter by tags
                            if tags and include:
                                if not any(tag in entry.tags for tag in tags):
                                    include = False

                            if include:
                                entries.append(entry)
        finally:
            conn.close()

        return entries

    def get_entry_by_title(self, title: str) -> Optional[JournalEntry]:
        """
        Find a journal entry by its title.

        Args:
            title: The title to search for

        Returns:
            JournalEntry object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
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

    def get_entries_by_tag(
        self, tag: str, limit: int = 10, offset: int = 0
    ) -> List[JournalEntry]:
        """
        Find journal entries by tag.

        Args:
            tag: The tag to search for
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination

        Returns:
            List of JournalEntry objects with the specified tag
        """
        conn = sqlite3.connect(self.db_path)
        conn.create_function("LOWER", 1, lambda x: x.lower() if x else None)
        cursor = conn.cursor()
        try:
            # Use JSON functions to search within the tags array
            query = """
                SELECT id FROM entries
                WHERE EXISTS (
                    SELECT 1 FROM json_each(tags)
                    WHERE LOWER(json_each.value) = ?
                )
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, (tag.lower(), limit, offset))
            rows = cursor.fetchall()

            entries = []
            for row in rows:
                entry = self.get_entry(row[0])
                if entry:
                    entries.append(entry)

            return entries
        finally:
            conn.close()

    def get_all_tags(self) -> List[str]:
        """
        Get a list of all unique tags used across all entries.

        Returns:
            List of unique tag strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tags FROM entries")
            rows = cursor.fetchall()

            # Extract and flatten all tags
            all_tags = set()
            for row in rows:
                if row[0]:  # if tags exist
                    tags = json.loads(row[0])
                    all_tags.update(tags)

            return sorted(list(all_tags))
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the journal entries.

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            stats = {
                "total_entries": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "total_tags": 0,
                "most_used_tags": [],
            }

            # Get total entries
            cursor.execute("SELECT COUNT(*) FROM entries")
            stats["total_entries"] = cursor.fetchone()[0]

            # Get oldest entry date
            if stats["total_entries"] > 0:
                cursor.execute("SELECT MIN(created_at) FROM entries")
                stats["oldest_entry"] = cursor.fetchone()[0]

                cursor.execute("SELECT MAX(created_at) FROM entries")
                stats["newest_entry"] = cursor.fetchone()[0]

            # Count tags
            all_tags = self.get_all_tags()
            stats["total_tags"] = len(all_tags)

            # Get most used tags (requires additional processing)
            tag_counts = {}
            cursor.execute("SELECT tags FROM entries")
            for row in cursor.fetchall():
                if row[0]:
                    tags = json.loads(row[0])
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            stats["most_used_tags"] = sorted_tags[:5]  # Top 5 tags

            return stats
        finally:
            conn.close()
