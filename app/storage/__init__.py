"""
Storage package for the journal application.

This package provides modular storage components for journal entries,
vector search, configuration, summaries, tags, and images.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import JournalEntry, BatchAnalysis
from app.storage.entries import EntryStorage
from app.storage.vector_search import VectorStorage
from app.storage.config import ConfigStorage
from app.storage.summaries import SummaryStorage
from app.storage.images import ImageStorage
from app.storage.tags import TagStorage
from app.storage.batch_analyses import BatchAnalysisStorage


class StorageManager:
    """
    Facade for storage components that preserves the existing interface.

    This class delegates to specialized storage components while maintaining
    backward compatibility with existing code.
    """

    def __init__(self, base_dir="./journal_data"):
        """
        Initialize all storage components.

        Args:
            base_dir: Base directory for all storage (default: ./journal_data)
        """
        self.base_dir = base_dir
        # Initialize all storage components
        self.entries = EntryStorage(base_dir)
        self.vectors = VectorStorage(base_dir)
        self.config = ConfigStorage(base_dir)
        self.summaries = SummaryStorage(base_dir)
        self.images = ImageStorage(base_dir)
        self.tags = TagStorage(base_dir)
        self.batch_analyses = BatchAnalysisStorage(base_dir)  # New batch analysis component

    # Entry management methods

    def save_entry(self, entry: JournalEntry) -> str:
        """Save a journal entry and index it for vector search."""
        entry_id = self.entries.save_entry(entry)
        # Also index for vector search
        self.vectors.index_entry(entry)
        return entry_id

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get a journal entry by ID."""
        return self.entries.get_entry(entry_id)

    def update_entry(
        self, entry_id: str, update_data: Dict[str, Any]
    ) -> Optional[JournalEntry]:
        """Update an existing entry."""
        entry = self.entries.update_entry(entry_id, update_data)
        if entry:
            # Re-index for vector search if content was updated
            if "content" in update_data or "title" in update_data:
                self.vectors.index_entry(entry)
        return entry

    def get_entries(
        self,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        favorite: Optional[bool] = None,
    ) -> List[JournalEntry]:
        """Get entries with optional filtering by date, tags, folder, "
        "and favorite status."""
        return self.entries.get_entries(
            limit, offset, date_from, date_to, tags, folder, favorite
        )

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry by ID."""
        return self.entries.delete_entry(entry_id)

    def get_entry_by_title(self, title: str) -> Optional[JournalEntry]:
        """Find entry by title."""
        return self.entries.get_entry_by_title(title)

    def text_search(
        self,
        query: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        favorite: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """Perform text-based search."""
        return self.entries.text_search(
            query, date_from, date_to, tags, folder, favorite, limit, offset
        )

    def get_entries_by_date(
        self,
        date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JournalEntry]:
        """Get entries created on a specific date for calendar view."""
        return self.entries.get_entries_by_date(date, limit, offset)

    # Tag methods

    def get_entries_by_tag(
        self, tag: str, limit: int = 10, offset: int = 0
    ) -> List[JournalEntry]:
        """Find entries by tag."""
        entry_ids = self.tags.get_entries_by_tag(tag, limit, offset)
        entries = []
        for entry_id in entry_ids:
            entry = self.get_entry(entry_id)
            if entry:
                entries.append(entry)
        return entries

    def get_all_tags(self) -> List[str]:
        """Get all unique tags."""
        return self.tags.get_all_tags()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about entries and tags."""
        stats = {
            "total_entries": 0,
            "oldest_entry": None,
            "newest_entry": None,
            "total_tags": 0,
            "most_used_tags": [],
        }

        # Get entry stats
        entries = self.get_entries(limit=1)
        stats["total_entries"] = len(entries)

        if entries:
            # Get date range
            oldest = self.entries.get_entries(limit=1, offset=0)
            newest = self.entries.get_entries(limit=1, offset=0)

            if oldest:
                stats["oldest_entry"] = oldest[0].created_at.isoformat()
            if newest:
                stats["newest_entry"] = newest[0].created_at.isoformat()

        # Get tag stats
        all_tags = self.tags.get_all_tags()
        stats["total_tags"] = len(all_tags)
        stats["most_used_tags"] = self.tags.get_popular_tags(5)

        return stats

    # Vector search methods

    def update_vectors_with_embeddings(
        self, entry_id: str, embeddings: Dict[int, Any]
    ) -> bool:
        """Update vector embeddings for an entry."""
        return self.vectors.update_vectors_with_embeddings(entry_id, embeddings)

    def get_chunks_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get text chunks that don't have embeddings yet."""
        return self.vectors.get_chunks_without_embeddings(limit)

    def semantic_search(
        self,
        query_embedding: Any,
        limit: int = 5,
        offset: int = 0,
        batch_size: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings."""
        results = self.vectors.semantic_search(
            query_embedding, limit, offset, batch_size
        )

        # Fetch complete entries for each result
        result_with_entries = []
        for result in results:
            entry = self.get_entry(result["entry_id"])
            if entry:
                result["entry"] = entry
                result_with_entries.append(result)

        return result_with_entries

    # Configuration methods

    def save_llm_config(self, config) -> bool:
        """Save LLM configuration."""
        return self.config.save_llm_config(config)

    def get_llm_config(self, config_id: str = "default"):
        """Get LLM configuration."""
        return self.config.get_llm_config(config_id)

    # Summary methods

    def save_entry_summary(self, entry_id: str, summary) -> bool:
        """Save an entry summary."""
        return self.summaries.save_entry_summary(entry_id, summary)

    def get_entry_summaries(self, entry_id: str) -> List:
        """Get summaries for an entry."""
        return self.summaries.get_entry_summaries(entry_id)

    def delete_entry_summary(self, summary_id: str) -> bool:
        """Delete an entry summary."""
        return self.summaries.delete_entry_summary(summary_id)

    # Image methods

    def save_image(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        entry_id: Optional[str] = None,
        description: str = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Save an image file."""
        return self.images.save_image(
            file_data, filename, mime_type, entry_id, description, width, height
        )

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get image metadata."""
        return self.images.get_image(image_id)

    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """Get binary image data."""
        return self.images.get_image_data(image_id)

    def delete_image(self, image_id: str) -> bool:
        """Delete an image."""
        return self.images.delete_image(image_id)

    def get_entry_images(self, entry_id: str) -> List[Dict[str, Any]]:
        """Get images for an entry."""
        return self.images.get_entry_images(entry_id)

    def update_image_metadata(
        self, image_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update image metadata."""
        return self.images.update_image_metadata(image_id, updates)

    def get_orphaned_images(self) -> List[Dict[str, Any]]:
        """Get images not associated with any entry."""
        return self.images.get_orphaned_images()

    def assign_image_to_entry(self, image_id: str, entry_id: str) -> bool:
        """Associate an image with an entry."""
        return self.images.assign_image_to_entry(image_id, entry_id)

    # Advanced search functionality

    def advanced_search(
        self,
        query: str = "",
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        favorite: Optional[bool] = None,
        semantic: bool = False,
        limit: int = 100,
        offset: int = 0,
        folder: Optional[str] = None,
    ) -> List[JournalEntry]:
        """
        Advanced search for journal entries with multiple filters.

        This integrates text search and semantic search capabilities.
        """
        # If using semantic search with a query, process it differently
        if semantic and query.strip():
            # Import here to avoid circular imports
            from app.llm_service import LLMService

            llm_service = LLMService()

            try:
                # Get query embedding
                query_embedding = llm_service.get_embedding(query)
                if query_embedding is not None:
                    # Get semantic search results
                    semantic_results = self.semantic_search(
                        query_embedding=query_embedding,
                        limit=100,  # Get more results for filtering
                    )

                    if semantic_results:
                        # Extract entry IDs from semantic results
                        entry_ids = [result["entry_id"] for result in semantic_results]

                        # Load full entries
                        all_entries = []
                        for entry_id in entry_ids:
                            entry = self.get_entry(entry_id)
                            if entry:
                                all_entries.append(entry)

                        # Apply additional filters including folder and favorite
                        filtered_entries = []
                        for entry in all_entries:
                            # Check tag filter
                            if tags and not any(
                                tag.lower() in [t.lower() for t in entry.tags]
                                for tag in tags
                            ):
                                continue

                            # Check date filters
                            if date_from and entry.created_at < date_from:
                                continue

                            if date_to and entry.created_at > date_to:
                                continue

                            # Check folder filter
                            if folder is not None and entry.folder != folder:
                                continue

                            # Check favorite filter
                            if favorite is not None and entry.favorite != favorite:
                                continue

                            filtered_entries.append(entry)

                        # Apply pagination
                        return filtered_entries[offset : offset + limit]  # noqa: E203
            except Exception as e:
                logging.getLogger(__name__).error(f"Semantic search error: {str(e)}")
                # Fall back to regular search on error

        # Regular search path (also fallback if semantic search fails)
        if not query.strip():
            # Get all entries matching date, tag, folder, and favorite filters
            all_entries = self.get_entries(
                limit=1000,  # Get more to filter properly
                offset=0,
                date_from=date_from,
                date_to=date_to,
                tags=tags,
                folder=folder,
                favorite=favorite,
            )

            # Apply pagination
            return all_entries[offset : offset + limit]  # noqa: E203

        # Regular text search with additional filtering
        entries = self.text_search(
            query=query,
            date_from=date_from,
            date_to=date_to,
            tags=tags,
            folder=folder,
            favorite=favorite,
            limit=1000,  # Get more entries
            offset=0,
        )

        # Apply pagination
        return entries[offset : offset + limit]  # noqa: E203

    # Journal organization methods

    def get_favorite_entries(
        self,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> List[JournalEntry]:
        """Get favorite entries with optional filtering."""
        return self.entries.get_favorite_entries(
            limit, offset, date_from, date_to, tags
        )

    def batch_update_folder(
        self,
        entry_ids: List[str],
        folder: Optional[str],
    ) -> int:
        """Update the folder for multiple entries at once."""
        return self.entries.batch_update_folder(entry_ids, folder)

    def batch_toggle_favorite(
        self,
        entry_ids: List[str],
        favorite: bool,
    ) -> int:
        """Set favorite status for multiple entries at once."""
        return self.entries.batch_toggle_favorite(entry_ids, favorite)

    def get_folders(self) -> List[str]:
        """Get all unique folder names used in the journal."""
        return self.entries.get_folders()

    def get_entries_by_folder(
        self,
        folder: str,
        limit: int = 10,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[JournalEntry]:
        """Get entries in a specific folder, with optional date filtering.

        Args:
            folder: The folder path to filter by
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip for pagination
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering

        Returns:
            List of JournalEntry objects in the specified folder
        """
        return self.entries.get_entries_by_folder(
            folder, limit, offset, date_from, date_to
        )

    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder in the journal system.

        Args:
            folder_name: Name of the folder to create

        Returns:
            True if the folder was created successfully, False otherwise
        """
        return self.entries.create_folder(folder_name)

    # Batch Analysis methods
    
    def save_batch_analysis(self, analysis: BatchAnalysis) -> bool:
        """
        Save a batch analysis to the database.
        
        Args:
            analysis: BatchAnalysis object to save
            
        Returns:
            True if successful, False otherwise
        """
        return self.batch_analyses.save_batch_analysis(analysis)
        
    def get_batch_analysis(self, batch_id: str) -> Optional[BatchAnalysis]:
        """
        Get a batch analysis by ID.
        
        Args:
            batch_id: ID of the batch analysis to retrieve
            
        Returns:
            BatchAnalysis object if found, None otherwise
        """
        return self.batch_analyses.get_batch_analysis(batch_id)
        
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
        return self.batch_analyses.get_batch_analyses(limit, offset)
        
    def delete_batch_analysis(self, batch_id: str) -> bool:
        """
        Delete a batch analysis by ID.
        
        Args:
            batch_id: ID of the batch analysis to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.batch_analyses.delete_batch_analysis(batch_id)
        
    def get_entry_batch_analyses(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get all batch analyses that include a specific entry.
        
        Args:
            entry_id: ID of the journal entry
            
        Returns:
            List of dictionaries with basic batch analysis info
        """
        return self.batch_analyses.get_entry_batch_analyses(entry_id)
