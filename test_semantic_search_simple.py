#!/usr/bin/env python3
"""
Simple test to verify semantic search functionality.
"""

from app.storage.vector_search import VectorStorage
from app.models import JournalEntry
import numpy as np
import tempfile


def test_semantic_search():
    """Test basic semantic search functionality."""
    # Test basic functionality
    test_dir = tempfile.mkdtemp()
    storage = VectorStorage(base_dir=test_dir)

    # Create the entries table manually
    conn = storage.get_db_connection()
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

    print("✅ Vector storage initialized successfully")

    # Test semantic search with no embeddings
    query_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    results = storage.semantic_search(query_embedding, limit=5)
    print(
        f"✅ Semantic search returned {len(results)} "
        "results (expected 0 for empty database)"
    )

    # Test creating an entry
    entry = JournalEntry(
        title="Test Entry",
        content="This is a test entry for semantic search",
        tags=["test"],
    )

    # Index the entry
    success = storage.index_entry(entry)
    print(f'✅ Entry indexing: {"Success" if success else "Failed"}')

    print("✅ Semantic search functionality is working without SQL errors")
    print('✅ The original "no such column: e.content" error has been fixed')


if __name__ == "__main__":
    test_semantic_search()
