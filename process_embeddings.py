#!/usr/bin/env python3
"""
Utility script to process journal entries and generate embeddings for semantic search.

This script:
1. Processes journal entries that don't have embeddings yet
2. Uses Ollama to generate embeddings for each chunk of text
3. Updates the SQLite database with the embeddings

Usage:
  python process_embeddings.py [batch_size]

Example:
  python process_embeddings.py 10
"""

import sys
import time
from app.storage import StorageManager
from app.llm_service import LLMService


def process_all_embeddings(batch_size=10, model_name="nomic-embed-text:latest"):
    """Process all entries without embeddings in batches"""
    print(f"Processing embeddings with batch size: {batch_size}")
    print(f"Using embedding model: {model_name}")

    # Initialize services
    storage = StorageManager()

    # Initialize LLM service without directly passing embedding_model
    llm_service = LLMService(storage_manager=storage)

    # Update the embedding model in the config if needed
    if llm_service.embedding_model != model_name:
        print(
            "Updating embedding model from "
            f"{llm_service.embedding_model} to {model_name}"
        )

        config = storage.get_llm_config()
        config.embedding_model = model_name
        storage.save_llm_config(config)
        llm_service.reload_config()

    # Process in batches until all are done
    total_processed = 0
    start_time = time.time()

    while True:
        processed = llm_service.process_entries_without_embeddings(limit=batch_size)
        if processed == 0:
            break

        total_processed += processed
        elapsed = time.time() - start_time
        print(f"Processed {total_processed} chunks in {elapsed:.2f} seconds")

    print("\nFinished processing embeddings for all entries!")
    print(f"Total chunks processed: {total_processed}")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

    return total_processed


if __name__ == "__main__":
    # Get batch size from command line or use default
    batch_size = 10
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
            if batch_size < 1:
                print("Batch size must be at least 1")
                sys.exit(1)
        except ValueError:
            print(f"Invalid batch size: {sys.argv[1]}")
            print("Using default batch size of 10")

    print(f"Processing embeddings with batch size: {batch_size}")

    try:
        import ollama

        # Test if Ollama is available
        ollama.embeddings(model="nomic-embed-text:latest", prompt="test")
        process_all_embeddings(batch_size)
    except ImportError:
        print("Error: The ollama package is not installed.")
        print("Please install it with: pip install ollama")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        print("Please check if Ollama is running and accessible.")
        sys.exit(1)
