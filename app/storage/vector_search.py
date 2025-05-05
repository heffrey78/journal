import numpy as np
import sqlite3
import re
from typing import List, Dict, Any

from sklearn.metrics.pairwise import cosine_similarity
from app.storage.base import BaseStorage


class VectorStorage(BaseStorage):
    """Handles vector embeddings storage and semantic search."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize vector storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_table()

    def _init_table(self):
        """Initialize vectors table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
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
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vectors_entry_id ON vectors(entry_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vectors_has_embedding"
            " ON vectors(embedding) WHERE embedding IS NOT NULL"
        )
        conn.commit()
        conn.close()

    def index_entry(self, entry):
        """
        Index an entry for vector search.

        Args:
            entry: JournalEntry to index

        Returns:
            True if successful, False otherwise
        """
        # Get a database connection
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Delete any existing vectors for this entry (for updates)
            cursor.execute("DELETE FROM vectors WHERE entry_id = ?", (entry.id,))

            # Index the entry content for vector search
            self._index_for_vector_search(conn, entry)

            conn.commit()
            return True
        except Exception as e:
            print(f"Error indexing entry: {e}")
            return False
        finally:
            conn.close()

    def _index_for_vector_search(self, conn, entry):
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
        conn = self.get_db_connection()
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
        conn = self.get_db_connection()
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
        conn = self.get_db_connection()
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

            return paginated_results
        finally:
            conn.close()
