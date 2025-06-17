#!/usr/bin/env python3
"""
Advanced CLI for journal management with full feature parity to the web API.
"""

import argparse
import sys
import datetime
import os
import glob
import re
from typing import List, Dict, Any, Optional

from app.models import JournalEntry
from app.storage import StorageManager
from app.llm_service import LLMService
from app.import_service import ImportService


def create_entry(
    storage: StorageManager,
    title: str,
    content: str,
    tags: List[str],
    favorite: bool = False,
) -> str:
    """Create a new journal entry and save it."""
    entry = JournalEntry(title=title, content=content, tags=tags, favorite=favorite)
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
    if entry.favorite:
        print("★ Favorited")
    if entry.images:
        print(f"Images: {', '.join(entry.images)}")
    print("\n" + entry.content)


def list_entries(
    storage: StorageManager, limit: int = 10, favorite_only: bool = False
) -> None:
    """List recent journal entries."""
    # Remove the favorite parameter since it's not supported in get_entries
    entries = storage.get_entries(limit=limit)
    if not entries:
        print("No journal entries found.")
        return

    filter_text = "favorited " if favorite_only else ""
    print(f"\nRecent {filter_text}Entries ({len(entries)}):")
    print("-" * 60)

    for entry in entries:
        created_date = entry.created_at.strftime("%Y-%m-%d %H:%M")
        tags_display = f" [{', '.join(entry.tags)}]" if entry.tags else ""
        # Remove reference to favorite since it doesn't exist in the JournalEntry model
        print(f"{entry.id}: {entry.title} ({created_date}){tags_display}")


def search_entries(
    storage: StorageManager,
    query: str,
    tags: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    favorite: bool = None,
    semantic: bool = False,
) -> None:
    """Search journal entries with advanced filters."""
    # Convert string dates to datetime objects if provided
    date_from = None
    if start_date:
        try:
            date_from = datetime.datetime.fromisoformat(start_date)
        except ValueError:
            print(
                f"Invalid start date format: {start_date}. Use ISO format (YYYY-MM-DD)."
            )
            return

    date_to = None
    if end_date:
        try:
            date_to = datetime.datetime.fromisoformat(end_date)
        except ValueError:
            print(f"Invalid end date format: {end_date}. Use ISO format (YYYY-MM-DD).")
            return

    # Call the appropriate search function based on parameters
    if any([tags, date_from, date_to, favorite is not None, semantic]):
        entries = storage.advanced_search(
            query=query,
            tags=tags,
            date_from=date_from,
            date_to=date_to,
            favorite=favorite,
            semantic=semantic,
        )
    else:
        # Simple text search if no advanced filters
        entries = storage.text_search(query, use_semantic=semantic)

    if not entries:
        print("No entries found matching the search criteria")
        return

    print(f"\nSearch Results ({len(entries)} entries):")
    print("-" * 60)

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


