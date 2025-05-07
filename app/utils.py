"""
Utility functions shared across the application.
"""
from app.storage import StorageManager
from app.llm_service import LLMService

# Create singleton storage manager and LLM service
storage_manager = None
llm_service = None


def get_storage() -> StorageManager:
    """Dependency to get the storage manager instance"""
    global storage_manager
    if storage_manager is None:
        storage_manager = StorageManager()
    return storage_manager


def get_llm_service() -> LLMService:
    """Dependency to get the LLM service instance"""
    global llm_service, storage_manager
    if llm_service is None:
        if storage_manager is None:
            storage_manager = StorageManager()
        llm_service = LLMService(storage_manager=storage_manager)
    return llm_service
