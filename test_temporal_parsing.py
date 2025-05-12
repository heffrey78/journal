#!/usr/bin/env python3
"""
Test script for temporal query parsing.

This script tests the TemporalParser's ability to identify date-related expressions
in natural language and convert them to appropriate date filters.

Sample usage:
    python test_temporal_parsing.py
"""

import sys
from datetime import datetime
from app.temporal_parser import TemporalParser


def format_date_filter(date_filter):
    """Format date filter for display."""
    if not date_filter:
        return "No date filter detected"

    result = []
    if "date_from" in date_filter:
        date_from = date_filter["date_from"]
        result.append(f"From: {date_from.strftime('%Y-%m-%d %H:%M:%S')}")

    if "date_to" in date_filter:
        date_to = date_filter["date_to"]
        result.append(f"To:   {date_to.strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(result)


def main():
    """Run tests for temporal query parsing."""
    parser = TemporalParser()

    # Sample queries to test
    test_queries = [
        # Basic tests
        "What did I write yesterday?",
        "Show me entries from today",
        "Find journal entries from last week",
        "Get entries from May 2024",
        "Entries between January and March",
        "Show me what I wrote 3 days ago",
        "What did I write about last summer?",
        "Entries from the past month",
        "Find notes from this year",
        "What did I write in 2024?",
        # Complex tests
        "Show me entries about work from last week",
        "Find any journal entries from April 15 that mention meetings",
        "What did I write about programming between March and April?",
        "Entries from May 5, 2025 about the project deadline",
        "Show me notes from before May 10",
        "Entries after January 15 that mention exercise",
        "Did I write anything about cooking in the past month?",
        "Show me entries from spring 2025",
        # Non-temporal queries
        "What's the weather like?",
        "Tell me about my exercise routine",
        "How many entries do I have?",
        "What topics do I write about most?",
    ]

    print("===== Temporal Query Parser Test =====\n")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}\n")

    for i, query in enumerate(test_queries, 1):
        print(f'Query {i}: "{query}"')
        result = parser.parse_temporal_query(query)
        print(f"Result: {format_date_filter(result)}")
        print("-" * 50)

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("\n===== Interactive Mode =====")
        print("Type a query to test temporal parsing (or 'exit' to quit):")

        while True:
            try:
                query = input("\nQuery: ")
                if query.lower() in ("exit", "quit"):
                    break

                result = parser.parse_temporal_query(query)
                print(f"Result: {format_date_filter(result)}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
