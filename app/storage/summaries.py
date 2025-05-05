import json
import logging
from datetime import datetime
from typing import List
from uuid import uuid4

from app.storage.base import BaseStorage


class SummaryStorage(BaseStorage):
    """Handles storage and retrieval of entry summaries."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize summary storage with database setup.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        super().__init__(base_dir)
        self._init_table()

    def _init_table(self):
        """Initialize entry_summaries table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
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
        # Create index for entry summaries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_entry_summaries_entry_id "
            "ON entry_summaries(entry_id)"
        )
        conn.commit()
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
        conn = self.get_db_connection()
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
        from app.llm_service import EntrySummary

        conn = self.get_db_connection()
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
        conn = self.get_db_connection()
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
