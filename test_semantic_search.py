#!/usr/bin/env python3
"""
Test script for semantic search functionality.

This script demonstrates how to use the semantic search feature
of the journal application through the REST API.

Prerequisites:
- The API server must be running (python main.py)
- Ollama must be installed and running
"""

import json
import requests
import sys
import time
from typing import List, Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
DEFAULT_QUERIES = [
    "nature and outdoors",
    "technology and programming",
    "cooking recipes",
    "personal reflections",
]


def test_api_connection() -> bool:
    """Test the connection to the API server"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            api_info = response.json()
            print(f"Connected to {api_info['name']} v{api_info['version']}")
            print(f"Description: {api_info['description']}")
            return True
        else:
            print(f"Error connecting to API: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return False


def perform_simple_search(
    query: str, semantic: bool = False
) -> Optional[List[Dict[str, Any]]]:
    """Perform a simple search using the API"""
    try:
        url = f"{BASE_URL}/entries/search/"
        params = {"query": query, "semantic": semantic}

        print(
            f"\nPerforming {'semantic' if semantic else 'text'} search for: '{query}'"
        )

        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results")
            return results
        else:
            print(f"Search failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return None


def perform_advanced_search(
    query: str,
    semantic: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Perform an advanced search using the API"""
    try:
        url = f"{BASE_URL}/entries/search/"
        search_params = {"query": query, "semantic": semantic}

        if date_from:
            search_params["date_from"] = date_from
        if date_to:
            search_params["date_to"] = date_to
        if tags:
            search_params["tags"] = tags

        print(f"\nPerforming advanced {'semantic' if semantic else 'text'} search:")
        print(f"Query: '{query}'")
        if tags:
            print(f"Tags: {', '.join(tags)}")
        if date_from or date_to:
            date_range = f"From: {date_from if date_from else 'beginning'}"
            date_range += f" To: {date_to if date_to else 'present'}"
            print(f"Date range: {date_range}")

        response = requests.post(url, json=search_params)
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results")
            return results
        else:
            print(f"Search failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return None


def display_search_results(results: List[Dict[str, Any]], max_results: int = 3) -> None:
    """Display search results in a readable format"""
    if not results:
        print("No results to display")
        return

    for i, entry in enumerate(results[:max_results]):
        print(f"\nResult {i+1}:")
        print(f"  Title: {entry['title']}")
        print(f"  ID: {entry['id']}")
        if "tags" in entry and entry["tags"]:
            print(f"  Tags: {', '.join(entry['tags'])}")

        content = entry.get("content", "")
        if content:
            # Show a preview of the content
            preview = content.split("\n")[0][:100]  # First line, max 100 chars
            print(f"  Content preview: {preview}...")

    if len(results) > max_results:
        print(f"\n...and {len(results) - max_results} more results")


def compare_search_methods(query: str) -> None:
    """Compare text search and semantic search results for the same query"""
    print("\n" + "=" * 60)
    print(f"COMPARING SEARCH METHODS FOR: '{query}'")
    print("=" * 60)

    # Text search
    text_results = perform_simple_search(query, semantic=False)
    if text_results:
        print("\nTEXT SEARCH RESULTS:")
        display_search_results(text_results)

    # Small delay to prevent overwhelming the API
    time.sleep(0.5)

    # Semantic search
    semantic_results = perform_simple_search(query, semantic=True)
    if semantic_results:
        print("\nSEMANTIC SEARCH RESULTS:")
        display_search_results(semantic_results)

    print("\nOBSERVATIONS:")
    if not text_results and not semantic_results:
        print("  Both search methods returned no results.")
    elif not text_results:
        print("  Text search found no results, but semantic search did.")
    elif not semantic_results:
        print("  Semantic search found no results, but text search did.")
    else:
        text_ids = [e["id"] for e in text_results]
        semantic_ids = [e["id"] for e in semantic_results]

        # Find common and unique results
        common = set(text_ids).intersection(set(semantic_ids))
        text_only = set(text_ids) - set(semantic_ids)
        semantic_only = set(semantic_ids) - set(text_ids)

        print(f"  Common results: {len(common)}")
        print(f"  Text search only: {len(text_only)}")
        print(f"  Semantic search only: {len(semantic_only)}")


def get_available_tags() -> List[str]:
    """Get all available tags from the API"""
    try:
        response = requests.get(f"{BASE_URL}/tags/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []


def main() -> int:
    """Main function"""
    print("Semantic Search Test Script")
    print("==========================")

    # Check API connection
    if not test_api_connection():
        print("Failed to connect to the API. Please make sure the server is running.")
        return 1

    # Get command line arguments or use defaults
    queries = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_QUERIES

    for query in queries:
        compare_search_methods(query)

    # Test advanced search with tags if available
    tags = get_available_tags()
    if tags and len(tags) > 0:
        print("\n" + "=" * 60)
        print("TESTING ADVANCED SEARCH WITH TAGS")
        print("=" * 60)

        # Pick the first tag for testing
        tag = tags[0]
        results = perform_advanced_search(
            query="",  # Empty query to prioritize tag filtering
            semantic=True,  # Use semantic search
            tags=[tag],
        )

        if results:
            print(f"\nEntries with tag '{tag}' (semantic search):")
            display_search_results(results)

    print("\nTest completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
