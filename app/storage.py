import logging
import os
import json
import re
import sqlite3
import numpy as np
import uuid
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
        self.images_dir = os.path.join(base_dir, "images")
        self.db_path = os.path.join(base_dir, "journal.db")

        # Ensure directories exist
        os.makedirs(self.entries_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

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
            system_prompt TEXT,
            min_similarity REAL DEFAULT 0.5
        )
        """
        )

        # Prompt types table for LLM analysis types
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS prompt_types (
            id TEXT NOT NULL,
            config_id TEXT NOT NULL,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            PRIMARY KEY (id, config_id),
            FOREIGN KEY (config_id) REFERENCES config(id)
        )
        """
        )

        # Images table for storing image metadata
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            entry_id TEXT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            size INTEGER NOT NULL,
            width INTEGER,
            height INTEGER,
            created_at TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
        )
        """
        )

        # Entry summaries table for saved/favorite summaries
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS entry_summaries (
            id TEXT PRIMARY KEY,
            entry_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            key_topics TEXT NOT NULL,
            mood TEXT NOT NULL,
            favorite BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
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

        # Create index for entry summaries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entry_summaries_entry_id "
            "ON entry_summaries(entry_id)"
        )

        # Create index for images
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_images_entry_id ON images(entry_id)"
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
            # Check the actual table structure
            cursor.execute("PRAGMA table_info(config)")
            columns = [info[1] for info in cursor.fetchall()]

            logger = logging.getLogger(__name__)
            logger.info(f"Config table columns: {columns}")

            # Use a direct approach with explicit column names
            cursor.execute(
                """
                INSERT OR REPLACE INTO config
                (id, model_name, embedding_model, max_retries, retry_delay,
                temperature, max_tokens, system_prompt, min_similarity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config.id,
                    config.model_name,
                    config.embedding_model,
                    config.max_retries,
                    config.retry_delay,
                    config.temperature,
                    config.max_tokens,
                    config.system_prompt,
                    config.min_similarity,
                ),
            )

            # Delete existing prompt types for this config
            cursor.execute("DELETE FROM prompt_types WHERE config_id = ?", (config.id,))

            # Insert new prompt types
            if config.prompt_types:
                for pt in config.prompt_types:
                    cursor.execute(
                        "INSERT INTO prompt_types (id, config_id, name, prompt) "
                        "VALUES (?, ?, ?, ?)",
                        (pt.id, config.id, pt.name, pt.prompt),
                    )

            conn.commit()
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving LLM config: {e}")
            conn.rollback()
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
            # Get the main config
            cursor.execute(
                """
                SELECT
                    model_name, embedding_model, max_retries, retry_delay,
                    temperature, max_tokens, system_prompt, min_similarity
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
                min_similarity,
            ) = row

            # Get prompt types for this config
            cursor.execute(
                "SELECT id, name, prompt FROM prompt_types WHERE config_id = ?",
                (config_id,),
            )

            from app.models import PromptType

            prompt_types = []
            for pt_row in cursor.fetchall():
                pt_id, pt_name, pt_prompt = pt_row
                prompt_types.append(
                    PromptType(id=pt_id, name=pt_name, prompt=pt_prompt)
                )

            # If no prompt types are found, use the defaults from LLMConfig
            if not prompt_types:
                config = LLMConfig(
                    id=config_id,
                    model_name=model_name,
                    embedding_model=embedding_model,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    min_similarity=min_similarity
                    if min_similarity is not None
                    else 0.5,
                )
            else:
                # Create config with the retrieved prompt types
                config = LLMConfig(
                    id=config_id,
                    model_name=model_name,
                    embedding_model=embedding_model,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    min_similarity=min_similarity
                    if min_similarity is not None
                    else 0.5,
                    prompt_types=prompt_types,
                )

            return config
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving LLM config: {e}")
            return None
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
        conn = None
        try:
            # Use a timeout to prevent database locks from blocking indefinitely
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()

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

            # Add to cache
            self._add_to_cache(entry)

            return entry.id
        except Exception as e:
            # Log the error and rethrow
            logging.error(f"Error saving entry {entry.id}: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

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
            paginated_results = all_results[offset : offset + limit]  # noqa: E203

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

            # Apply pagination after all search results are collected
            paginated_entries = entries[offset : offset + limit]  # noqa: E203

            return paginated_entries
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

    def save_entry_summary(self, entry_id: str, summary) -> bool:
        """
        Save an entry summary to the database.

        Args:
            entry_id: The ID of the journal entry
            summary: EntrySummary object to save

        Returns:
            True if successful, False otherwise
        """
        from uuid import uuid4
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Generate a unique ID for the summary
            summary_id = str(uuid4())

            cursor.execute(
                """
                INSERT INTO entry_summaries (
                    id, entry_id, summary, key_topics, mood,
                    favorite, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary_id,
                    entry_id,
                    summary.summary,
                    json.dumps(summary.key_topics),
                    summary.mood,
                    1 if summary.favorite else 0,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving entry summary: {e}")
            return False
        finally:
            conn.close()

    def get_entry_summaries(self, entry_id: str) -> List:
        """
        Get all summaries for a specific entry.

        Args:
            entry_id: The ID of the journal entry

        Returns:
            List of EntrySummary objects
        """
        from app.models import EntrySummary

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, summary, key_topics, mood, favorite, created_at
                FROM entry_summaries
                WHERE entry_id = ? AND favorite = 1
                ORDER BY created_at DESC
                """,
                (entry_id,),
            )

            summaries = []
            for row in cursor.fetchall():
                (
                    summary_id,
                    summary_text,
                    key_topics_json,
                    mood,
                    favorite,
                    created_at,
                ) = row

                # Create EntrySummary object
                summary = EntrySummary(
                    summary=summary_text,
                    key_topics=json.loads(key_topics_json),
                    mood=mood,
                    favorite=bool(favorite),
                )
                summaries.append(summary)

            return summaries
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving entry summaries: {e}")
            return []
        finally:
            conn.close()

    def delete_entry_summary(self, summary_id: str) -> bool:
        """
        Delete an entry summary by its ID.

        Args:
            summary_id: The ID of the summary to delete

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM entry_summaries WHERE id = ?", (summary_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting entry summary: {e}")
            return False
        finally:
            conn.close()

    # Image Storage Methods

    def save_image(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        entry_id: Optional[str] = None,
        description: str = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Save an image file to the filesystem and record its metadata in the database.

        Args:
            file_data: The binary image data
            filename: Original filename of the image
            mime_type: MIME type of the image (e.g., 'image/jpeg')
            entry_id: Optional ID of the journal entry this image is associated with
            description: Optional description of the image
            width: Optional width of the image in pixels
            height: Optional height of the image in pixels

        Returns:
            Dictionary with image metadata including the ID and path
        """
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())

        # Extract file extension from the original filename or mime type
        ext = os.path.splitext(filename)[1]
        if not ext:
            # If no extension in filename, try to get from mime type
            if mime_type == "image/jpeg" or mime_type == "image/jpg":
                ext = ".jpg"
            elif mime_type == "image/png":
                ext = ".png"
            elif mime_type == "image/gif":
                ext = ".gif"
            elif mime_type == "image/webp":
                ext = ".webp"
            else:
                ext = ".bin"  # Default extension if unable to determine

        # Create a sanitized filename that includes the ID to ensure uniqueness
        new_filename = f"{image_id}{ext}"
        file_path = os.path.join(self.images_dir, new_filename)

        # Save the file to disk
        with open(file_path, "wb") as f:
            f.write(file_data)

        # Calculate the file size
        file_size = len(file_data)

        # Record in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO images (
                    id, entry_id, filename, file_path, mime_type,
                    size, width, height, created_at, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image_id,
                    entry_id,
                    filename,  # Original filename
                    file_path,  # System path
                    mime_type,
                    file_size,
                    width,
                    height,
                    datetime.now().isoformat(),
                    description,
                ),
            )
            conn.commit()

            # Return image metadata
            return {
                "id": image_id,
                "filename": filename,
                "path": file_path,
                "mime_type": mime_type,
                "size": file_size,
                "width": width,
                "height": height,
                "entry_id": entry_id,
                "description": description,
            }
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving image: {e}")
            # If database insertion fails, delete the file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
        finally:
            conn.close()

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an image by its ID.

        Args:
            image_id: The ID of the image to retrieve

        Returns:
            Dictionary with image metadata if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, entry_id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE id = ?
                """,
                (image_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Extract values
            (
                id,
                entry_id,
                filename,
                file_path,
                mime_type,
                size,
                width,
                height,
                created_at,
                description,
            ) = row

            # Check if file exists
            if not os.path.exists(file_path):
                logger = logging.getLogger(__name__)
                logger.error(f"Image file not found: {file_path}")
                return None

            return {
                "id": id,
                "entry_id": entry_id,
                "filename": filename,
                "path": file_path,
                "mime_type": mime_type,
                "size": size,
                "width": width,
                "height": height,
                "created_at": created_at,
                "description": description,
            }
        finally:
            conn.close()

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """
        Get the binary data for an image by its ID.

        Args:
            image_id: The ID of the image to retrieve

        Returns:
            Binary image data if found, None otherwise
        """
        image_meta = self.get_image(image_id)
        if not image_meta:
            return None

        try:
            with open(image_meta["path"], "rb") as f:
                return f.read()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error reading image file: {e}")
            return None

    def delete_image(self, image_id: str) -> bool:
        """
        Delete an image by its ID.

        Args:
            image_id: The ID of the image to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        # Get image metadata to find the file path
        image_meta = self.get_image(image_id)
        if not image_meta:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Delete from database
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            conn.commit()

            # Delete the file if it exists
            if os.path.exists(image_meta["path"]):
                os.remove(image_meta["path"])

            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting image: {e}")
            return False
        finally:
            conn.close()

    def get_entry_images(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get all images associated with a specific journal entry.

        Args:
            entry_id: The ID of the journal entry

        Returns:
            List of dictionaries with image metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE entry_id = ?
                ORDER BY created_at ASC
                """,
                (entry_id,),
            )

            images = []
            for row in cursor.fetchall():
                (
                    id,
                    filename,
                    file_path,
                    mime_type,
                    size,
                    width,
                    height,
                    created_at,
                    description,
                ) = row

                # Only include if the file exists
                if os.path.exists(file_path):
                    images.append(
                        {
                            "id": id,
                            "filename": filename,
                            "path": file_path,
                            "mime_type": mime_type,
                            "size": size,
                            "width": width,
                            "height": height,
                            "created_at": created_at,
                            "description": description,
                        }
                    )

            return images
        finally:
            conn.close()

    def update_image_metadata(
        self, image_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update metadata for an image.

        Args:
            image_id: The ID of the image to update
            updates: Dictionary containing fields to update

        Returns:
            Updated image metadata dictionary if successful, None otherwise
        """
        # Check if image exists
        image_meta = self.get_image(image_id)
        if not image_meta:
            return None

        # Validate updatable fields
        valid_fields = {"entry_id", "description", "width", "height"}

        # Filter to only valid fields
        updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not updates:
            return image_meta  # No valid updates

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Build update query dynamically
            set_parts = []
            params = []

            for field, value in updates.items():
                set_parts.append(f"{field} = ?")
                params.append(value)

            # Add image_id at the end for the WHERE clause
            params.append(image_id)

            query = f"""
                UPDATE images
                SET {', '.join(set_parts)}
                WHERE id = ?
            """

            cursor.execute(query, tuple(params))
            conn.commit()

            # Return updated metadata
            return self.get_image(image_id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating image metadata: {e}")
            return None
        finally:
            conn.close()

    def get_orphaned_images(self) -> List[Dict[str, Any]]:
        """
        Get all images that are not associated with any journal entry.

        Returns:
            List of dictionaries with image metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, filename, file_path, mime_type,
                       size, width, height, created_at, description
                FROM images
                WHERE entry_id IS NULL
                ORDER BY created_at DESC
                """
            )

            images = []
            for row in cursor.fetchall():
                (
                    id,
                    filename,
                    file_path,
                    mime_type,
                    size,
                    width,
                    height,
                    created_at,
                    description,
                ) = row

                # Only include if the file exists
                if os.path.exists(file_path):
                    images.append(
                        {
                            "id": id,
                            "filename": filename,
                            "path": file_path,
                            "mime_type": mime_type,
                            "size": size,
                            "width": width,
                            "height": height,
                            "created_at": created_at,
                            "description": description,
                        }
                    )

            return images
        finally:
            conn.close()

    def assign_image_to_entry(self, image_id: str, entry_id: str) -> bool:
        """
        Associate an existing image with a journal entry.

        Args:
            image_id: The ID of the image
            entry_id: The ID of the journal entry

        Returns:
            True if successful, False otherwise
        """
        # Check if the image exists
        image_meta = self.get_image(image_id)
        if not image_meta:
            return False

        # Check if the entry exists
        entry = self.get_entry(entry_id)
        if not entry:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE images SET entry_id = ? WHERE id = ?", (entry_id, image_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error assigning image to entry: {e}")
            return False
        finally:
            conn.close()

    def advanced_search(
        self,
        query: str = "",
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        favorite: Optional[bool] = None,  # Keeping parameter for API compatibility
        semantic: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """
        Advanced search for journal entries with multiple filters.

        Args:
            query: The search query string
            tags: Optional list of tags to filter entries by
            date_from: Optional start date for filtering entries
            date_to: Optional end date for filtering entries
            favorite: Optional boolean to filter by favorite status
            (not used - kept for API compatibility)
            semantic: Whether to use semantic search for the query
            limit: Maximum number of entries to return
            offset: Number of entries to skip for pagination

        Returns:
            List of JournalEntry objects that match the search criteria
        """
        # If using semantic search with a query, process it differently
        if semantic and query.strip():
            # Import here to avoid circular imports - assuming it's available
            from app.llm_service import LLMService

            llm_service = LLMService()

            try:
                # Get query embedding
                query_embedding = llm_service.get_embedding(query)
                if query_embedding is not None:
                    # Get semantic search results
                    semantic_results = self.semantic_search(
                        query_embedding=query_embedding,
                        limit=100,  # Get more results for filtering
                    )

                    if semantic_results:
                        # Extract entry IDs from semantic results
                        entry_ids = [result["entry_id"] for result in semantic_results]

                        # Load full entries
                        all_entries = []
                        for entry_id in entry_ids:
                            entry = self.get_entry(entry_id)
                            if entry:
                                all_entries.append(entry)

                        # Apply additional filters (without favorite)
                        filtered_entries = self._apply_filters(
                            all_entries, tags, date_from, date_to
                        )

                        # Apply pagination
                        return filtered_entries[offset : offset + limit]  # noqa: E203
            except Exception as e:
                logging.getLogger(__name__).error(f"Semantic search error: {str(e)}")
                # Fall back to regular search on error

        # Regular search path (also fallback if semantic search fails)

        # If no query but we have other filters, get entries with filters
        if not query.strip():
            # Get all entries matching date and tag filters
            all_entries = self.get_entries(
                limit=1000,  # Get more to filter properly
                offset=0,
                date_from=date_from,
                date_to=date_to,
                tags=tags,
            )

            # Apply pagination
            return all_entries[offset : offset + limit]  # noqa: E203

        # Regular text search with additional filtering
        entries = self.text_search(
            query=query,
            date_from=date_from,
            date_to=date_to,
            tags=tags,
            limit=1000,  # Get more entries
            offset=0,
        )

        # Apply pagination
        return entries[offset : offset + limit]  # noqa: E203

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
