#!/usr/bin/env python3
"""
Cleanup script for removing existing 0-length chat sessions.

This script should be run after implementing the lazy session creation feature
to clean up any existing empty sessions that were created before the fix.
"""

import logging
from app.storage.chat import ChatStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main cleanup function."""
    try:
        logger.info("Starting cleanup of 0-length chat sessions...")

        # Initialize chat storage
        chat_storage = ChatStorage("./journal_data")

        # Run cleanup
        deleted_count = chat_storage.cleanup_empty_sessions()

        if deleted_count > 0:
            logger.info(f"Successfully cleaned up {deleted_count} empty chat sessions")
        else:
            logger.info("No empty sessions found to clean up")

        logger.info("Cleanup completed successfully")

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise


if __name__ == "__main__":
    main()
