"""
Tests for batch analysis functionality.
"""
import unittest
import os
import tempfile
import shutil
from datetime import datetime
import sqlite3

from app.storage import StorageManager
from app.models import JournalEntry, BatchAnalysis
from app.migrate_db import migrate_database


class BatchAnalysisTest(unittest.TestCase):
    """Test case for batch analysis functionality."""

    def setUp(self):
        """Set up test environment with a temporary storage directory."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Create necessary subdirectories
        os.makedirs(os.path.join(self.test_dir, "entries"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "images"), exist_ok=True)
        
        # Create an empty database file
        db_path = os.path.join(self.test_dir, "journal.db")
        conn = sqlite3.connect(db_path)
        conn.close()
        
        # Initialize database schema
        migrate_database(db_path)
        
        # Now initialize the storage manager
        self.storage = StorageManager(self.test_dir)

        # Create test entries to use in batch analysis
        self.entry1 = JournalEntry(
            title="Test Entry 1",
            content="This is test content for entry 1.",
            tags=["test", "batch"],
            created_at=datetime(2025, 5, 1, 10, 0),
        )
        self.entry1_id = self.storage.save_entry(self.entry1)

        self.entry2 = JournalEntry(
            title="Test Entry 2",
            content="This is test content for entry 2.",
            tags=["test", "analysis"],
            created_at=datetime(2025, 5, 2, 10, 0),
        )
        self.entry2_id = self.storage.save_entry(self.entry2)

        self.entry3 = JournalEntry(
            title="Test Entry 3",
            content="This is test content for entry 3.",
            tags=["test", "batch", "analysis"],
            created_at=datetime(2025, 5, 3, 10, 0),
        )
        self.entry3_id = self.storage.save_entry(self.entry3)

        # Create a sample batch analysis
        self.batch_analysis = BatchAnalysis(
            title="Test Batch Analysis",
            entry_ids=[self.entry1_id, self.entry2_id, self.entry3_id],
            date_range="2025-05-01 to 2025-05-03",
            summary="This is a test batch analysis summary.",
            key_themes=["test", "analysis", "batch"],
            mood_trends={"focused": 2, "productive": 1},
            notable_insights=["Test insight 1", "Test insight 2"],
            prompt_type="test",
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_save_and_get_batch_analysis(self):
        """Test saving and retrieving batch analysis."""
        # Save the batch analysis
        result = self.storage.save_batch_analysis(self.batch_analysis)
        self.assertTrue(result)

        # Retrieve the batch analysis
        retrieved = self.storage.get_batch_analysis(self.batch_analysis.id)
        
        # Verify the retrieved analysis matches the original
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, self.batch_analysis.id)
        self.assertEqual(retrieved.title, self.batch_analysis.title)
        self.assertEqual(len(retrieved.entry_ids), 3)
        self.assertEqual(set(retrieved.entry_ids), 
                         set([self.entry1_id, self.entry2_id, self.entry3_id]))
        self.assertEqual(retrieved.summary, self.batch_analysis.summary)
        self.assertEqual(retrieved.key_themes, self.batch_analysis.key_themes)
        self.assertEqual(retrieved.mood_trends, self.batch_analysis.mood_trends)
        self.assertEqual(retrieved.notable_insights, self.batch_analysis.notable_insights)
        self.assertEqual(retrieved.prompt_type, self.batch_analysis.prompt_type)

    def test_get_batch_analyses_list(self):
        """Test retrieving a list of batch analyses."""
        # Save the batch analysis
        self.storage.save_batch_analysis(self.batch_analysis)
        
        # Create and save another batch analysis
        another_analysis = BatchAnalysis(
            title="Another Test Analysis",
            entry_ids=[self.entry1_id, self.entry2_id],
            date_range="2025-05-01 to 2025-05-02",
            summary="Another test summary.",
            key_themes=["test"],
            mood_trends={"focused": 1},
            notable_insights=["Another test insight"],
            prompt_type="test",
        )
        self.storage.save_batch_analysis(another_analysis)
        
        # Retrieve the list of batch analyses
        analyses = self.storage.get_batch_analyses()
        
        # Verify the list contains both analyses
        self.assertEqual(len(analyses), 2)
        self.assertTrue(any(a.id == self.batch_analysis.id for a in analyses))
        self.assertTrue(any(a.id == another_analysis.id for a in analyses))

    def test_delete_batch_analysis(self):
        """Test deleting a batch analysis."""
        # Save the batch analysis
        self.storage.save_batch_analysis(self.batch_analysis)
        
        # Delete the batch analysis
        result = self.storage.delete_batch_analysis(self.batch_analysis.id)
        self.assertTrue(result)
        
        # Verify it's no longer retrievable
        retrieved = self.storage.get_batch_analysis(self.batch_analysis.id)
        self.assertIsNone(retrieved)
        
        # Verify the list is empty
        analyses = self.storage.get_batch_analyses()
        self.assertEqual(len(analyses), 0)
        
    def test_get_entry_batch_analyses(self):
        """Test retrieving batch analyses that include a specific entry."""
        # Save the batch analysis
        self.storage.save_batch_analysis(self.batch_analysis)
        
        # Create and save another batch analysis with only entry 1
        another_analysis = BatchAnalysis(
            title="Entry 1 Only Analysis",
            entry_ids=[self.entry1_id],
            date_range="2025-05-01",
            summary="Analysis of entry 1.",
            key_themes=["test"],
            mood_trends={"focused": 1},
            notable_insights=["Entry 1 insight"],
            prompt_type="test",
        )
        self.storage.save_batch_analysis(another_analysis)
        
        # Retrieve batch analyses for entry 1
        entry1_analyses = self.storage.get_entry_batch_analyses(self.entry1_id)
        
        # Verify both analyses are included
        self.assertEqual(len(entry1_analyses), 2)
        
        # Retrieve batch analyses for entry 3
        entry3_analyses = self.storage.get_entry_batch_analyses(self.entry3_id)
        
        # Verify only the first analysis is included
        self.assertEqual(len(entry3_analyses), 1)
        self.assertEqual(entry3_analyses[0]["id"], self.batch_analysis.id)


if __name__ == "__main__":
    unittest.main()