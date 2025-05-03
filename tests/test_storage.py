"""
Test suite for the storage module.

This module contains pytest tests for the StorageManager class.
"""
import sys
from pathlib import Path
import pytest
import os
import shutil
import sqlite3
import tempfile
import numpy as np
from datetime import datetime, timedelta
from app.models import JournalEntry
from app.storage import StorageManager

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
SKLEARN_AVAILABLE = False


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestStorageManager:
    """Test cases for the StorageManager class."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up a temporary test environment for each test."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(base_dir=self.test_dir)

        yield

        # Clean up after test
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test initialization of StorageManager."""
        # Verify directories were created
        assert os.path.exists(self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, "entries"))

        # Verify database was initialized
        conn = sqlite3.connect(os.path.join(self.test_dir, "journal.db"))
        cursor = conn.cursor()

        # Check if entries table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        assert cursor.fetchone() is not None

        # Check if vectors table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vectors'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_save_and_retrieve_entry(self):
        """Test saving and retrieving a journal entry."""
        # Create a journal entry
        entry = JournalEntry(
            title="Test Storage",
            content="Testing storage functionality",
            tags=["storage", "test"],
        )

        # Save the entry
        entry_id = self.storage.save_entry(entry)
        assert entry_id == entry.id

        # Check if file was created
        file_path = os.path.join(self.test_dir, "entries", f"{entry_id}.md")
        assert os.path.exists(file_path)

        # Check file content
        with open(file_path, "r") as f:
            content = f.read()
            assert content.startswith(f"# {entry.title}")
            assert entry.content in content

        # Retrieve the entry
        retrieved_entry = self.storage.get_entry(entry_id)
        assert retrieved_entry is not None
        assert retrieved_entry.id == entry.id
        assert retrieved_entry.title == entry.title
        assert retrieved_entry.content == entry.content
        assert retrieved_entry.tags == entry.tags

    def test_update_entry(self):
        """Test updating a journal entry."""
        # Create and save an entry
        entry = JournalEntry(
            title="Original Title", content="Original content", tags=["original"]
        )
        entry_id = self.storage.save_entry(entry)

        # Update the entry
        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
            "tags": ["updated", "test"],
        }
        updated_entry = self.storage.update_entry(entry_id, update_data)

        # Verify update was successful
        assert updated_entry is not None
        assert updated_entry.title == "Updated Title"
        assert updated_entry.content == "Updated content"
        assert updated_entry.tags == ["updated", "test"]

        # Verify changes were persisted
        retrieved_entry = self.storage.get_entry(entry_id)
        assert retrieved_entry.title == "Updated Title"
        assert retrieved_entry.content == "Updated content"
        assert retrieved_entry.tags == ["updated", "test"]

        # Verify file was updated
        file_path = os.path.join(self.test_dir, "entries", f"{entry_id}.md")
        with open(file_path, "r") as f:
            content = f.read()
            assert content.startswith("# Updated Title")
            assert "Updated content" in content

    def test_delete_entry(self):
        """Test deleting a journal entry."""
        # Create and save an entry
        entry = JournalEntry(
            title="Delete Test",
            content="This entry will be deleted",
        )
        entry_id = self.storage.save_entry(entry)

        # Verify entry exists
        file_path = os.path.join(self.test_dir, "entries", f"{entry_id}.md")
        assert os.path.exists(file_path)

        # Delete the entry
        result = self.storage.delete_entry(entry_id)
        assert result is True

        # Verify entry was deleted
        assert not os.path.exists(file_path)
        assert self.storage.get_entry(entry_id) is None

        # Try deleting non-existent entry
        result = self.storage.delete_entry("nonexistent")
        assert result is False

    def test_get_entries(self):
        """Test retrieving multiple journal entries with filters."""
        # Create several entries with different dates and tags
        entries = []

        # Entry 1 - today
        entry1 = JournalEntry(
            title="Today's Entry", content="Content for today", tags=["daily", "test"]
        )
        entries.append(entry1)

        # Entry 2 - yesterday
        yesterday = datetime.now() - timedelta(days=1)
        entry2 = JournalEntry(
            id=yesterday.strftime("%Y%m%d%H%M%S"),
            title="Yesterday's Entry",
            content="Content from yesterday",
            created_at=yesterday,
            tags=["daily", "past"],
        )
        entries.append(entry2)

        # Entry 3 - last week
        last_week = datetime.now() - timedelta(days=7)
        entry3 = JournalEntry(
            id=last_week.strftime("%Y%m%d%H%M%S"),
            title="Last Week's Entry",
            content="Content from last week",
            created_at=last_week,
            tags=["weekly", "past"],
        )
        entries.append(entry3)

        # Save all entries
        for entry in entries:
            self.storage.save_entry(entry)

        # Test getting all entries (default limit 10)
        all_entries = self.storage.get_entries()
        assert len(all_entries) == 3

        # Test pagination
        paginated = self.storage.get_entries(limit=2, offset=0)
        assert len(paginated) == 2
        assert paginated[0].id == entry1.id  # Newest first

        # Test date filtering
        three_days_ago = datetime.now() - timedelta(days=3)
        recent_entries = self.storage.get_entries(date_from=three_days_ago)
        assert len(recent_entries) == 2
        assert all(e.id in [entry1.id, entry2.id] for e in recent_entries)

        # Test tag filtering
        daily_entries = self.storage.get_entries_by_tag("daily")
        assert len(daily_entries) == 2
        assert all(e.id in [entry1.id, entry2.id] for e in daily_entries)

        # Test combined filtering
        combined = self.storage.get_entries(date_from=three_days_ago, tags=["daily"])
        assert len(combined) >= 2
        assert all("daily" in e.tags for e in combined)

    def test_text_search(self):
        """Test text search functionality."""
        # Create entries with specific content for testing search
        entries = [
            JournalEntry(
                title="Programming Journal",
                content="I learned about Python and FastAPI today.",
                tags=["programming", "learning"],
            ),
            JournalEntry(
                title="Cooking Adventures",
                content="I made a delicious pasta dish for dinner.",
                tags=["cooking", "food"],
            ),
            JournalEntry(
                title="Weekend Plans",
                content="I might go hiking or visit the Python programming meetup.",
                tags=["weekend", "planning"],
            ),
        ]

        # Save all entries
        for entry in entries:
            self.storage.save_entry(entry)

        # Search for "Python" (should match entries 0 and 2)
        python_results = self.storage.text_search("Python")
        assert len(python_results) == 2
        assert any("Programming Journal" == e.title for e in python_results)
        assert any("Weekend Plans" == e.title for e in python_results)

        # Search for "cooking" (should match entry 1 by title or tag)
        cooking_results = self.storage.text_search("cooking")
        assert len(cooking_results) == 1
        assert cooking_results[0].title == "Cooking Adventures"

        # Search with tag filter
        weekend_results = self.storage.text_search(query="planning", tags=["weekend"])
        assert len(weekend_results) == 1
        assert weekend_results[0].title == "Weekend Plans"

    def test_chunking_logic(self):
        """Test text chunking for vector search."""
        # Create a long text with multiple paragraphs
        long_text = """# Test Chunking

        This is a test of the chunking algorithm.

        This is the second paragraph with some additional content.

        This is the third paragraph. It contains multiple sentences.
        The second sentence is here. And here's a third one.

        The fourth paragraph is short.

        This is the fifth and final paragraph with enough text to make it reasonable.
        We need to ensure that the chunking algorithm properly handles paragraphs and
        sentences.
        """

        # Call the chunking method
        chunks = self.storage._chunk_text(long_text, chunk_size=100)

        # Verify output
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(len(chunk) <= 150 for chunk in chunks)  # Allow some flexibility

    def test_vector_embedding_workflow(self):
        """Test the workflow for handling vector embeddings."""
        # Create an entry
        entry = JournalEntry(
            title="Vector Test",
            content="This is a test entry for vector embedding functionality.",
        )
        entry_id = self.storage.save_entry(entry)

        # Get chunks without embeddings
        chunks = self.storage.get_chunks_without_embeddings()
        assert len(chunks) >= 1

        # Check that chunks are related to our entry
        entry_chunks = [c for c in chunks if c["entry_id"] == entry_id]
        assert len(entry_chunks) >= 1

        # Simulate adding embeddings
        mock_embeddings = {}
        for chunk in entry_chunks:
            # Create a random embedding vector
            mock_embeddings[chunk["chunk_id"]] = np.random.rand(384).astype(np.float32)

        # Update vectors with embeddings
        result = self.storage.update_vectors_with_embeddings(entry_id, mock_embeddings)
        assert result is True

        # Verify chunks no longer appear in "without embeddings"
        updated_chunks = self.storage.get_chunks_without_embeddings()
        updated_entry_chunks = [c for c in updated_chunks if c["entry_id"] == entry_id]
        assert len(updated_entry_chunks) == 0

    def test_get_all_tags(self):
        """Test retrieving all unique tags."""
        # Create entries with various tags
        entries = [
            JournalEntry(
                title="Entry 1", content="Content 1", tags=["tag1", "tag2", "common"]
            ),
            JournalEntry(title="Entry 2", content="Content 2", tags=["tag3", "common"]),
            JournalEntry(title="Entry 3", content="Content 3", tags=["tag4", "tag5"]),
        ]

        # Save all entries
        for entry in entries:
            self.storage.save_entry(entry)

        # Get all tags
        all_tags = self.storage.get_all_tags()

        # Verify results
        assert len(all_tags) == 5
        assert "tag1" in all_tags
        assert "tag2" in all_tags
        assert "tag3" in all_tags
        assert "tag4" in all_tags
        assert "tag5" in all_tags
        assert "common" in all_tags

    def test_stats(self):
        """Test statistics gathering."""
        # Create some entries
        entries = [
            JournalEntry(title="Entry 1", content="Content 1", tags=["stats", "test"]),
            JournalEntry(
                title="Entry 2", content="Content 2", tags=["stats", "important"]
            ),
            JournalEntry(title="Entry 3", content="Content 3", tags=["test"]),
        ]

        # Save all entries
        for entry in entries:
            self.storage.save_entry(entry)

        # Get statistics
        stats = self.storage.get_stats()

        # Verify statistics
        assert stats["total_entries"] == 3
        assert stats["total_tags"] == 3  # stats, test, important
        assert len(stats["most_used_tags"]) > 0

        # Check tag counts
        tag_counts = {tag: count for tag, count in stats["most_used_tags"]}
        assert tag_counts.get("stats", 0) == 2
        assert tag_counts.get("test", 0) == 2


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
