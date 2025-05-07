#!/usr/bin/env python3
"""
Debug script to investigate text search issues.
"""

import os
import json
import sqlite3
from app.storage import StorageManager


def dump_entry_content():
    """Display all entry content to verify what's actually in the database and files"""
    storage = StorageManager()

    # Connect directly to the database for debugging
    conn = sqlite3.connect(storage.db_path)
    cursor = conn.cursor()

    # Get all entries
    cursor.execute("SELECT id, title, file_path, tags FROM entries")
    rows = cursor.fetchall()

    print(f"Found {len(rows)} entries in the database:")
    print("=" * 60)

    for row in rows:
        entry_id, title, file_path, tags_json = row
        tags = json.loads(tags_json) if tags_json else []

        print(f"Entry ID: {entry_id}")
        print(f"Title: {title}")
        print(f"Tags: {tags}")

        # Read actual file content
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                # Print summary of content
                content_preview = (
                    content[:100] + "..." if len(content) > 100 else content
                )
                print(f"Content: {content_preview}")

                # Check for specific terms
                search_terms = ["errands", "savings"]
                found_terms = [
                    term for term in search_terms if term.lower() in content.lower()
                ]
                if found_terms:
                    print(f"FOUND TERMS: {', '.join(found_terms)}")
        else:
            print(f"WARNING: File not found: {file_path}")

        print("-" * 60)

    conn.close()


def test_direct_search():
    """Test searching directly in files"""
    storage = StorageManager()

    # Connect to database
    conn = sqlite3.connect(storage.db_path)
    cursor = conn.cursor()

    # Get all file paths
    cursor.execute("SELECT id, file_path FROM entries")
    rows = cursor.fetchall()

    # Search term
    search_term = "errands"

    print(f"\nSearching for '{search_term}' directly in files:")
    print("=" * 60)

    found = 0
    for entry_id, file_path in rows:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                if search_term.lower() in content.lower():
                    found += 1
                    print(f"Found in entry {entry_id}")
                    print(f"File path: {file_path}")
                    # Show context around the term
                    index = content.lower().find(search_term.lower())
                    start = max(0, index - 30)
                    end = min(len(content), index + 30 + len(search_term))
                    context = content[start:end]
                    print(f"Context: ...{context}...")
                    print("-" * 60)

    print(f"Found '{search_term}' in {found} entries")


if __name__ == "__main__":
    print("Journal Entry Debug Info")
    print("======================\n")

    # Display all entry content
    dump_entry_content()

    # Test searching directly
    test_direct_search()
