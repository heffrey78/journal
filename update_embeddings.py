#!/usr/bin/env python3
"""
Utility script to automatically generate embeddings for journal entries.

This script:
1. Checks for journal entries that don't have embeddings
2. Generates embeddings using Ollama
3. Updates the SQLite database with the new embeddings
4. Reports a summary of the process

Usage:
  python update_embeddings.py [--batch-size N] [--model MODEL_NAME]

Example:
  python update_embeddings.py --batch-size 20 --model nomic-embed-text:latest
"""

import argparse
import sys
import time
from app.storage import StorageManager
from app.llm_service import LLMService


def update_all_embeddings(batch_size=10, model_name="nomic-embed-text:latest"):
    """Process all entries without embeddings in batches"""
    print(f"Updating embeddings with batch size: {batch_size}")
    print(f"Using embedding model: {model_name}")

    storage = StorageManager()
    llm = LLMService(embedding_model=model_name, storage_manager=storage)

    # Record start time
    start_time = time.time()

    # Process entries without embeddings
    count = llm.process_entries_without_embeddings(limit=batch_size)

    # Calculate and display timing information
    elapsed_time = time.time() - start_time

    if count > 0:
        print("\nFinished updating embeddings!")
        print(f"Total chunks processed: {count}")
        print(f"Total time: {elapsed_time:.2f} seconds")
    else:
        print("\nNo entries found that need embeddings.")
        print("All entries have embeddings already.")

    return count


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Update embeddings for journal entries"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of chunks to process at once (default: 10)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="nomic-embed-text:latest",
        help="Ollama model to use for embeddings (default: nomic-embed-text:latest)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate batch size
    if args.batch_size < 1:
        print("Error: Batch size must be at least 1")
        sys.exit(1)

    # Run the update process
    update_all_embeddings(batch_size=args.batch_size, model_name=args.model)
