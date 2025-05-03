#!/usr/bin/env python3
"""
Test script for demonstrating vector search functionality in the journal app.

This script shows how to:
1. Create journal entries
2. Process embeddings using Ollama
3. Perform semantic searches

Prerequisites:
- Ollama must be installed and running locally
- All dependencies must be installed (numpy, scikit-learn, ollama)
"""
import os
import time
import sys
from app.models import JournalEntry
from app.storage import StorageManager
from app.llm_service import LLMService

# Configure test data directory to avoid affecting production data
TEST_DATA_DIR = "./test_journal_data"


def setup_test_environment():
    """Set up a clean test environment"""
    import shutil

    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    os.makedirs(os.path.join(TEST_DATA_DIR, "entries"), exist_ok=True)


def create_test_entries(storage):
    """Create sample journal entries for testing"""
    entries = [
        JournalEntry(
            title="My Day at the Beach",
            content=(
                "Today I went to the beach and it was absolutely wonderful. "
                "The waves were gentle, and the sun was shining brightly. "
                "I built a sandcastle and collected seashells along the shore. "
                "The ocean breeze was refreshing, and I felt very relaxed. "
                "I'm planning to go back next weekend if the weather is nice."
            ),
            tags=["beach", "relaxation", "nature"],
        ),
        JournalEntry(
            title="Learning Python Programming",
            content=(
                "I spent the day learning Python programming. "
                "I focused on data structures like lists and dictionaries. "
                "I also learned about using NumPy for numerical calculations "
                "and scikit-learn for machine learning applications. "
                "Programming is challenging but very "
                "rewarding when things work correctly."
            ),
            tags=["programming", "python", "learning"],
        ),
        JournalEntry(
            title="Thoughts on Climate Change",
            content=(
                "I've been reading about climate change and its effects on our planet. "
                "Rising temperatures are causing polar ice caps "
                "to melt at an alarming rate. "
                "This leads to rising sea levels and threatens coastal communities. "
                "We need to take urgent action to reduce carbon "
                "emissions and transition "
                "to renewable energy sources like solar and wind power."
            ),
            tags=["climate", "environment", "thoughts"],
        ),
        JournalEntry(
            title="My Favorite Recipe",
            content=(
                "I tried a new pasta recipe today that turned out delicious. "
                "I used fresh tomatoes, garlic, basil, and olive oil "
                "to make the sauce. "
                "The key was to cook the garlic slowly to bring out its sweetness. "
                "I paired it with a simple green salad and some crusty bread. "
                "I'll definitely be making this again soon."
            ),
            tags=["cooking", "food", "recipes"],
        ),
    ]

    entry_ids = []
    for entry in entries:
        entry_id = storage.save_entry(entry)
        entry_ids.append(entry_id)
        print(f"Created entry: {entry.title} (ID: {entry_id})")

    return entry_ids


def process_embeddings(llm_service):
    """Process embeddings for all journal entries"""
    print("\nProcessing embeddings...")
    total_processed = 0

    while True:
        # Process in small batches
        processed = llm_service.process_entries_without_embeddings(limit=5)
        if processed == 0:
            break

        total_processed += processed
        print(f"Processed {total_processed} chunks so far...")
        time.sleep(1)  # Small delay to avoid overwhelming Ollama

    print(f"Finished processing embeddings: {total_processed} chunks processed.")
    return total_processed


def perform_semantic_searches(llm_service):
    """Perform various semantic searches and display results"""
    search_queries = [
        "ocean and beaches",
        "programming and software development",
        "environmental issues",
        "cooking and food",
    ]

    print("\nPerforming semantic searches:")
    for query in search_queries:
        print(f"\nSearch query: '{query}'")
        results = llm_service.semantic_search(query, limit=2)

        if not results:
            print("  No results found.")
            continue

        for i, result in enumerate(results):
            entry = result["entry"]
            similarity = result["similarity"]
            print(f"  Result {i+1}: '{entry.title}' (Similarity: {similarity:.4f})")
            print(f"    Tags: {', '.join(entry.tags)}")
            print(f"    Text snippet: {result['text'][:100]}...")


def main():
    """Main function to run the test"""
    # Check if Ollama is available
    try:
        import ollama

        ollama.embeddings(model="nomic-embed-text:latest", prompt="test")
    except Exception as e:
        print(
            "ERROR: Ollama is not available. "
            "Please ensure it's installed and running."
        )
        print(f"Exception: {e}")
        return 1

    print(f"Setting up test environment in {TEST_DATA_DIR}")
    setup_test_environment()

    # Initialize storage and LLM service
    storage = StorageManager(base_dir=TEST_DATA_DIR)
    llm_service = LLMService(
        model_name="nomic-embed-text:latest", storage_manager=storage
    )

    # Create test entries
    create_test_entries(storage)

    # Process embeddings using Ollama
    process_embeddings(llm_service)

    # Perform semantic searches
    perform_semantic_searches(llm_service)

    print("\nTest completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
