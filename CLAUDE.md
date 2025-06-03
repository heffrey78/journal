# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is Llens, a full-stack journal application with AI-powered features:

- **Backend**: FastAPI Python API with SQLite storage
- **Frontend**: Next.js TypeScript app (in `journal-app-next/`)
- **Storage**: Markdown files for entries, SQLite for metadata and vector embeddings
- **AI Features**: Ollama integration for chat, summarization, and semantic search

## Essential Commands

### Backend Development
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run API server
python main.py
# OR
uvicorn main:app --reload

# Process embeddings (required for semantic search)
python process_embeddings.py
```

### Frontend Development
```bash
cd journal-app-next
npm install
npm run dev    # Development server
npm run build  # Production build
npm run lint   # Run linting
```

### Testing
```bash
# Run all tests
pytest

# Run specific test
pytest test_api.py
pytest tests/test_chat_api.py

# Run with coverage
pytest --cov=app
```

## Task Tracking System

This project uses a markdown-based task tracking system in `docs/tasks/`. When working on new features or fixes:

### Task File Format
Each task follows the naming convention: `CXX-NNN-description.md` where:
- `CXX` = Commit/Sprint number (e.g., C29)
- `NNN` = Task number (e.g., 001)
- `description` = Brief kebab-case description

### Task Structure
```markdown
# CXX-NNN: Task Title

## Priority: High/Medium/Low
## Status: Pending/In Progress/Completed
## Estimated Effort: X hours

## User Story
**As a** [user type]
**I want** [goal]
**So that** [benefit]

## Problem Description
[Detailed description of the issue/feature]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Details
- **Files affected**: List of files
- **Current behavior**: What happens now
- **Expected behavior**: What should happen

## Definition of Done
- All acceptance criteria met
- Tests written and passing
- Documentation updated

## Completion Summary (when done)
**Completed on:** YYYY-MM-DD
### Changes Made:
[List of changes]
### Verification:
[How it was tested]
```

### Summary File
Create a `CXX-summary.md` file for each sprint/commit group that lists all tasks, their status, and implementation order.

## Key Architecture Decisions

1. **Modular Storage System** (`app/storage/`):
   - Base storage class with specialized modules (entries, tags, vectors, chat)
   - SQLite for both metadata and vector embeddings (no separate vector DB)
   - Entries stored as markdown files in `journal_data/entries/`

2. **API Structure**:
   - Main routes in `app/api.py`
   - Specialized routes: `chat_routes.py`, `config_routes.py`, `organization_routes.py`
   - Pydantic models in `app/models.py` for validation

3. **LLM Integration**:
   - `app/llm_service.py`: Ollama integration for AI features
   - `app/chat_service.py`: Chat with context management
   - Vector search in `app/storage/vector_search.py`

4. **Frontend Architecture**:
   - API proxy configured in `next.config.ts` (backend on port 8000)
   - Components in `src/components/` organized by feature
   - Theme system with light/dark mode support

## Important Notes

- Database auto-initializes on first run at `./journal_data/journal.db`
- Ollama must be running locally for AI features to work
- Frontend expects API on port 8000 (configured in proxy)
- Vector embeddings must be processed (`process_embeddings.py`) for semantic search
- All journal entries are markdown files with YAML frontmatter for metadata
