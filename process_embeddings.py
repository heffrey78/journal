#!/usr/bin/env python3
"""
Utility script to process embeddings for journal entries.

This script processes all journal entries that don't have embeddings yet,
generating vector embeddings using Ollama and storing them in SQLite.
"""
import time
import argparse
import sys
from app.storage import StorageManager
from app.llm_service import LLMService


def process_embeddings(
    batch_size=10, model_name="nomic-embed-text:latest", verbose=True
):
    """
    Process embeddings for all journal entries that don't have them yet.

    Args:
        batch_size: Number of chunks to process in each batch
        model_name: Ollama model to use for embeddings
        verbose: Whether to print progress information

    Returns:
        Total number of chunks processed
    """
    # Initialize services
    storage = StorageManager()
    llm = LLMService(model_name=model_name, storage_manager=storage)

    if verbose:
        print(f"Processing embeddings for journal entries using model: {model_name}")
        print("This may take some time depending on the number of entries...")

    total_processed = 0
    start_time = time.time()

    while True:
        # Process in batches
        processed = llm.process_entries_without_embeddings(limit=batch_size)
        if processed == 0:
            break

        total_processed += processed
        if verbose:
            print(f"Processed {total_processed} chunks so far...")

        # Small delay to avoid overwhelming Ollama
        time.sleep(0.5)

    elapsed_time = time.time() - start_time

    if verbose:
        print("\nFinished processing embeddings:")
        print(f"- Total chunks processed: {total_processed}")
        print(f"- Time taken: {elapsed_time:.2f} seconds")

        if total_processed > 0:
            print(
                f"- Average time per chunk: {elapsed_time/total_processed:.2f} seconds"
            )

    return total_processed


def main():
    """Main function to run the embedding processor"""
    parser = argparse.ArgumentParser(
        description="Process embeddings for journal entries using Ollama"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of chunks to process in each batch",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="nomic-embed-text:latest",
        help="Ollama model to use for embeddings",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Run without printing progress information"
    )

    args = parser.parse_args()

    # Check if Ollama is available
    try:
        import ollama

        # Quick test to ensure we can connect to Ollama
        ollama.embeddings(model=args.model, prompt="test")
    except Exception as e:
        print(
            "ERROR: Ollama is not available. Please ensure it's installed and running."
        )
        print(f"Exception: {e}")
        return 1

    # Process embeddings
    total = process_embeddings(
        batch_size=args.batch_size, model_name=args.model, verbose=not args.quiet
    )

    if not args.quiet:
        if total == 0:
            print("No new embeddings needed to be processed.")
        else:
            print("Embedding processing completed successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
