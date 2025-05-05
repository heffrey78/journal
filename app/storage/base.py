import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BaseStorage:
    """Base storage class that handles database connections and initialization."""

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize the base storage with directory setup and database connection.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "journal.db")
        self.entries_dir = os.path.join(base_dir, "entries")
        self.images_dir = os.path.join(base_dir, "images")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.entries_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def get_db_connection(self):
        """Get a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)
