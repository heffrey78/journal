import os
import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

from app.models import JournalEntry, LLMConfig


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

        # Entry cache for improved performance
        self._entry_cache = {}
        self._cache_size = 50  # Maximum number of entries to cache

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

        # Configuration table for LLM settings
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS config (
            id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            embedding_model TEXT NOT NULL,
            max_retries INTEGER NOT NULL,
            retry_delay REAL NOT NULL,
            temperature REAL NOT NULL,
            max_tokens INTEGER NOT NULL,
            system_prompt TEXT
        )
        """
        )

        # Create index for faster vector queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vectors_entry_id ON vectors(entry_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vectors_has_embedding"
            " ON vectors(embedding) WHERE embedding IS NOT NULL"
        )

        conn.commit()
        conn.close()

        # Initialize default LLM config if not exists
        self._init_default_config()

    def _init_default_config(self):
        """Initialize default LLM configuration if it doesn't exist."""
        if not self.get_llm_config():
            default_config = LLMConfig()
            self.save_llm_config(default_config)

    def save_llm_config(self, config: LLMConfig) -> bool:
        """
        Save LLM configuration settings.

        Args:
            config: The LLMConfig object to save

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO config VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    config.id,
                    config.model_name,
                    config.embedding_model,
                    config.max_retries,
                    config.retry_delay,
                    config.temperature,
                    config.max_tokens,
                    config.system_prompt,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving LLM config: {e}")
            return False
        finally:
            conn.close()

    def get_llm_config(self, config_id: str = "default") -> Optional[LLMConfig]:
        """
        Retrieve LLM configuration settings.

        Args:
            config_id: The configuration ID to retrieve (defaults to "default")

        Returns:
            LLMConfig object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    model_name, embedding_model, max_retries, retry_delay,
                    temperature, max_tokens, system_prompt
                FROM config WHERE id = ?
                """,
                (config_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            (
                model_name,
                embedding_model,
                max_retries,
                retry_delay,
                temperature,
                max_tokens,
                system_prompt,
            ) = row

            return LLMConfig(
                id=config_id,
                model_name=model_name,
                embedding_model=embedding_model,
                max_retries=max_retries,
                retry_delay=retry_delay,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
        finally:
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
        Split text into sentence-aware chunks for vector indexing.

        This optimized version respects sentence and paragraph boundaries when possible,
        which improves the semantic coherence of chunks and leads to better searches.

        Args:
            text: The text to chunk
            chunk_size: Target size of each chunk in characters

        Returns:
            List of text chunks
        """
        # Split by paragraphs first (double newlines)
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            # If paragraph is too big on its own, we need to split it
            if len(paragraph) > chunk_size * 1.5:
                # Split into sentences
                sentences = self._split_into_sentences(paragraph)

                for sentence in sentences:
                    sentence_len = len(sentence)

                    # Handle very long sentences
                    if sentence_len > chunk_size:
                        # If current chunk has content, complete it first
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                            current_chunk = []
                            current_length = 0

                        # Split the long sentence into word-based chunks
                        words = sentence.split()
                        word_chunk = []
                        word_chunk_length = 0

                        for word in words:
                            if word_chunk_length + len(word) + 1 > chunk_size:
                                chunks.append(" ".join(word_chunk))
                                word_chunk = [word]
                                word_chunk_length = len(word)
                            else:
                                word_chunk.append(word)
                                word_chunk_length += len(word) + 1

                        if word_chunk:
                            chunks.append(" ".join(word_chunk))

                    # Normal sentence handling
                    elif current_length + sentence_len + 1 > chunk_size:
                        # Complete current chunk and start a new one with this sentence
                        chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_length = sentence_len
                    else:
                        # Add sentence to current chunk
                        current_chunk.append(sentence)
                        current_length += sentence_len + 1
            else:
                # Try to add the entire paragraph
                if current_length + len(paragraph) + 2 > chunk_size and current_chunk:
                    # Complete the current chunk first
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [paragraph]
                    current_length = len(paragraph)
                else:
                    # Add paragraph to current chunk
                    if current_chunk:  # Add a separator if joining paragraphs
                        current_chunk.append("\n\n" + paragraph)
                        current_length += len(paragraph) + 2
                    else:
                        current_chunk.append(paragraph)
                        current_length += len(paragraph)

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(" ".join(current_chunk).replace("\n\n ", "\n\n"))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split a text into sentences.

        Args:
            text: The text to split into sentences

        Returns:
            List of sentences
        """
        # Basic sentence splitting - sentence ending punctuation
        import re

        sentence_endings = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

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
        self,
        query_embedding: np.ndarray,
        limit: int = 5,
        offset: int = 0,
        batch_size: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar entries using vector embeddings with batched processing.

        Args:
            query_embedding: The embedding vector to search with
            limit: Maximum number of results to return
            offset: Number of entries to skip for pagination
            batch_size: Size of batches for processing vectors

        Returns:
            List of dictionaries with search results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Get total count for batching
            cursor.execute("SELECT COUNT(*) FROM vectors WHERE embedding IS NOT NULL")
            total_vectors = cursor.fetchone()[0]

            all_results = []

            # Process in batches to avoid memory issues with large datasets
            for batch_offset in range(0, total_vectors, batch_size):
                cursor.execute(
                    """
                    SELECT v.id, v.entry_id, v.text, v.embedding, e.title
                    FROM vectors v
                    JOIN entries e ON v.entry_id = e.id
                    WHERE v.embedding IS NOT NULL
                    LIMIT ? OFFSET ?
                    """,
                    (batch_size, batch_offset),
                )

                batch_results = []
                for row in cursor.fetchall():
                    vector_id, entry_id, text, embedding_bytes, title = row
                    if embedding_bytes:
                        # Convert bytes back to numpy array
                        db_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

                        # Calculate cosine similarity
                        similarity = float(
                            cosine_similarity([query_embedding], [db_embedding])[0][0]
                        )

                        batch_results.append(
                            {
                                "vector_id": vector_id,
                                "entry_id": entry_id,
                                "title": title,
                                "text": text,
                                "similarity": similarity,
                            }
                        )

                all_results.extend(batch_results)

            # Sort all results by similarity
            all_results.sort(key=lambda x: x["similarity"], reverse=True)

            # Apply pagination
            # fmt: off
            paginated_results = all_results[offset: offset + limit]
            # fmt: on

            # Now fetch the complete entries only for the paginated results
            # This avoids loading full entries for all matches
            result_with_entries = []
            for result in paginated_results:
                entry = self.get_entry(result["entry_id"])
                if entry:
                    result["entry"] = entry
                    result_with_entries.append(result)

            return result_with_entries
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
        # Check cache first
        if entry_id in self._entry_cache:
            return self._entry_cache[entry_id]

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
