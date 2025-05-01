# Local Journaling Application MVP Plan

Based on your requirements for a simple, local journaling application with markdown storage and vector search capabilities, I'll outline a clean, minimalist architecture using Ollama for LLM functionality.

## Architecture Overview

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   FastAPI     │◄────►│  Journal Core │◄────►│ Local Storage │
│   Backend     │      │  Business     │      │ - Markdown    │
│               │      │  Logic        │      │ - Vectors     │
└───────┬───────┘      └───────────────┘      └───────────────┘
        │                      ▲                      ▲
        ▼                      │                      │
┌───────────────┐              │              ┌───────────────┐
│  Simple UI    │              └──────────────┤  Ollama LLM   │
│  (HTML/JS)    │                             │  Service      │
└───────────────┘                             └───────────────┘
```

## Core Components

### 1. Data Model

```python
# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    tags: List[str] = []
```

### 2. Storage Manager

```python
# storage.py
import os
import json
import sqlite3
from datetime import datetime
import chromadb  # Lightweight vector DB

class StorageManager:
    def __init__(self, base_dir="./journal_data"):
        # Setup directory structure
        self.base_dir = base_dir
        self.entries_dir = os.path.join(base_dir, "entries")
        self.db_path = os.path.join(base_dir, "journal.db")

        # Ensure directories exist
        os.makedirs(self.entries_dir, exist_ok=True)

        # Initialize SQLite for metadata
        self._init_sqlite()

        # Initialize ChromaDB for vector storage
        self.vector_db = chromadb.PersistentClient(os.path.join(base_dir, "vectordb"))
        self.collection = self.vector_db.get_or_create_collection("journal_entries")

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            tags TEXT
        )
        ''')
        conn.commit()
        conn.close()

    def save_entry(self, entry):
        # Save markdown to file
        file_path = os.path.join(self.entries_dir, f"{entry.id}.md")
        with open(file_path, "w") as f:
            f.write(f"# {entry.title}\n\n{entry.content}")

        # Save metadata to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry.id,
                entry.title,
                file_path,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat() if entry.updated_at else None,
                json.dumps(entry.tags)
            )
        )
        conn.commit()
        conn.close()

        # Index in vector database
        self._index_in_vector_db(entry)

        return entry.id

    def _index_in_vector_db(self, entry):
        # Chunk content (simple approach for MVP)
        chunks = self._chunk_text(entry.content)

        # Add to vector DB
        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                metadatas=[{"entry_id": entry.id, "chunk_id": i}],
                ids=[f"{entry.id}_{i}"]
            )

    def _chunk_text(self, text, chunk_size=500):
        """Simple chunking by rough character count"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1  # +1 for space

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
```

### 3. Ollama Integration

```python
# llm_service.py
from typing import List, Dict, Any
from pydantic import BaseModel
import ollama

class EntrySummary(BaseModel):
    summary: str
    key_topics: List[str]
    mood: str

class LLMService:
    def __init__(self, model="llama3.1"):
        self.model = model

    def summarize_entry(self, content: str) -> EntrySummary:
        """Generate a summary of a journal entry using Ollama with structured output"""
        response = ollama.chat(
            messages=[{
                'role': 'user',
                'content': f"Summarize this journal entry and extract key topics and mood. Return as JSON:\n\n{content}"
            }],
            model=self.model,
            format={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "key_topics": {"type": "array", "items": {"type": "string"}},
                    "mood": {"type": "string"}
                },
                "required": ["summary", "key_topics", "mood"]
            }
        )

        return EntrySummary.model_validate_json(response.message.content)

    def semantic_search(self, query: str, vector_collection) -> List[Dict[str, Any]]:
        """Search journal entries semantically"""
        # First, get an embedding for the query using Ollama
        response = ollama.embeddings(model=self.model, prompt=query)
        query_embedding = response['embedding']

        # Use the embedding to search the vector database
        results = vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        return results
```

### 4. FastAPI Backend

```python
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from datetime import datetime
import os

from models import JournalEntry
from storage import StorageManager
from llm_service import LLMService

app = FastAPI(title="Journal App")
storage = StorageManager()
llm = LLMService()

# Mount static files for UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/entries/", response_model=dict)
async def create_entry(entry: JournalEntry):
    entry_id = storage.save_entry(entry)
    return {"id": entry_id, "message": "Entry created successfully"}

@app.get("/entries/", response_model=List[JournalEntry])
async def list_entries(limit: int = 10, offset: int = 0):
    return storage.get_entries(limit, offset)

@app.get("/entries/{entry_id}", response_model=JournalEntry)
async def get_entry(entry_id: str):
    entry = storage.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@app.post("/entries/{entry_id}/summary")
async def summarize_entry(entry_id: str):
    entry = storage.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    summary = llm.summarize_entry(entry.content)
    return summary

@app.get("/search/")
async def search_entries(q: str, semantic: bool = False):
    if semantic:
        return llm.semantic_search(q, storage.collection)
    else:
        return storage.text_search(q)

# Add additional routes for updating/deleting entries
```

### 5. Simple UI (HTML/JS)

For an MVP, a minimal HTML/JavaScript frontend that communicates with the FastAPI backend would be sufficient. This could include:

- A simple form for creating entries
- A list view of all entries with search functionality
- A detail view for reading/editing entries
- Basic LLM-powered functionality (summarize, analyze)

## Implementation Plan

1. **Setup Project Structure**
   ```
   journal_app/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── models.py
   │   ├── storage.py
   │   └── llm_service.py
   ├── static/
   │   ├── index.html
   │   ├── css/
   │   └── js/
   ├── journal_data/
   │   ├── entries/
   │   └── vectordb/
   ├── requirements.txt
   └── README.md
   ```

2. **Dependencies**
   ```
   fastapi
   uvicorn
   pydantic
   ollama
   chromadb
   sqlite3
   python-multipart
   ```

3. **Development Steps**
   1. Implement storage manager
   2. Set up vector database
   3. Integrate Ollama
   4. Develop FastAPI endpoints
   5. Create minimal UI
   6. Test and refine

## Advanced Features (Post-MVP)

1. **Enhanced Analysis**
   - Trend analysis over time
   - Mood tracking
   - Topic clustering

2. **Content Generation**
   - Guided journaling prompts
   - Reflective questions based on past entries

3. **Security Measures**
   - Encryption for sensitive journal entries
   - Authentication for multi-user support

This MVP architecture balances simplicity with functionality, using lightweight components that can run entirely locally without complex dependencies. The modular design allows for easy extension and refinement after the initial version is working.
