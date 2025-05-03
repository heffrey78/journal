import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

from app.models import JournalEntry


class StorageManager:
    """
    Manages the storage of journal entries in both filesystem and SQLite database.

    This implementation includes vector storage for semantic search capabilities.
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

        # Vector storage table for semantic search
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS vectors (
            id TEXT PRIMARY KEY,
            entry_id TEXT NOT NULL,
            chunk_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
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
            # Delete any existing vectors for this entry (for updates)
            cursor.execute("DELETE FROM vectors WHERE entry_id = ?", (entry.id,))

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

            # Index the entry content for vector search
            self._index_for_vector_search(conn, entry)

            conn.commit()
        finally:
            conn.close()

        return entry.id

    def _index_for_vector_search(self, conn, entry: JournalEntry):
        """
        Index the entry content for vector search.

        Args:
            conn: SQLite connection
            entry: JournalEntry to index
        """
        # Chunk the entry content
        chunks = self._chunk_text(f"{entry.title}\n\n{entry.content}")

        # In a real implementation with Ollama, we would get embeddings here
        # For now, store NULL in the embedding field - will be updated later
        cursor = conn.cursor()
        for i, chunk in enumerate(chunks):
            cursor.execute(
                "INSERT INTO vectors (id, entry_id, chunk_id, text, embedding)"
                "VALUES (?, ?, ?, ?, NULL)",
                (f"{entry.id}_{i}", entry.id, i, chunk),
            )

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for vector indexing.

        Args:
            text: The text to chunk
            chunk_size: Target size of each chunk in characters

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1  # +1 for space

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def update_vectors_with_embeddings(
        self, entry_id: str, embeddings: Dict[int, np.ndarray]
    ) -> bool:
        """
        Update vector embeddings for an entry.

        Args:
            entry_id: ID of the entry to update
            embeddings: Dictionary mapping chunk_id to embedding vector

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for chunk_id, embedding in embeddings.items():
                # Convert numpy array to bytes for storage
                embedding_bytes = embedding.astype(np.float32).tobytes()

                cursor.execute(
                    "UPDATE vectors SET embedding = ? "
                    "WHERE entry_id = ? AND chunk_id = ?",
                    (sqlite3.Binary(embedding_bytes), entry_id, chunk_id),
                )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating vectors: {e}")
            return False
        finally:
            conn.close()

    def get_chunks_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get text chunks that don't have embeddings yet.

        Args:
            limit: Maximum number of chunks to retrieve

        Returns:
            List of dictionaries with chunk information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, entry_id, chunk_id, text
                FROM vectors
                WHERE embedding IS NULL
                LIMIT ?
                """,
                (limit,),
            )

            chunks = []
            for row in cursor.fetchall():
                chunks.append(
                    {
                        "id": row[0],
                        "entry_id": row[1],
                        "chunk_id": row[2],
                        "text": row[3],
                    }
                )

            return chunks
        finally:
            conn.close()

    def semantic_search(
        self, query_embedding: np.ndarray, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar entries using vector embeddings.

        Args:
            query_embedding: The embedding vector to search with
            limit: Maximum number of results to return

        Returns:
            List of dictionaries with search results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, entry_id, text, embedding "
                "FROM vectors WHERE embedding IS NOT NULL"
            )
            results = []

            for row in cursor.fetchall():
                vector_id, entry_id, text, embedding_bytes = row
                if embedding_bytes:  # Skip entries without embeddings
                    # Convert bytes back to numpy array
                    db_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

                    # Calculate cosine similarity
                    similarity = float(
                        cosine_similarity([query_embedding], [db_embedding])[0][0]
                    )

                    # Get the full entry
                    entry = self.get_entry(entry_id)

                    results.append(
                        {
                            "vector_id": vector_id,
                            "entry_id": entry_id,
                            "title": entry.title if entry else "Unknown",
                            "text": text,
                            "similarity": similarity,
                            "entry": entry,
                        }
                    )

            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
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
        # If query is empty, return entries that match other filters
        if not query.strip():
            return self.get_entries(
                limit=100,  # Higher limit for empty queries
                offset=0,
                date_from=date_from,
                date_to=date_to,
                tags=tags,
            )

        entries = []
        conn = sqlite3.connect(self.db_path)
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

            return entries
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
                "oldest_entry": float("inf"),
                "newest_entry": -float("inf"),
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
