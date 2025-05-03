#!/usr/bin/env python3
import requests
import argparse
import datetime
from typing import List, Optional, Dict, Any


BASE_URL = "http://localhost:8000"


def search_entries(
    query: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
    advanced: bool = False,
):
    """
    Search for journal entries using either simple or advanced search.

    Args:
        query: Text to search for
        date_from: Optional start date filter (format: YYYY-MM-DD)
        date_to: Optional end date filter (format: YYYY-MM-DD)
        tags: Optional list of tags to filter by
        advanced: Whether to use the advanced search endpoint
    """
    print(f"\n--- Searching for: '{query}' " f"{'(advanced)' if advanced else ''} ---")

    try:
        if advanced:
            # Use POST advanced search endpoint
            search_params: Dict[str, Any] = {"query": query}
            if date_from:
                search_params["date_from"] = f"{date_from}T00:00:00"
            if date_to:
                search_params["date_to"] = f"{date_to}T23:59:59"
            if tags:
                search_params["tags"] = tags

            response = requests.post(f"{BASE_URL}/entries/search/", json=search_params)
        else:
            # Use GET simple search endpoint
            response = requests.get(f"{BASE_URL}/entries/search/?query={query}")

        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results for '{query}'")

            for idx, entry in enumerate(results, 1):
                created_date = datetime.datetime.fromisoformat(
                    entry["created_at"]
                ).strftime("%Y-%m-%d")

                print(
                    f"{idx}. {entry['title']} ({created_date}) - " f"ID: {entry['id']}"
                )
                print(f"   Tags: {', '.join(entry['tags'])}")

                # Show a snippet of content
                if len(entry["content"]) > 100:
                    content_snippet = entry["content"][:100] + "..."
                else:
                    content_snippet = entry["content"]
                print(f"   {content_snippet}")
                print()

            if len(results) == 0:
                print("No entries found matching your search criteria.")
        else:
            print(f"Search failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error searching: {e}")


def main():
    parser = argparse.ArgumentParser(description="Search journal entries")
    parser.add_argument("query", help="Text to search for")
    parser.add_argument("--from", dest="date_from", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD)")
    parser.add_argument("--tags", nargs="+", help="Tags to filter by")
    parser.add_argument("--advanced", action="store_true", help="Use advanced search")

    args = parser.parse_args()

    # Basic search
    search_entries(args.query)

    # Advanced search if requested
    if args.advanced or args.date_from or args.date_to or args.tags:
        search_entries(
            args.query,
            date_from=args.date_from,
            date_to=args.date_to,
            tags=args.tags,
            advanced=True,
        )


if __name__ == "__main__":
    main()
