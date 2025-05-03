"""
Test suite for the models module.

This module contains pytest tests for the JournalEntry model.
"""
import sys
from pathlib import Path
import pytest
from datetime import datetime
from app.models import JournalEntry

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestJournalEntry:
    """Test cases for the JournalEntry model."""

    def test_journal_entry_creation(self):
        """Test creating a basic journal entry."""
        # Create a journal entry
        entry = JournalEntry(
            title="Test Entry", content="This is a test entry", tags=["test", "pytest"]
        )

        # Verify default values
        assert entry.title == "Test Entry"
        assert entry.content == "This is a test entry"
        assert entry.tags == ["test", "pytest"]
        assert isinstance(entry.id, str)
        assert len(entry.id) == 14  # Format is YYYYMMDDhhmmss
        assert isinstance(entry.created_at, datetime)
        assert entry.updated_at is None

    def test_update_content(self):
        """Test updating content of a journal entry."""
        # Create an entry
        entry = JournalEntry(title="Original Title", content="Original content")

        # Update content
        original_time = entry.created_at
        entry.update_content("Updated content")

        # Verify changes
        assert entry.content == "Updated content"
        assert entry.updated_at is not None
        assert entry.updated_at > original_time

    def test_tag_operations(self):
        """Test adding and removing tags."""
        # Create an entry with no tags
        entry = JournalEntry(title="Tag Test", content="Testing tags", tags=[])

        # Add tags
        entry.add_tag("important")
        assert "important" in entry.tags
        assert len(entry.tags) == 1

        # Add duplicate tag (should not add)
        entry.add_tag("important")
        assert len(entry.tags) == 1

        # Add another tag
        entry.add_tag("follow-up")
        assert "follow-up" in entry.tags
        assert len(entry.tags) == 2

        # Remove a tag
        result = entry.remove_tag("important")
        assert result is True
        assert "important" not in entry.tags
        assert len(entry.tags) == 1

        # Remove non-existent tag
        result = entry.remove_tag("nonexistent")
        assert result is False
        assert len(entry.tags) == 1

    def test_id_generation(self):
        """Test that IDs are generated correctly based on timestamp."""
        # Create entries with custom timestamp-based IDs
        current_time = datetime.now()
        expected_id = current_time.strftime("%Y%m%d%H%M%S")

        entry = JournalEntry(
            id=expected_id, title="ID Test", content="Testing ID generation"
        )

        assert entry.id == expected_id

    def test_json_serialization(self):
        """Test JSON serialization of a JournalEntry."""
        # Create an entry
        entry = JournalEntry(
            title="JSON Test",
            content="Testing JSON serialization",
            tags=["json", "test"],
        )

        # Convert to dict/JSON
        json_data = entry.model_dump()

        # Verify fields
        assert json_data["title"] == "JSON Test"
        assert json_data["content"] == "Testing JSON serialization"
        assert json_data["tags"] == ["json", "test"]
        assert "id" in json_data
        assert "created_at" in json_data


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
