"""
Storage functionality for batch analyses.

This module handles the database operations for batch analyses of journal entries.
"""
import json
import logging
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import BatchAnalysis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BatchAnalysisStorage:
    """Storage methods for batch analyses."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize batch analysis storage.
        
        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "journal.db")

    def save_batch_analysis(self, analysis: BatchAnalysis) -> bool:
        """
        Save a batch analysis to the database.
        
        Args:
            analysis: BatchAnalysis object to save
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert complex types to JSON strings
            key_themes_json = json.dumps(analysis.key_themes)
            mood_trends_json = json.dumps(analysis.mood_trends)
            notable_insights_json = json.dumps(analysis.notable_insights)
            
            # Ensure created_at is in ISO format string
            created_at = (
                analysis.created_at.isoformat()
                if isinstance(analysis.created_at, datetime)
                else analysis.created_at
            )
            
            # Insert into batch_analyses table
            cursor.execute(
                """
                INSERT OR REPLACE INTO batch_analyses
                (id, title, date_range, summary, key_themes, mood_trends, 
                 notable_insights, prompt_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.id,
                    analysis.title,
                    analysis.date_range,
                    analysis.summary,
                    key_themes_json,
                    mood_trends_json,
                    notable_insights_json,
                    analysis.prompt_type,
                    created_at,
                ),
            )
            
            # Remove any existing entry associations
            cursor.execute(
                "DELETE FROM batch_analysis_entries WHERE batch_id = ?",
                (analysis.id,)
            )
            
            # Insert entry associations into batch_analysis_entries table
            for entry_id in analysis.entry_ids:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO batch_analysis_entries
                    (batch_id, entry_id)
                    VALUES (?, ?)
                    """,
                    (analysis.id, entry_id),
                )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save batch analysis: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_batch_analysis(self, batch_id: str) -> Optional[BatchAnalysis]:
        """
        Get a batch analysis by ID.
        
        Args:
            batch_id: ID of the batch analysis to retrieve
            
        Returns:
            BatchAnalysis object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the main batch analysis data
            cursor.execute(
                """
                SELECT title, date_range, summary, key_themes, mood_trends,
                       notable_insights, prompt_type, created_at
                FROM batch_analyses
                WHERE id = ?
                """,
                (batch_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
                
            (
                title, date_range, summary, key_themes_json, 
                mood_trends_json, notable_insights_json, 
                prompt_type, created_at
            ) = row
            
            # Get associated entry IDs
            cursor.execute(
                "SELECT entry_id FROM batch_analysis_entries WHERE batch_id = ?",
                (batch_id,)
            )
            entry_ids = [row[0] for row in cursor.fetchall()]
            
            # Parse JSON data
            key_themes = json.loads(key_themes_json)
            mood_trends = json.loads(mood_trends_json) 
            notable_insights = json.loads(notable_insights_json)
            
            # Create and return BatchAnalysis object
            return BatchAnalysis(
                id=batch_id,
                title=title,
                entry_ids=entry_ids,
                date_range=date_range,
                created_at=created_at,
                summary=summary,
                key_themes=key_themes,
                mood_trends=mood_trends,
                notable_insights=notable_insights,
                prompt_type=prompt_type
            )
        except Exception as e:
            logger.error(f"Error retrieving batch analysis: {e}")
            return None
        finally:
            conn.close()

    def get_batch_analyses(
        self, limit: int = 10, offset: int = 0
    ) -> List[BatchAnalysis]:
        """
        Get a list of batch analyses with pagination.
        
        Args:
            limit: Maximum number of analyses to retrieve
            offset: Number of analyses to skip for pagination
            
        Returns:
            List of BatchAnalysis objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get batch analyses with pagination
            cursor.execute(
                """
                SELECT id FROM batch_analyses
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            batch_ids = [row[0] for row in cursor.fetchall()]
            
            # Load each analysis
            analyses = []
            for batch_id in batch_ids:
                analysis = self.get_batch_analysis(batch_id)
                if analysis:
                    analyses.append(analysis)
            
            return analyses
        except Exception as e:
            logger.error(f"Error retrieving batch analyses list: {e}")
            return []
        finally:
            conn.close()

    def delete_batch_analysis(self, batch_id: str) -> bool:
        """
        Delete a batch analysis by ID.
        
        Args:
            batch_id: ID of the batch analysis to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete from batch_analyses table (will cascade to batch_analysis_entries)
            cursor.execute("DELETE FROM batch_analyses WHERE id = ?", (batch_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting batch analysis: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_entry_batch_analyses(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get all batch analyses that include a specific entry.
        
        Args:
            entry_id: ID of the journal entry
            
        Returns:
            List of dictionaries with basic batch analysis info
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT ba.id, ba.title, ba.created_at, ba.prompt_type
                FROM batch_analyses ba
                JOIN batch_analysis_entries bae ON ba.id = bae.batch_id
                WHERE bae.entry_id = ?
                ORDER BY ba.created_at DESC
                """,
                (entry_id,)
            )
            
            results = []
            for row in cursor.fetchall():
                batch_id, title, created_at, prompt_type = row
                
                # Get count of entries in this batch
                cursor.execute(
                    "SELECT COUNT(*) FROM batch_analysis_entries WHERE batch_id = ?",
                    (batch_id,)
                )
                entry_count = cursor.fetchone()[0]
                
                results.append({
                    "id": batch_id,
                    "title": title,
                    "created_at": created_at,
                    "prompt_type": prompt_type,
                    "entry_count": entry_count
                })
                
            return results
        except Exception as e:
            logger.error(f"Error getting batch analyses for entry: {e}")
            return []
        finally:
            conn.close()