def update_entry(
    storage: StorageManager,
    entry_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> None:
    """Update an existing journal entry."""
    entry = storage.get_entry(entry_id)
    if not entry:
        print(f"No entry found with ID: {entry_id}")
        return

    # Only update fields that were provided
    if title is not None:
        entry.title = title

    if content is not None:
        entry.content = content

    if tags is not None:
        entry.tags = tags

    if storage.save_entry(entry, update=True):
        print(f"Entry {entry_id} updated successfully.")
    else:
        print(f"Failed to update entry {entry_id}.")


def toggle_favorite(storage: StorageManager, entry_id: str, favorite: bool) -> None:
    """Toggle the favorite status of an entry."""
    entry = storage.get_entry(entry_id)
    if not entry:
        print(f"No entry found with ID: {entry_id}")
        return

    entry.favorite = favorite
    if storage.save_entry(entry, update=True):
        status = "favorited" if favorite else "unfavorited"
        print(f"Entry {entry_id} {status} successfully.")
    else:
        print(f"Failed to update favorite status for entry {entry_id}.")


def bulk_import(
    storage: StorageManager,
    directory: str,
    pattern: str = "*.md",
    tags: Optional[List[str]] = None,
    folder: Optional[str] = None,
    custom_title: Optional[str] = None,
) -> None:
    """Bulk import multiple files from a directory."""
    import_service = ImportService(storage)

    # Expand the directory path
    directory = os.path.expanduser(directory)

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    # Build the full pattern path
    search_pattern = os.path.join(directory, pattern)
    files = glob.glob(search_pattern)

    if not files:
        print(f"No files found matching pattern '{pattern}' in '{directory}'")
        return

    # Sort files for consistent processing
    files.sort()

    print(f"Found {len(files)} files to import...")
    print("-" * 60)

    successful_imports = 0
    failed_imports = 0

    for file_path in files:
        try:
            # Read file content
            with open(file_path, "rb") as f:
                file_data = f.read()

            filename = os.path.basename(file_path)
            print(f"Processing: {filename}")

            # Try to extract date from filename (format: YYYY_MM_DD.md)
            file_date = None
            date_match = re.search(r"(\d{4})_(\d{2})_(\d{2})", filename)
            if date_match:
                year, month, day = date_match.groups()
                try:
                    file_date = datetime.datetime(int(year), int(month), int(day))
                except ValueError:
                    pass  # Invalid date, keep as None

            # Handle "None" string
            if folder == "None":
                folder = None

            # Process the file
            success, entry_id, error = import_service.process_file(
                file_data=file_data,
                filename=filename,
                tags=tags or [],
                folder=folder,
                file_date=file_date,
                custom_title=custom_title,
                is_multi_file_import=True,
            )

            if success:
                successful_imports += 1
                print(f"  ✓ Successfully imported as entry: {entry_id}")
            else:
                failed_imports += 1
                print(f"  ✗ Failed to import: {error}")

        except Exception as e:
            failed_imports += 1
            print(f"  ✗ Error processing {filename}: {str(e)}")

    print("-" * 60)
    print(f"Import completed: {successful_imports} successful, {failed_imports} failed")


def summarize_entry(
    storage: StorageManager,
    llm_service: LLMService,
    entry_id: str,
    prompt_type: str = "default",
) -> None:
    """Generate a summary/analysis for an entry using the LLM service."""
    entry = storage.get_entry(entry_id)
    if not entry:
        print(f"No entry found with ID: {entry_id}")
        return

    print(
        f"Generating summary for entry '{entry.title}' "
        f"using prompt type '{prompt_type}'..."
    )
    try:
        summary = llm_service.summarize_entry(entry, prompt_type=prompt_type)

        print("\n--- Summary ---")
        print(f"Summary: {summary.get('summary', 'Not available')}")
        print(f"Key Topics: {', '.join(summary.get('key_topics', ['None']))}")
        print(f"Mood: {summary.get('mood', 'Not analyzed')}")

        # Ask if user wants to save this as a favorite summary
        save_choice = (
            input("\nSave this summary as a favorite? (y/n): ").strip().lower()
        )
        if save_choice == "y":
            storage.save_favorite_summary(entry_id, summary)
            print("Summary saved as favorite.")

    except Exception as e:
        print(f"Error generating summary: {str(e)}")


def list_favorite_summaries(storage: StorageManager, entry_id: str) -> None:
    """List favorite summaries for an entry."""
    entry = storage.get_entry(entry_id)
    if not entry:
        print(f"No entry found with ID: {entry_id}")
        return

    summaries = storage.get_favorite_summaries(entry_id)
    if not summaries:
        print(f"No favorite summaries for entry '{entry.title}'")
        return

    print(f"\nFavorite Summaries for '{entry.title}':")
    print("-" * 60)

    for i, summary in enumerate(summaries, 1):
        created_at = summary.get("created_at", "Unknown date")
        prompt_type = summary.get("prompt_type", "default")
        print(f"{i}. Created: {created_at}, Type: {prompt_type}")
        print(f"   Summary: {summary.get('summary', 'Not available')}")
        print(f"   Key Topics: {', '.join(summary.get('key_topics', ['None']))}")
        print(f"   Mood: {summary.get('mood', 'Not analyzed')}")
        print("")


def list_tags(storage: StorageManager) -> None:
    """List all available tags."""
    tags = storage.get_all_tags()
    if not tags:
        print("No tags found.")
        return

    print("\nAvailable Tags:")
    print("-" * 40)

    # Count occurrences of each tag
    tag_counts = {}
    for tag in tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort tags by count (most used first)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    for tag, count in sorted_tags:
        print(f"{tag} ({count})")


def get_llm_config(llm_service: LLMService) -> None:
    """Get and display the current LLM configuration."""
    try:
        config = llm_service.get_config()
        print("\nCurrent LLM Configuration:")
        print("-" * 40)
        print(f"Model: {config.get('model', 'Not configured')}")
        print(f"Base URL: {config.get('base_url', 'Default')}")
        print(f"API Key: {'Configured' if config.get('api_key') else 'Not configured'}")
        print(f"Enabled: {'Yes' if config.get('enabled', False) else 'No'}")
        print(f"Temperature: {config.get('temperature', 0.7)}")
    except Exception as e:
        print(f"Error fetching LLM configuration: {str(e)}")


def update_llm_config(llm_service: LLMService, config_updates: Dict[str, Any]) -> None:
    """Update the LLM configuration."""
    try:
        current_config = llm_service.get_config()
        # Merge updates with current config
        updated_config = {**current_config, **config_updates}
        llm_service.update_config(updated_config)
        print("LLM configuration updated successfully.")
        # Display the new configuration
        get_llm_config(llm_service)
    except Exception as e:
        print(f"Error updating LLM configuration: {str(e)}")


def test_llm_connection(llm_service: LLMService) -> None:
    """Test the LLM connection."""
    print("Testing LLM connection...")
    try:
        result = llm_service.test_connection()
        print(f"Status: {result.get('status', 'Unknown')}")
        print(f"Message: {result.get('message', 'No message')}")
    except Exception as e:
        print(f"Connection test failed: {str(e)}")


def list_available_models(llm_service: LLMService) -> None:
    """List available LLM models."""
    try:
        models = llm_service.get_available_models()
        print("\nAvailable LLM Models:")
        print("-" * 40)
        for model in models:
            print(model)
    except Exception as e:
        print(f"Error fetching available models: {str(e)}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Advanced Journal CLI")
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
    create_parser.add_argument(
        "--favorite", "-f", action="store_true", help="Mark as favorite"
    )

    # View entry command
    view_parser = subparsers.add_parser("view", help="View a journal entry")
    view_parser.add_argument("id", help="ID of the entry to view")

    # List entries command
    list_parser = subparsers.add_parser("list", help="List recent journal entries")
    list_parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum number of entries to list"
    )
    list_parser.add_argument(
        "--favorite", "-f", action="store_true", help="Show only favorite entries"
    )

    # Search entries command
    search_parser = subparsers.add_parser(
        "search", help="Search journal entries with advanced filters"
    )
    search_parser.add_argument("query", help="Search query", nargs="?", default="")
    search_parser.add_argument(
        "--tags", "-t", help="Comma-separated list of tags to filter by", default=""
    )
    search_parser.add_argument(
        "--start-date", "-s", help="Filter entries after this date (YYYY-MM-DD)"
    )
    search_parser.add_argument(
        "--end-date", "-e", help="Filter entries before this date (YYYY-MM-DD)"
    )
    search_parser.add_argument(
        "--favorite", "-f", action="store_true", help="Show only favorite entries"
    )
    search_parser.add_argument(
        "--semantic", action="store_true", help="Use semantic search"
    )

    # Delete entry command
    delete_parser = subparsers.add_parser("delete", help="Delete a journal entry")
    delete_parser.add_argument("id", help="ID of the entry to delete")

    # Update entry command
    update_parser = subparsers.add_parser(
        "update", help="Update an existing journal entry"
    )
    update_parser.add_argument("id", help="ID of the entry to update")
    update_parser.add_argument("--title", help="New title for the entry")
    update_parser.add_argument(
        "--content",
        "-c",
        help="New content for the entry (or use stdin if just -c is provided)",
    )
    update_parser.add_argument("--tags", "-t", help="New comma-separated list of tags")

    # Favorite command
    favorite_parser = subparsers.add_parser(
        "favorite", help="Toggle favorite status for an entry"
    )
    favorite_parser.add_argument("id", help="ID of the entry")
    favorite_parser.add_argument(
        "--status",
        "-s",
        choices=["on", "off"],
        required=True,
        help="Set favorite status to on or off",
    )

    # Tags command
    _ = subparsers.add_parser("tags", help="List all available tags")

    # Import command
    import_parser = subparsers.add_parser(
        "import", help="Bulk import files from a directory"
    )
    import_parser.add_argument("directory", help="Directory containing files to import")
    import_parser.add_argument(
        "--pattern", "-p", default="*.md", help="File pattern to match (default: *.md)"
    )
    import_parser.add_argument(
        "--tags",
        "-t",
        help="Comma-separated list of tags to apply to all entries",
        default="",
    )
    import_parser.add_argument(
        "--folder", "-f", help="Folder path to organize entries into"
    )
    import_parser.add_argument(
        "--title", help="Custom title prefix for imported entries"
    )

    # Summarize command
    summarize_parser = subparsers.add_parser(
        "summarize", help="Generate a summary/analysis for an entry"
    )
    summarize_parser.add_argument("id", help="ID of the entry to summarize")
    summarize_parser.add_argument(
        "--prompt", "-p", default="default", help="Type of summary prompt to use"
    )

    # List summaries command
    list_summaries_parser = subparsers.add_parser(
        "summaries", help="List favorite summaries for an entry"
    )
    list_summaries_parser.add_argument("id", help="ID of the entry")

    # LLM Config command group
    llm_parser = subparsers.add_parser(
        "llm", help="LLM service configuration and operations"
    )
    llm_subparsers = llm_parser.add_subparsers(dest="llm_command")

    # Update LLM config
    llm_update_parser = llm_subparsers.add_parser(
        "update", help="Update LLM configuration"
    )
    llm_update_parser.add_argument("--model", help="LLM model to use")
    llm_update_parser.add_argument("--base-url", help="Base URL for the LLM service")
    llm_update_parser.add_argument("--api-key", help="API key for the LLM service")
    llm_update_parser.add_argument(
        "--enabled", type=bool, help="Enable or disable LLM features"
    )
    llm_update_parser.add_argument(
        "--temperature", type=float, help="Temperature for LLM requests"
    )

    args = parser.parse_args()
    storage = StorageManager()
    llm_service = LLMService()

    if args.command == "create":
        content = args.content
        if content is None:
            print("Enter journal content (press Ctrl+D when finished):")
            content = sys.stdin.read().strip()

        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        create_entry(storage, args.title, content, tags, favorite=args.favorite)

    elif args.command == "view":
        view_entry(storage, args.id)

    elif args.command == "list":
        list_entries(storage, args.limit, favorite_only=args.favorite)

    elif args.command == "search":
        tags = (
            [tag.strip() for tag in args.tags.split(",") if tag.strip()]
            if args.tags
            else None
        )
        search_entries(
            storage,
            args.query,
            tags=tags,
            start_date=args.start_date,
            end_date=args.end_date,
            favorite=args.favorite if hasattr(args, "favorite") else None,
            semantic=args.semantic if hasattr(args, "semantic") else False,
        )

    elif args.command == "delete":
        delete_entry(storage, args.id)

    elif args.command == "update":
        content = None
        if hasattr(args, "content"):
            if args.content is None and "-c" in sys.argv:
                print("Enter new journal content (press Ctrl+D when finished):")
                content = sys.stdin.read().strip()
            else:
                content = args.content

        tags = None
        if args.tags is not None:
            tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

        update_entry(storage, args.id, title=args.title, content=content, tags=tags)

    elif args.command == "favorite":
        toggle_favorite(storage, args.id, favorite=(args.status == "on"))

    elif args.command == "tags":
        list_tags(storage)

    elif args.command == "import":
        tags = (
            [tag.strip() for tag in args.tags.split(",") if tag.strip()]
            if args.tags
            else None
        )
        bulk_import(
            storage,
            args.directory,
            pattern=args.pattern,
            tags=tags,
            folder=args.folder,
            custom_title=args.title,
        )

    elif args.command == "summarize":
        summarize_entry(storage, llm_service, args.id, prompt_type=args.prompt)

    elif args.command == "summaries":
        list_favorite_summaries(storage, args.id)

    elif args.command == "llm":
        if args.llm_command == "get":
            get_llm_config(llm_service)

        elif args.llm_command == "update":
            # Build a dict of only the provided config updates
            updates = {}
            if args.model is not None:
                updates["model"] = args.model
            if args.base_url is not None:
                updates["base_url"] = args.base_url
            if args.api_key is not None:
                updates["api_key"] = args.api_key
            if args.enabled is not None:
                updates["enabled"] = args.enabled
            if args.temperature is not None:
                updates["temperature"] = args.temperature

            update_llm_config(llm_service, updates)

        elif args.llm_command == "test":
            test_llm_connection(llm_service)

        elif args.llm_command == "models":
            list_available_models(llm_service)

        else:
            llm_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
