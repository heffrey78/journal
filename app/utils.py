"""
Utility functions shared across the application.
"""
import logging
from app.storage import StorageManager
from app.llm_service import LLMService
from app.migrate_db import migrate_database

# Configure logging
logger = logging.getLogger(__name__)

# Create singleton storage manager and LLM service
storage_manager = None
llm_service = None


def initialize_database():
    """Initialize the database with required schema"""
    logger.info("Initializing database...")
    success = migrate_database()
    if success:
        logger.info("Database initialized successfully")
    else:
        logger.warning("Database initialization failed - some features may not work")
    return success


def get_storage() -> StorageManager:
    """Dependency to get the storage manager instance"""
    global storage_manager
    if storage_manager is None:
        # Run the database migration when first initializing the storage manager
        initialize_database()
        storage_manager = StorageManager()
    return storage_manager


def get_llm_service() -> LLMService:
    """Dependency to get the LLM service instance"""
    global llm_service, storage_manager
    if llm_service is None:
        if storage_manager is None:
            # Run the database migration when first initializing the storage manager
            initialize_database()
            storage_manager = StorageManager()
        llm_service = LLMService(storage_manager=storage_manager)
    return llm_service
