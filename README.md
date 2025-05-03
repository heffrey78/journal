# Journal App

The Journal App is a personal journaling application designed to help users create, store, and search journal entries efficiently. It features a FastAPI backend, SQLite for metadata storage, and vector search capabilities using SQLite and Ollama.

## Features

- **Markdown Journal Entries**: Store your journal entries in markdown format
- **SQLite Database**: Efficient storage of entry metadata and vector embeddings
- **Vector Search**: Semantic search capabilities powered by Ollama embeddings
- **Text Analysis**: Get summaries and insights about your journal entries
- **Simple UI**: Clean web interface for creating and searching journal entries

## Architecture

The application uses a simple architecture with SQLite at its core:

- **Storage**: SQLite database stores both entry metadata and vector embeddings
- **Vectors**: Text chunks are embedded using Ollama and stored in SQLite
- **Search**: Semantic search uses cosine similarity for finding relevant entries
- **LLM Features**: Entry summarization and analysis via Ollama

## Requirements

- Python 3.8+
- FastAPI
- SQLite
- Ollama
- NumPy and scikit-learn for vector operations

## Installation

1. Clone the repository
2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Make sure you have Ollama installed and running locally (see [Ollama website](https://ollama.com/))

## Usage

1. Start the API server:
   ```
   uvicorn main:app --reload
   ```
2. Open your browser to `http://localhost:8000` to access the UI
3. Use the CLI for quick entries:
   ```
   python cli.py add "My journal entry title" "Content of my entry"
   ```

## Vector Search Setup

To enable semantic search:

1. Create entries using the API or CLI
2. Process embeddings with the included utility script:
   ```
   python process_embeddings.py
   ```
3. Use semantic search in the UI or API

> **Important**: Semantic search requires embeddings to be generated for your journal entries. New entries are initially stored without embeddings, and the `process_embeddings.py` script must be run to generate these embeddings. If semantic search isn't returning expected results, make sure you've run this script after creating new entries.

### How Semantic Search Works

Unlike traditional text search (which looks for exact keyword matches), semantic search understands the meaning and context of your query:

- **Text Search**: Finds entries containing the exact words you searched for
- **Semantic Search**: Finds entries related to your search concept, even if they use different words

For example, searching for "food" might return entries about "cooking", "recipes", or "dinner" even if they don't contain the word "food".

The process works by:
1. Converting text into numerical vectors (embeddings) that represent meaning
2. Finding entries with similar vector representations to your search query
3. Ranking results by similarity score

You can toggle between text search and semantic search in the UI by checking the "Use semantic search" option.

## Advanced Search Options

The Journal App includes powerful search capabilities that can be combined to find exactly what you're looking for:

### Search Types

1. **Text Search**: Finds entries that contain specific keywords in their title, content, or tags.
   - Example: Searching for "finance" will find entries with that word in title, content, or tags.

2. **Semantic Search**: Finds entries that are conceptually related to your query, even if they don't contain the exact words.
   - Example: Searching for "financial planning" might find entries about "savings accounts" or "budget".

### Filters

You can combine your search with filters:

- **Date Range**: Filter entries by date, using either "from" date, "to" date, or both.
- **Tags**: Filter entries that have specific tags.

### Using Advanced Search

From the UI:
1. Click "Search" in the navigation
2. Enter your search terms
3. Check "Use semantic search" if desired
4. Click "Show advanced options" to access date and tag filters
5. Apply filters as needed and search

From the API:
```
POST /entries/search/
{
  "query": "your search terms",
  "semantic": true,
  "date_from": "2025-05-01",
  "date_to": "2025-05-31",
  "tags": ["work", "ideas"]
}
```

### Keeping Semantic Search Updated

Remember to run the embeddings generator after adding new entries:
```
python update_embeddings.py
```

This will index any new entries into the semantic search engine.

## API Endpoints

- `POST /entries/`: Create a new journal entry
- `GET /entries/`: List all journal entries
- `GET /entries/{entry_id}`: Get a specific entry
- `GET /search/?q=query&semantic=true`: Search entries (set semantic=true for vector search)
- `POST /entries/{entry_id}/summary`: Get AI summary of an entry

## Example Usage

See the `test_vector_search.py` script for a demonstration of the vector search capabilities.
