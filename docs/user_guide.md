# Journal App User Guide

This guide provides detailed instructions on how to use the Journal App, a personal journaling application with powerful search capabilities and AI-assisted features.

## Table of Contents
- [Getting Started](#getting-started)
- [Working with Journal Entries](#working-with-journal-entries)
- [Markdown Features](#markdown-features)
- [Search Capabilities](#search-capabilities)
- [Using Tags](#using-tags)
- [AI Features](#ai-features)
- [Command Line Interface](#command-line-interface)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Ensure you have Python 3.8 or higher installed on your system
2. Clone the repository
3. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Make sure Ollama is installed and running (required for semantic search and AI features)
6. Initialize the database:
   ```
   python -c "from app.storage import StorageManager; StorageManager().initialize_db()"
   ```

### Starting the Application

1. Launch the application server:
   ```
   python main.py
   ```
   Or directly with uvicorn:
   ```
   uvicorn main:app --reload
   ```

2. Open your web browser and navigate to `http://localhost:8000`

## Working with Journal Entries

### Creating a New Entry

#### Using the Web Interface
1. Open the Journal App in your browser
2. Click the "New Entry" button in the navigation menu
3. Enter a title for your journal entry
4. Write your content in the text area (Markdown is supported)
5. Add tags in the "Tags" field, separating multiple tags with commas
6. Click "Save" to create your entry

#### Using the Command Line
```
python cli.py add "My Journal Title" "Content of my journal entry" --tags "tag1,tag2"
```

### Editing an Entry

1. View the entry you want to edit
2. Click the "Edit" button
3. Make your changes to the title, content or tags
4. Click "Save" to update your entry

### Deleting an Entry

1. View the entry you want to delete
2. Click the "Delete" button
3. Confirm the deletion when prompted

## Markdown Features

Journal App supports rich text formatting with enhanced Markdown support. You can use these features to create well-structured, visually appealing journal entries.

### Basic Formatting

```markdown
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*
~~Strikethrough~~

> This is a blockquote
```

### Lists

```markdown
* Unordered list item
* Another item
  * Nested item

1. Ordered list item
2. Another ordered item
```

### Links and Images

```markdown
[Link text](https://example.com)

![Image alt text](path/to/image.jpg)
```

### Code Blocks with Syntax Highlighting

````markdown
```javascript
function sayHello() {
  console.log("Hello, world!");
}
```
````

### Tables

You can create tables using the following syntax:

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

This will render as:

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

### Task Lists

```markdown
- [x] Completed task
- [ ] Incomplete task
- [ ] Another task
```

### Horizontal Rule

```markdown
---
```

## Search Capabilities

The Journal App offers powerful search capabilities, including both traditional text search and semantic search.

### Basic Text Search

Basic text search looks for exact matches of your search term in entry titles, content, and tags.

1. Click the "Search" button in the navigation menu
2. Enter your search term in the text field
3. Ensure the "Use semantic search" option is unchecked
4. Click "Search" to view results

### Semantic Search

Semantic search understands the meaning behind your query and finds conceptually related entries, even if they don't contain the exact words you searched for.

1. Click the "Search" button in the navigation menu
2. Enter your search term in the text field
3. Check the "Use semantic search" option
4. Click "Search" to view results

> **Note**: For semantic search to work, you need to first generate embeddings for your entries. After creating new entries, run:
> ```
> python process_embeddings.py
> ```

### Advanced Search Options

You can refine your search using various filters:

1. Click "Show advanced options" on the search page
2. Apply any of these filters:
   - Date Range: Filter entries by date
   - Tags: Filter entries by specific tags
3. Click "Search" to apply filters

## Using Tags

Tags help you categorize and find related entries.

### Adding Tags When Creating Entries

1. When creating a new entry, enter tags in the Tags field
2. Separate multiple tags with commas
3. Example: `work, ideas, follow-up`

### Browsing Entries by Tag

1. Click on any tag displayed on an entry to see all entries with that tag
2. Or click "Tags" in the navigation menu to browse all available tags

### Managing Tags

1. To add tags to an existing entry, edit the entry and add new tags
2. To remove a tag, edit the entry and delete the tag

## AI Features

The Journal App includes AI-powered features to help you gain insights from your journal entries.

### Entry Summarization

1. View any journal entry
2. Click the "Summarize" button
3. The system will analyze your entry and provide:
   - A brief summary
   - Key topics identified in the entry
   - The overall mood or sentiment detected

### Semantic Search Insights

When using semantic search, the results include relevance information:
1. Matches will be ranked by conceptual similarity
2. The relevant parts of each entry that match your search will be highlighted

## Command Line Interface

The Journal App includes a CLI for quick access to common functions.

### Available Commands

```
# Add a new entry
python cli.py add "Title" "Content" --tags "tag1,tag2"

# List recent entries
python cli.py list [--limit N]

# Show a specific entry
python cli.py show <entry_id>

# Search for entries
python cli.py search "query" [--semantic] [--limit N]

# Update embeddings
python cli.py update-embeddings
```

## Troubleshooting

### Semantic Search Not Working

If semantic search isn't returning expected results:

1. Make sure Ollama is installed and running
2. Run `python process_embeddings.py` to generate embeddings for all entries
3. Verify that new entries have been indexed by checking the database

### Database Issues

If you encounter database errors:

1. Ensure you have proper write permissions for the journal_data directory
2. Try reinitializing the database:
   ```
   python -c "from app.storage import StorageManager; StorageManager().initialize_db(True)"
   ```
   Note: This will reset the database, but your entry files will remain intact

### Server Connection Problems

If you can't connect to the Journal App server:

1. Verify the server is running with `python main.py`
2. Check that you're accessing the correct URL (http://localhost:8000 by default)
3. Ensure no other service is using port 8000

### File Access Issues

If journal entries aren't loading properly:

1. Check that entries exist in the journal_data/entries directory
2. Verify file permissions allow the application to read files
3. Ensure filenames match the expected format (YYYYMMDDHHMMSS.md)
