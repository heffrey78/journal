#!/usr/bin/env python3
"""
Debug script to investigate text search issues with the fixed approach.
"""

import os
import json
import sqlite3
from app.storage import StorageManager


def run_search_test():
    """Test the text_search method with various search terms"""
    print("Running search diagnostics...")
    print("=" * 60)

    # Initialize storage manager
    storage = StorageManager()

    # List of search terms to test
    search_terms = ["date", "errands", "savings", "python"]

    # Try both exact and approximate terms
    for term in search_terms:
        print(f"Testing search for '{term}':")

        # Run storage text_search
        results = storage.text_search(term)
        print(f"  text_search returned {len(results)} results")

        if results:
            print("  First few results:")
            for i, entry in enumerate(results[:3]):  # Show up to 3 results
                print(f"  - {entry.title} (Tags: {entry.tags})")
                # Show a snippet of content
                preview = (
                    entry.content[:50] + "..."
                    if len(entry.content) > 50
                    else entry.content
                )
                print(f"    Content: {preview}")
        else:
            print("  No results found")

        print("-" * 60)

    # Test tag-specific search
    print("\nTesting tag search:")
    all_tags = storage.get_all_tags()
    print(f"All tags in the system: {all_tags}")

    if all_tags:
        # Try searching for each tag
        for tag in all_tags[:3]:  # Test first 3 tags
            print(f"Searching for tag '{tag}':")
            tag_results = storage.text_search(tag)
            print(f"  Found {len(tag_results)} results")
            if tag_results:
                # Check if the tag is actually in the results
                tag_matches = [
                    e for e in tag_results if tag.lower() in [t.lower() for t in e.tags]
                ]
                print(f"  Entries with exact tag match: {len(tag_matches)}")

    print("\nDirect SQL tests:")
    try:
        # Get database path from entries component
        db_path = storage.entries.db_path
        print(f"Database path: {db_path}")

        # Connect directly to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if entries table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        if cursor.fetchone():
            print("Entries table exists")

            # Count entries in the database
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            print(f"Total entries in database: {count}")

            # SQL-based search test
            test_term = "date"
            print(f"\nDirect SQL search for '{test_term}':")

            cursor.execute("SELECT id, title, tags FROM entries")
            entries = cursor.fetchall()

            matching = 0
            for entry_id, title, tags_json in entries:
                if test_term.lower() in title.lower():
                    matching += 1
                    print(f"Match in title: {title}")
                if tags_json:
                    tags = json.loads(tags_json)
                    if any(test_term.lower() in tag.lower() for tag in tags):
                        matching += 1
                        print(f"Match in tags: {tags}")

            # Check file contents
            cursor.execute("SELECT id, file_path FROM entries")
            files = cursor.fetchall()

            file_matches = 0
            for entry_id, file_path in files:
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        content = f.read()
                        if test_term.lower() in content.lower():
                            file_matches += 1

            # Fixed long line by splitting into two lines
            print(
                f"Found term in {matching} database records and "
                f"{file_matches} file contents"
            )
        else:
            print("Entries table not found in database")

        conn.close()
    except Exception as e:
        print(f"Database test error: {e}")

    print("\nTest direct function calls:")
    # Test the EntryStorage's text_search implementation directly
    try:
        print("Testing EntryStorage.text_search directly:")
        results = storage.entries.text_search("date")
        print(f"Direct text_search returned {len(results)} results")
    except Exception as e:
        print(f"Direct text_search error: {e}")


if __name__ == "__main__":
    run_search_test()
