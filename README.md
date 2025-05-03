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

## API Endpoints

- `POST /entries/`: Create a new journal entry
- `GET /entries/`: List all journal entries
- `GET /entries/{entry_id}`: Get a specific entry
- `GET /search/?q=query&semantic=true`: Search entries (set semantic=true for vector search)
- `POST /entries/{entry_id}/summary`: Get AI summary of an entry

## Example Usage

See the `test_vector_search.py` script for a demonstration of the vector search capabilities.
