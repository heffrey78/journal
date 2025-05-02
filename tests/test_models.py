import os
import sys
import unittest
from datetime import datetime, timedelta
from pydantic import ValidationError

# Add the parent directory to sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after sys.path modification
from app.models import JournalEntry  # noqa: E402


class TestJournalEntry(unittest.TestCase):
    """Test cases for the JournalEntry model"""

    def test_create_entry(self):
        """Test creating a journal entry with valid data"""
        entry = JournalEntry(title="Test Entry", content="This is a test entry")

        # Validate required fields are set
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.title, "Test Entry")
        self.assertEqual(entry.content, "This is a test entry")
        self.assertIsNotNone(entry.created_at)
        self.assertIsNone(entry.updated_at)
        self.assertEqual(entry.tags, [])

    def test_default_id_format(self):
        """Test that the default ID follows expected format (YYYYMMDDhhmmss)"""
        entry = JournalEntry(title="Test Entry", content="Content")
        # ID should be a string with 14 digits in YYYYMMDDhhmmss format
        self.assertEqual(len(entry.id), 14)
        self.assertTrue(entry.id.isdigit())

        # The timestamp should be close to now
        entry_time = datetime.strptime(entry.id, "%Y%m%d%H%M%S")
        time_diff = datetime.now() - entry_time
        # Check the time difference is small
        self.assertLess(time_diff, timedelta(seconds=5))

    def test_update_content(self):
        """Test updating the content of a journal entry"""
        entry = JournalEntry(title="Test", content="Original content")

        # Store original timestamp
        original_created_at = entry.created_at

        # Update content and verify updated_at is set
        entry.update_content("Updated content")
        self.assertEqual(entry.content, "Updated content")
        self.assertIsNotNone(entry.updated_at)
        self.assertNotEqual(entry.updated_at, original_created_at)
        # created_at shouldn't change
        self.assertEqual(entry.created_at, original_created_at)

    def test_tags_management(self):
        """Test adding and removing tags"""
        entry = JournalEntry(title="Test", content="Content with tags")

        # Add tags
        entry.add_tag("work")
        entry.add_tag("important")
        self.assertEqual(set(entry.tags), {"work", "important"})

        # Adding a duplicate tag shouldn't change anything
        entry.add_tag("work")
        self.assertEqual(len(entry.tags), 2)

        # Test removing tags
        success = entry.remove_tag("work")
        self.assertTrue(success)
        self.assertEqual(entry.tags, ["important"])

        # Test removing a non-existent tag
        success = entry.remove_tag("nonexistent")
        self.assertFalse(success)

    def test_validation(self):
        """Test validation of required fields"""
        # Title is required
        with self.assertRaises(ValidationError):
            JournalEntry(content="Content without title")

        # Content is required
        with self.assertRaises(ValidationError):
            JournalEntry(title="Title without content")


if __name__ == "__main__":
    unittest.main()
