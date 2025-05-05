import json
from typing import List, Dict, Any
from app.storage.base import BaseStorage


class TagStorage(BaseStorage):
    """Handles tag-related functionality."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize tag storage.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)

    def get_all_tags(self) -> List[str]:
        """
        Get a list of all unique tags used across all entries.

        Returns:
            List of unique tag strings
        """
        conn = self.get_db_connection()
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

    def get_entries_by_tag(
        self, tag: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find journal entries by tag.

        Args:
            tag: The tag to search for
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination

        Returns:
            List of entry IDs with the specified tag
        """
        conn = self.get_db_connection()
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
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_tag_count(self) -> List[Dict[str, Any]]:
        """
        Get tag usage statistics.

        Returns:
            List of dictionaries with tag and count
        """
        # Count tags
        tag_counts = {}
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT tags FROM entries")
            for row in cursor.fetchall():
                if row[0]:
                    tags = json.loads(row[0])
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            return [{"tag": tag, "count": count} for tag, count in sorted_tags]
        finally:
            conn.close()

    def get_popular_tags(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most frequently used tags.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of dictionaries with tag and count
        """
        all_tag_counts = self.get_tag_count()
        return all_tag_counts[:limit]
