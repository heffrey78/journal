#!/usr/bin/env python3
"""
Test script to verify batch analysis functionality in the LLM service.
"""
from app.storage import StorageManager
from app.llm_service import LLMService, BatchAnalysisError
from app.models import BatchAnalysis
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_batch_analysis():
    """Test the batch analysis functionality."""
    print("Testing Batch Analysis LLM Service")
    print("-" * 50)

    # Initialize the storage manager with the real database
    storage = StorageManager()
    
    # Initialize the LLM service
    llm_service = LLMService(storage_manager=storage)
    
    # Get some entries to analyze
    print("Fetching entries to analyze...")
    entries = storage.get_entries(limit=3)
    
    if not entries or len(entries) < 2:
        print("Error: Need at least 2 entries in the database for this test.")
        return
        
    print(f"Found {len(entries)} entries for analysis.")
    
    # Progress tracking function
    def progress_callback(progress):
        percentage = int(progress * 100)
        print(f"Analysis progress: {percentage}%")
    
    # Test with prompt type "weekly"
    prompt_type = "weekly"
    print(f"\nPerforming batch analysis with prompt type: {prompt_type}")
    try:
        batch_analysis = llm_service.analyze_entries_batch(
            entries=entries,
            title="Test Weekly Analysis",
            prompt_type=prompt_type,
            progress_callback=progress_callback
        )
        
        print("\nBatch Analysis Result:")
        print(f"- Title: {batch_analysis.title}")
        print(f"- Date Range: {batch_analysis.date_range}")
        print(f"- Summary: {batch_analysis.summary[:150]}...") # Truncated for readability
        print(f"- Key themes: {batch_analysis.key_themes}")
        print(f"- Number of mood trends: {len(batch_analysis.mood_trends)}")
        print(f"- Notable insights: {len(batch_analysis.notable_insights)}")
        
        # Save the batch analysis
        print("\nSaving batch analysis to database...")
        saved = storage.save_batch_analysis(batch_analysis)
        print(f"Saved successfully: {saved}")
        
        # Retrieve the batch analysis
        retrieved = storage.get_batch_analysis(batch_analysis.id)
        if retrieved:
            print("Successfully retrieved batch analysis from database")
            
        # Clean up
        print("\nCleaning up test data...")
        deleted = storage.delete_batch_analysis(batch_analysis.id)
        print(f"Deleted successfully: {deleted}")
        
    except BatchAnalysisError as e:
        print(f"Error in batch analysis: {e}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    test_batch_analysis()