#!/usr/bin/env python3
"""
Simple CLI for creating and viewing journal entries.
"""

import argparse
import sys
from typing import List

from app.models import JournalEntry
from app.storage import StorageManager


def create_entry(
    storage: StorageManager, title: str, content: str, tags: List[str]
) -> str:
    """Create a new journal entry and save it."""
    entry = JournalEntry(title=title, content=content, tags=tags)
    entry_id = storage.save_entry(entry)
    print(f"Entry created with ID: {entry_id}")
    return entry_id


def view_entry(storage: StorageManager, entry_id: str) -> None:
    """View a journal entry by its ID."""
    entry = storage.get_entry(entry_id)
    if not entry:
        print(f"No entry found with ID: {entry_id}")
        return

    print(f"\n--- {entry.title} ---")
    print(f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if entry.updated_at and entry.updated_at != entry.created_at:
        print(f"Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if entry.tags:
        print(f"Tags: {', '.join(entry.tags)}")
    print("\n" + entry.content)


def list_entries(storage: StorageManager, limit: int = 10) -> None:
    """List recent journal entries."""
    entries = storage.get_entries(limit=limit)
    if not entries:
        print("No journal entries found.")
        return

    print(f"\nRecent Entries ({len(entries)}):")
    print("-" * 40)

    for entry in entries:
        created_date = entry.created_at.strftime("%Y-%m-%d %H:%M")
        tags_display = f" [{', '.join(entry.tags)}]" if entry.tags else ""
        print(f"{entry.id}: {entry.title} ({created_date}){tags_display}")


def search_entries(storage: StorageManager, query: str) -> None:
    """Search journal entries for a query."""
    entries = storage.text_search(query)
    if not entries:
        print(f"No entries found matching '{query}'")
        return

    print(f"\nSearch Results for '{query}' ({len(entries)} entries):")
    print("-" * 40)

    for entry in entries:
        created_date = entry.created_at.strftime("%Y-%m-%d %H:%M")
        tags_display = f" [{', '.join(entry.tags)}]" if entry.tags else ""
        print(f"{entry.id}: {entry.title} ({created_date}){tags_display}")


def delete_entry(storage: StorageManager, entry_id: str) -> None:
    """Delete a journal entry by its ID."""
    if storage.delete_entry(entry_id):
        print(f"Entry {entry_id} deleted successfully.")
    else:
        print(f"Failed to delete entry {entry_id}. Entry may not exist.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Journal CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create entry command
    create_parser = subparsers.add_parser("create", help="Create a new journal entry")
    create_parser.add_argument("title", help="Title of the journal entry")
    create_parser.add_argument(
        "--content",
        "-c",
        help="Content of the journal entry (or use stdin if not provided)",
    )
    create_parser.add_argument(
        "--tags", "-t", help="Comma-separated list of tags", default=""
    )

    # View entry command
    view_parser = subparsers.add_parser("view", help="View a journal entry")
    view_parser.add_argument("id", help="ID of the entry to view")

    # List entries command
    list_parser = subparsers.add_parser("list", help="List recent journal entries")
    list_parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum number of entries to list"
    )

    # Search entries command
    search_parser = subparsers.add_parser("search", help="Search journal entries")
    search_parser.add_argument("query", help="Search query")

    # Delete entry command
    delete_parser = subparsers.add_parser("delete", help="Delete a journal entry")
    delete_parser.add_argument("id", help="ID of the entry to delete")

    args = parser.parse_args()
    storage = StorageManager()

    if args.command == "create":
        content = args.content
        if not content:
            print("Enter journal content (press Ctrl+D when finished):")
            content = sys.stdin.read().strip()

        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        create_entry(storage, args.title, content, tags)

    elif args.command == "view":
        view_entry(storage, args.id)

    elif args.command == "list":
        list_entries(storage, args.limit)

    elif args.command == "search":
        search_entries(storage, args.query)

    elif args.command == "delete":
        delete_entry(storage, args.id)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
