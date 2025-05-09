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
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Existing tables: {', '.join(existing_tables) or 'none'}")

        # Check if config table exists
        if "config" not in existing_tables:
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
            logger.info("Config table created successfully")
        else:
            # Check if min_similarity column exists in config table
            cursor.execute("PRAGMA table_info(config)")
            columns = [info[1] for info in cursor.fetchall()]
            if "min_similarity" not in columns:
                logger.info("Adding min_similarity column to config table")
                cursor.execute(
                    "ALTER TABLE config ADD COLUMN min_similarity REAL DEFAULT 0.5"
                )
                logger.info("min_similarity column added successfully")

        # Check if prompt_types table exists
        if "prompt_types" not in existing_tables:
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
            logger.info("prompt_types table created successfully")

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
            logger.info("Default prompt types added successfully")

        # Check if batch_analyses table exists
        if "batch_analyses" not in existing_tables:
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
            logger.info("batch_analyses table created successfully")

            # Create index for batch_analyses
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_batch_analyses_created_at
                ON batch_analyses(created_at)"""
            )
            logger.info("batch_analyses index created successfully")

        # Check if batch_analysis_entries table exists
        if "batch_analysis_entries" not in existing_tables:
            logger.info("Creating batch_analysis_entries relation table")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_analysis_entries (
                    batch_id TEXT,
                    entry_id TEXT,
                    PRIMARY KEY (batch_id, entry_id),
                    FOREIGN KEY (batch_id) REFERENCES batch_analyses(id)
                    ON DELETE CASCADE,
                    FOREIGN KEY (entry_id) REFERENCES entries(id)
                    ON DELETE CASCADE
                )
                """
            )
            logger.info("batch_analysis_entries table created successfully")

            # Create index for batch_analysis_entries
            cursor.execute(
                """CREATE INDEX IF NOT EXISTS idx_batch_analysis_entries_entry_id
                ON batch_analysis_entries(entry_id)"""
            )
            logger.info("batch_analysis_entries index created successfully")

        # Verify all tables were created properly
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_after_migration = [row[0] for row in cursor.fetchall()]
        required_tables = [
            "config",
            "prompt_types",
            "batch_analyses",
            "batch_analysis_entries",
        ]
        missing_tables = [
            table for table in required_tables if table not in tables_after_migration
        ]

        if missing_tables:
            logger.error(f"Failed to create tables: {', '.join(missing_tables)}")
            conn.rollback()
            return False

        conn.commit()
        logger.info("Database migration completed successfully")
        logger.info(f"Tables after migration: {', '.join(tables_after_migration)}")
        return True

    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate_database()
    if success:
        logger.info("Database migration script executed successfully")
    else:
        logger.error("Database migration failed")
