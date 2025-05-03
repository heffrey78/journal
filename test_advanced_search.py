#!/usr/bin/env python3
"""
Test script for advanced search options in the journal app.

This script tests:
1. Basic text search
2. Semantic search
3. Date range filtering
4. Tag filtering
5. Combined filtering with semantic search

Prerequisites:
- The API server must be running (python main.py)
- Ollama must be installed and running
- Entries must have embeddings generated
(run process_embeddings.py or update_embeddings.py)
"""

import argparse
import datetime
import requests
import sys
from typing import List, Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
DEFAULT_QUERIES = [
    "daily routines",
    "feelings about work",
    "food and cooking",
    "financial planning",
]


def test_api_connection() -> bool:
    """Test the connection to the API server"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except requests.RequestException:
        try:
            # Try docs endpoint as fallback
            response = requests.get(f"{BASE_URL}/docs")
            return response.status_code == 200
        except requests.RequestException:
            return False


def perform_basic_search(query: str) -> Optional[List[Dict[str, Any]]]:
    """Perform a basic text search using the API"""
    try:
        url = f"{BASE_URL}/entries/search/?query={query}"
        print(f"\nPerforming basic text search for: '{query}'")

        response = requests.get(url)
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


def perform_semantic_search(query: str) -> Optional[List[Dict[str, Any]]]:
    """Perform a semantic search using the API"""
    try:
        url = f"{BASE_URL}/entries/search/?query={query}&semantic=true"
        print(f"\nPerforming semantic search for: '{query}'")

        response = requests.get(url)
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
    """Perform an advanced search with filters using the API"""
    try:
        url = f"{BASE_URL}/entries/search/"
        search_params = {"query": query, "semantic": semantic}

        # Add optional parameters
        if date_from:
            search_params["date_from"] = date_from
        if date_to:
            search_params["date_to"] = date_to
        if tags:
            search_params["tags"] = tags

        # Display search info
        search_type = "semantic" if semantic else "text"
        print(f"\nPerforming advanced {search_type} search:")
        print(f"Query: '{query}'")

        if tags:
            print(f"Tags: {', '.join(tags)}")

        if date_from or date_to:
            date_range = []
            if date_from:
                date_range.append(f"from {date_from}")
            if date_to:
                date_range.append(f"to {date_to}")
            print(f"Date range: {' '.join(date_range)}")

        # Send request
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
        print("No results to display.")
        return

    # Limit display to max_results
    display_count = min(len(results), max_results)

    print(f"\nShowing top {display_count} results:")
    for i, entry in enumerate(results[:display_count], 1):
        created_date = datetime.datetime.fromisoformat(entry["created_at"]).strftime(
            "%Y-%m-%d"
        )

        print(f"{i}. {entry['title']} ({created_date})")
        print(f"   Tags: {', '.join(entry.get('tags', []))}")

        # Show a snippet of content
        content = entry.get("content", "")
        if content:
            snippet = content[:100] + "..." if len(content) > 100 else content
            print(f"   {snippet}")

        print()

    if len(results) > display_count:
        print(f"...and {len(results) - display_count} more results.")


def get_available_tags() -> List[str]:
    """Get all available tags from the API"""
    try:
        response = requests.get(f"{BASE_URL}/tags/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


def test_basic_search() -> None:
    """Test basic text search"""
    print("\n" + "=" * 60)
    print("TESTING BASIC TEXT SEARCH")
    print("=" * 60)

    for query in DEFAULT_QUERIES:
        results = perform_basic_search(query)
        if results:
            display_search_results(results)


def test_semantic_search() -> None:
    """Test semantic search"""
    print("\n" + "=" * 60)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 60)

    for query in DEFAULT_QUERIES:
        results = perform_semantic_search(query)
        if results:
            display_search_results(results)


def test_date_filtering() -> None:
    """Test search with date filtering"""
    print("\n" + "=" * 60)
    print("TESTING DATE FILTERING")
    print("=" * 60)

    # Get current date and yesterday's date
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Test with date ranges
    test_cases = [
        # Recent entries (past day)
        {
            "name": "Recent entries (past day)",
            "date_from": yesterday.isoformat(),
            "date_to": today.isoformat(),
        },
        # Older entries
        {
            "name": "Entries from beginning of month",
            "date_from": f"{today.year}-{today.month:02d}-01",
            "date_to": f"{today.year}-{today.month:02d}-15",
        },
    ]

    for test_case in test_cases:
        print(f"\nTest case: {test_case['name']}")
        results = perform_advanced_search(
            query="",  # Empty query to focus on date filtering
            date_from=test_case["date_from"],
            date_to=test_case["date_to"],
        )
        if results:
            display_search_results(results)


def test_tag_filtering() -> None:
    """Test search with tag filtering"""
    print("\n" + "=" * 60)
    print("TESTING TAG FILTERING")
    print("=" * 60)

    # Get available tags
    tags = get_available_tags()
    if not tags:
        print("No tags available for testing.")
        return

    # Test with first tag
    print(f"\nSearching entries with tag: {tags[0]}")
    results = perform_advanced_search(
        query="", tags=[tags[0]]  # Empty query to focus on tag filtering
    )
    if results:
        display_search_results(results)

    # Test with multiple tags if available
    if len(tags) >= 2:
        print(f"\nSearching entries with tags: {tags[0]} OR {tags[1]}")
        results = perform_advanced_search(
            query="", tags=tags[:2]  # Empty query to focus on tag filtering
        )
        if results:
            display_search_results(results)


def test_combined_filtering() -> None:
    """Test search with combined filtering options"""
    print("\n" + "=" * 60)
    print("TESTING COMBINED FILTERING")
    print("=" * 60)

    # Get tags
    tags = get_available_tags()
    if not tags:
        print("No tags available for testing combined filtering.")
        return

    # Get date range (past week)
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    # Test with query + semantic + tag + date
    query = DEFAULT_QUERIES[0]
    print("\nAdvanced search with all filters:")
    print(f"- Query: '{query}'")
    print("- Using semantic search")
    print(f"- Tag: {tags[0]}")
    print(f"- Date range: {week_ago.isoformat()} to {today.isoformat()}")

    results = perform_advanced_search(
        query=query,
        semantic=True,
        tags=[tags[0]],
        date_from=week_ago.isoformat(),
        date_to=today.isoformat(),
    )
    if results:
        display_search_results(results)


def main() -> int:
    """Main function"""
    parser = argparse.ArgumentParser(description="Test advanced search options")
    parser.add_argument(
        "--tests",
        choices=["basic", "semantic", "date", "tag", "combined", "all"],
        default="all",
        help="Specific test(s) to run",
    )

    args = parser.parse_args()

    print("Advanced Search Testing")
    print("======================")

    # Check API connection
    if not test_api_connection():
        print(
            "Failed to connect to the API. " "Please make sure the server is running."
        )
        return 1

    # Run specified tests
    if args.tests in ["basic", "all"]:
        test_basic_search()

    if args.tests in ["semantic", "all"]:
        test_semantic_search()

    if args.tests in ["date", "all"]:
        test_date_filtering()

    if args.tests in ["tag", "all"]:
        test_tag_filtering()

    if args.tests in ["combined", "all"]:
        test_combined_filtering()

    return 0


if __name__ == "__main__":
    sys.exit(main())
