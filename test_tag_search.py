#!/usr/bin/env python3
"""
Test script to verify text search functionality specifically for tag searches.
"""

from app.storage import StorageManager


def test_tag_search():
    """Test searching for tags"""
    storage = StorageManager()

    # Test searching for "errands" which should be in a tag
    print("\nSearching for 'errands':")
    results = storage.text_search("errands")
    print(f"Found {len(results)} results")
    for entry in results:
        print(f"- {entry.title} (Tags: {entry.tags})")
        print(f"  Created: {entry.created_at}")
        print(
            f"  Content preview: {entry.content[:60]}..."
            if len(entry.content) > 60
            else entry.content
        )

    # Test searching for "savings" which should be in content
    print("\nSearching for 'savings':")
    results = storage.text_search("savings")
    print(f"Found {len(results)} results")
    for entry in results:
        print(f"- {entry.title} (Tags: {entry.tags})")
        print(f"  Created: {entry.created_at}")
        print(
            f"  Content preview: {entry.content[:60]}..."
            if len(entry.content) > 60
            else entry.content
        )


if __name__ == "__main__":
    test_tag_search()
