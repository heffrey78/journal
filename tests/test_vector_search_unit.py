"""
Unit tests for vector search functionality.

These tests verify that:
1. Semantic search executes without SQL errors
2. Vector storage operations work correctly
3. Error handling and logging function properly
4. Search returns appropriate results
"""
import pytest
import tempfile
import shutil
import numpy as np
import sqlite3
import os
from unittest.mock import patch

from app.models import JournalEntry
from app.storage.vector_search import VectorStorage


class TestVectorSearch:
    """Test cases for the VectorStorage class."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up a temporary test environment for each test."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.vector_storage = VectorStorage(base_dir=self.test_dir)

        # Create test entries directory
        os.makedirs(os.path.join(self.test_dir, "entries"), exist_ok=True)

        # Initialize the entries table manually since VectorStorage
        # only creates vectors table
        self._init_entries_table()

        yield

        # Clean up after test
        shutil.rmtree(self.test_dir)

    def _init_entries_table(self):
        """Initialize the entries table for testing."""
        conn = self.vector_storage.get_db_connection()
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

    def test_vector_storage_initialization(self):
        """Test initialization of VectorStorage."""
        # Verify database was initialized
        conn = self.vector_storage.get_db_connection()
        cursor = conn.cursor()

        # Check if vectors table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' " "AND name='vectors'"
        )
        assert cursor.fetchone() is not None

        # Check if entries table exists (should be created by base class)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' " "AND name='entries'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_index_entry_creates_vectors(self):
        """Test that indexing an entry creates vector chunks."""
        # Create a test entry
        entry = JournalEntry(
            title="Test Entry",
            content="This is a test entry for vector indexing. " * 10,
            tags=["test"],
        )

        # Index the entry
        result = self.vector_storage.index_entry(entry)
        assert result is True

        # Verify vectors were created
        conn = self.vector_storage.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vectors WHERE entry_id = ?", (entry.id,))
        count = cursor.fetchone()[0]
        assert count > 0
        conn.close()

    def test_semantic_search_sql_column_fix(self):
        """Test that the SQL query uses file_path instead of content column."""
        # This test verifies the fix for the original SQL error
        entry = JournalEntry(title="Test Entry", content="Test content", tags=["test"])

        # Create the entry file
        entry_file = os.path.join(self.test_dir, "entries", f"{entry.id}.md")
        with open(entry_file, "w") as f:
            f.write(f"# {entry.title}\n\n{entry.content}")

        # Add entry to database
        conn = self.vector_storage.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO entries (id, title, file_path, created_at, tags)
               VALUES (?, ?, ?, ?, ?)""",
            (entry.id, entry.title, entry_file, entry.created_at, "test"),
        )
        conn.commit()

        # Index and add embeddings
        self.vector_storage.index_entry(entry)
        embeddings = {0: np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)}
        self.vector_storage.update_vectors_with_embeddings(entry.id, embeddings)

        # This should NOT raise "no such column: e.content" error
        query_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        try:
            self.vector_storage.semantic_search(query_embedding, limit=5)
            # If we get here without exception, the SQL fix worked
            assert True
        except sqlite3.OperationalError as e:
            if "no such column: e.content" in str(e):
                pytest.fail("SQL error not fixed: still trying to select e.content")
            else:
                raise

    def test_semantic_search_with_no_embeddings(self):
        """Test semantic search when no embeddings exist."""
        query_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

        with patch("logging.getLogger") as mock_logger:
            results = self.vector_storage.semantic_search(query_embedding, limit=5)

            assert results == []
            # Verify warning was logged about no embeddings
            mock_logger.return_value.warning.assert_called()

    def test_semantic_search_error_handling(self):
        """Test error handling in semantic search."""
        query_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

        # Mock database error
        with patch.object(self.vector_storage, "get_db_connection") as mock_conn:
            mock_conn.side_effect = Exception("Database connection failed")

            with patch("logging.getLogger") as mock_logger:
                # The semantic_search method should catch the exception
                # and return an empty list
                results = self.vector_storage.semantic_search(query_embedding, limit=5)

                assert results == []
                # Verify error was logged
                mock_logger.return_value.error.assert_called_with(
                    "Error in semantic search: Database connection failed"
                )
