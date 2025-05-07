#!/usr/bin/env python3
"""
Simple test script to verify batch analysis functionality.
"""
from app.storage import StorageManager
from app.models import BatchAnalysis
import uuid


def main():
    """Test batch analysis functionality."""
    print("Testing Batch Analysis Functionality")
    print("-" * 50)

    # Initialize the storage manager with the real database
    storage = StorageManager()

    # Create a sample batch analysis
    print("Creating a sample batch analysis...")
    
    # Get some real entry IDs from the database to use in our test
    entries = storage.get_entries(limit=3)
    if not entries or len(entries) < 2:
        print("Error: Need at least 2 entries in the database for this test.")
        return
        
    entry_ids = [entry.id for entry in entries]
    
    # Create a unique ID for our test batch analysis
    test_id = f"test-{uuid.uuid4()}"
    
    analysis = BatchAnalysis(
        id=test_id,
        title="Test Weekly Analysis",
        entry_ids=entry_ids,
        date_range="2025-05-01 to 2025-05-07",
        summary="This is a test batch analysis summary created to verify functionality.",
        key_themes=["testing", "batch analysis", "implementation"],
        mood_trends={"focused": 2, "productive": 1},
        notable_insights=["Feature implementation is on track", 
                         "Batch analysis will be useful for weekly reviews"],
        prompt_type="weekly"
    )
    
    # Save the batch analysis
    success = storage.save_batch_analysis(analysis)
    print(f"Batch analysis saved: {success}")
    
    # Retrieve the batch analysis
    retrieved = storage.get_batch_analysis(test_id)
    if retrieved:
        print("\nSuccessfully retrieved batch analysis:")
        print(f"- ID: {retrieved.id}")
        print(f"- Title: {retrieved.title}")
        print(f"- Entry count: {len(retrieved.entry_ids)}")
        print(f"- Summary: {retrieved.summary}")
        print(f"- Key themes: {retrieved.key_themes}")
        print(f"- Prompt type: {retrieved.prompt_type}")
    else:
        print("Error: Failed to retrieve batch analysis.")
        
    # Get a list of batch analyses
    print("\nGetting list of batch analyses:")
    all_analyses = storage.get_batch_analyses(limit=10)
    print(f"Found {len(all_analyses)} batch analyses")
    
    # Get entry-specific batch analyses for the first entry
    if entry_ids:
        print(f"\nBatch analyses for entry {entry_ids[0]}:")
        entry_analyses = storage.get_entry_batch_analyses(entry_ids[0])
        print(f"Found {len(entry_analyses)} batch analyses for this entry")
        
    # Clean up by deleting our test analysis
    print("\nDeleting test batch analysis...")
    deleted = storage.delete_batch_analysis(test_id)
    print(f"Batch analysis deleted: {deleted}")
    
    # Verify deletion
    should_be_none = storage.get_batch_analysis(test_id)
    if should_be_none is None:
        print("Verified: Batch analysis was successfully deleted.")
    else:
        print("Error: Batch analysis was not properly deleted.")
        
    print("\nBatch analysis test completed!")
    
    
if __name__ == "__main__":
    main()