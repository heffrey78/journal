#!/usr/bin/env python
"""
Database migration script for journal app.

This script updates the database schema by adding necessary tables and columns.
It should be run whenever the database schema changes.
"""
import os
import sqlite3
import logging
from app.models import LLMConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database(db_path="./journal_data/journal.db"):
    """
    Update database schema with new tables/columns.

    Args:
        db_path: Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False

    logger.info(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if config table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='config'"
        )
        if not cursor.fetchone():
            logger.info("Creating config table")
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
        else:
            # Check if min_similarity column exists in config table
            cursor.execute("PRAGMA table_info(config)")
            columns = [info[1] for info in cursor.fetchall()]
            if "min_similarity" not in columns:
                logger.info("Adding min_similarity column to config table")
                cursor.execute(
                    "ALTER TABLE config ADD COLUMN min_similarity REAL DEFAULT 0.5"
                )

        # Check if prompt_types table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_types'"
        )
        if not cursor.fetchone():
            logger.info("Creating prompt_types table")
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

            # Populate with default prompt types
            logger.info("Populating default prompt types")
            # Get default config ID
            cursor.execute("SELECT id FROM config LIMIT 1")
            row = cursor.fetchone()
            config_id = row[0] if row else "default"

            # Use default prompt types from LLMConfig
            default_config = LLMConfig()
            for pt in default_config.prompt_types:
                cursor.execute(
                    "INSERT INTO prompt_types (id, config_id, name, prompt) "
                    "VALUES (?, ?, ?, ?)",
                    (pt.id, config_id, pt.name, pt.prompt),
                )

        # Check if batch_analyses table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='batch_analyses'"
        )
        if not cursor.fetchone():
            logger.info("Creating batch_analyses table")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_analyses (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date_range TEXT,
                    summary TEXT NOT NULL,
                    key_themes TEXT NOT NULL,
                    mood_trends TEXT NOT NULL,
                    notable_insights TEXT NOT NULL,
                    prompt_type TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            
            # Create index for batch_analyses
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_batch_analyses_created_at ON batch_analyses(created_at)"
            )
        
        # Check if batch_analysis_entries table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='batch_analysis_entries'"
        )
        if not cursor.fetchone():
            logger.info("Creating batch_analysis_entries relation table")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_analysis_entries (
                    batch_id TEXT,
                    entry_id TEXT,
                    PRIMARY KEY (batch_id, entry_id),
                    FOREIGN KEY (batch_id) REFERENCES batch_analyses(id) ON DELETE CASCADE,
                    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
                )
                """
            )
            
            # Create index for batch_analysis_entries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_batch_analysis_entries_entry_id ON batch_analysis_entries(entry_id)"
            )

        conn.commit()
        logger.info("Database migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration error: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
