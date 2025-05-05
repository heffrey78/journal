# Journal App

The Journal App is a personal journaling application designed to help users create, store, and search journal entries efficiently. It features a FastAPI backend, SQLite for metadata storage, and vector search capabilities using SQLite and Ollama.

## Features

- **Markdown Journal Entries**: Store your journal entries in markdown format
- **SQLite Database**: Efficient storage of entry metadata and vector embeddings
- **Vector Search**: Semantic search capabilities powered by Ollama embeddings
- **Enhanced LLM Features**:
  - Choose from multiple prompt types for entry analysis
  - Track analysis progress in real-time
  - Save favorite analyses for future reference
- **Simple UI**: Clean web interface for creating and searching journal entries
- **Modern Next.js Frontend**: Alternative frontend with enhanced UI experience and full feature parity

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
   For development, use:
   ```
   pip install -r requirements-dev.txt
   ```
4. Make sure you have Ollama installed and running locally (see [Ollama website](https://ollama.com/))
5. Initialize the database:
   ```
   python -c "from app.storage import StorageManager; StorageManager().initialize_db()"
   ```

## Usage

### Starting the Application

1. Start the API server:
   ```
   uvicorn main:app --reload
   ```
   Or use the simpler command:
   ```
   python main.py
   ```
2. Open your browser to `http://localhost:8000` to access the standard UI

### Using the Next.js Frontend

The Journal App includes a modern alternative frontend built with Next.js:

1. Make sure the API server is running (as above)
2. Navigate to the Next.js directory:
   ```
   cd journal-app-next
   ```
3. Install dependencies (first time only):
   ```
   npm install
   ```
4. Start the development server:
   ```
   npm run dev
   ```
5. Open your browser to `http://localhost:3000`

The Next.js frontend provides all the same functionality as the standard UI but with an enhanced user experience, including:
- Light and dark mode support
- Improved editor interface
- Better navigation and transitions
- Full support for semantic search and AI features
- Additional customization options

For more details, see the [User Guide](/docs/user_guide.md#using-the-nextjs-frontend).

### Using the CLI

The CLI provides quick access to journal functions from the terminal:

```
# Add a new entry
python cli.py add "My journal entry title" "Content of my entry"

# List recent entries
python cli.py list

# Show a specific entry
python cli.py show 20250503110105

# Search for entries
python cli.py search "query text"

# Use semantic search
python cli.py search "query text" --semantic
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

The Journal App exposes the following REST API endpoints:

### Entries Management

- `POST /entries/`: Create a new journal entry
- `GET /entries/`: List all journal entries (with pagination and filters)
- `GET /entries/{entry_id}`: Get a specific entry by ID
- `PATCH /entries/{entry_id}`: Update an existing entry
- `DELETE /entries/{entry_id}`: Delete an entry

### Search

- `GET /entries/search/?query=text&semantic=true`: Simple search via query parameters
- `POST /entries/search/`: Advanced search with JSON body for complex filters

### Tags

- `GET /tags/`: List all unique tags used in entries
- `GET /tags/{tag}/entries`: Get all entries with a specific tag

### LLM Features

- `POST /entries/{entry_id}/summarize`: Generate basic AI summary of an entry
- `POST /entries/{entry_id}/summarize/custom`: Generate custom analysis with specified prompt type
  - Request body: `{"prompt_type": "default|detailed|creative|concise"}`
- `POST /entries/{entry_id}/summaries/favorite`: Save a summary as a favorite
- `GET /entries/{entry_id}/summaries/favorite`: Retrieve all favorite summaries for an entry

### Statistics

- `GET /stats/`: Get statistics about your journal entries

## Error Handling

The API provides structured error responses for easier debugging:

```json
{
  "status_code": 404,
  "message": "Entry with ID 20220101000000 not found",
  "details": null,
  "timestamp": "2025-05-03T12:34:56"
}
```

## Testing

The project includes comprehensive tests for all major components:

### Running Tests

```
# Run all tests
pytest

# Run specific test file
pytest test_api.py

# Run with coverage report
pytest --cov=app
```

### Test Categories

- Unit tests: Test individual components in isolation
- Integration tests: Test components working together
- API tests: Test the HTTP API endpoints
- Search tests: Dedicated tests for various search capabilities

## Development

### Project Structure

- `app/`: Main application code
  - `api.py`: FastAPI routes and handlers
  - `models.py`: Pydantic data models
  - `storage.py`: Data storage and retrieval logic
  - `llm_service.py`: LLM integration for AI features
- `static/`: Frontend UI files
- `tests/`: Test modules
- `cli.py`: Command-line interface
- `main.py`: Application entry point
- `update_embeddings.py`: Utility for generating embeddings
- `process_embeddings.py`: Utility for processing existing entries

### Contributing

1. Create a feature branch: `git checkout -b feature-name`
2. Make your changes
3. Run tests: `pytest`
4. Submit a pull request

## Example Usage

See the `test_vector_search.py` script for a demonstration of the vector search capabilities.
