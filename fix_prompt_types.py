#!/usr/bin/env python
"""
Utility script to fix prompt types persistence in the database.
This script directly ensures the prompt_types table exists and
is properly populated with the default values.
"""
import os
import sys
import sqlite3
import logging
import json
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the default prompt types
DEFAULT_PROMPT_TYPES = [
    {
        "id": "default",
        "name": "Default Summary",
        "prompt": "Summarize this journal entry. Extract key topics and mood. Return as JSON:",
    },
    {
        "id": "detailed",
        "name": "Detailed Analysis",
        "prompt": "Provide a detailed analysis of this journal entry. Identify key themes, emotional states, and important insights. Extract key topics and mood. Return as JSON:",
    },
    {
        "id": "creative",
        "name": "Creative Insights",
        "prompt": "Read this journal entry and create an insightful, reflective summary that captures the essence of the writing. Extract key topics and mood. Return as JSON:",
    },
    {
        "id": "concise",
        "name": "Concise Summary",
        "prompt": "Create a very brief summary of this journal entry in 2-3 sentences. Extract key topics and mood. Return as JSON:",
    },
]


def fix_prompt_types(db_path="./journal_data/journal.db"):
    """
    Ensure prompt_types table exists and is properly set up.

    Args:
        db_path: Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False

    logger.info(f"Fixing prompt types in database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Ensure the prompt_types table exists
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS prompt_types (
            id TEXT NOT NULL,
            config_id TEXT NOT NULL,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            PRIMARY KEY (id, config_id)
        )
        """
        )

        # Check if min_similarity column exists in config table
        cursor.execute("PRAGMA table_info(config)")
        columns = [info[1] for info in cursor.fetchall()]
        if "min_similarity" not in columns:
            cursor.execute(
                "ALTER TABLE config ADD COLUMN min_similarity REAL DEFAULT 0.5"
            )

        # Get the config_id (usually "default")
        cursor.execute("SELECT id FROM config LIMIT 1")
        row = cursor.fetchone()
        config_id = row[0] if row else "default"

        # Check if custom prompt types exist
        cursor.execute("SELECT COUNT(*) FROM prompt_types")
        count = cursor.fetchone()[0]

        # If no prompt types or forced reset, delete existing and add defaults
        cursor.execute("DELETE FROM prompt_types WHERE config_id = ?", (config_id,))

        # Insert default prompt types
        for pt in DEFAULT_PROMPT_TYPES:
            cursor.execute(
                "INSERT INTO prompt_types (id, config_id, name, prompt) VALUES (?, ?, ?, ?)",
                (pt["id"], config_id, pt["name"], pt["prompt"]),
            )

        # Commit changes
        conn.commit()
        logger.info(f"Successfully fixed prompt types for config_id: {config_id}")

        # Verify the prompt types
        cursor.execute(
            "SELECT id, name FROM prompt_types WHERE config_id = ?", (config_id,)
        )
        rows = cursor.fetchall()
        logger.info(
            f"Prompt types in the database: {', '.join(f'{r[0]}:{r[1]}' for r in rows)}"
        )

        return True

    except Exception as e:
        logger.error(f"Error fixing prompt types: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    db_path = "./journal_data/journal.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    success = fix_prompt_types(db_path)
    if success:
        logger.info("Database prompt types fixed successfully")
    else:
        logger.error("Failed to fix database prompt types")
        sys.exit(1)
