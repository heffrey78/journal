# Incremental Implementation Plan for Journal App

## Phase 1: Project Setup & Core Functionality

### Commit 1: Initial Project Structure
```
git commit -m "Initial project setup with directory structure and requirements"
```
- Create directory structure as outlined in MVP doc
- Setup virtual environment
- Add requirements.txt with basic dependencies (fastapi, pydantic, uvicorn)
- Create README.md with project overview

### Commit 2: Data Models Implementation
```
git commit -m "Implement core data models for journal entries"
```
- Implement `models.py` with JournalEntry class
- Add basic validation and test script
- Verify model functionality with simple tests

### Commit 3: Basic Storage Implementation (No Vector DB Yet)
```
git commit -m "Implement basic storage functionality for markdown files and SQLite"
```
- Implement StorageManager without vector DB functionality
- Add methods for saving/loading entries from filesystem
- Initialize SQLite database for metadata
- Create simple CLI to create and view entries

## Phase 2: Backend API Development

### Commit 4: FastAPI Backend - Base Endpoints
```
git commit -m "Add FastAPI backend with basic CRUD operations"
```
- Implement FastAPI app with basic routes:
  - Create entry
  - List entries
  - Get entry by ID
- Implement error handling
- Add simple test client script

### Commit 5: Storage Manager Completion
```
git commit -m "Complete storage manager with get_entries and get_entry methods"
```
- Add missing methods for retrieving entries
- Implement update and delete functionality
- Add basic text search functionality
- Connect storage manager to API endpoints

## Phase 3: Vector Search Integration

### Commit 6: SQLite Vector Search Integration
```
git commit -m "Add SQLite-based vector storage"
```
- Add numpy and scikit-learn to requirements
- Implement vector storage functionality in StorageManager using SQLite
- Add chunking functionality for text
- Update entry creation to include vector storage
- Prepare for Ollama integration in Commit 8

### Commit 7: Simple Text Search
```
git commit -m "Implement basic text search functionality"
```
- Implement basic text search in SQLite
- Add search endpoint to API
- Create simple test script for searching

## Phase 4: Ollama LLM Integration

### Commit 8: Structured Output Implementation
```
git commit -m "Implement structured outputs for journal entry analysis"
```
- Implement EntrySummary model
- Add summarize_entry method using Ollama's structured output
- Connect to API via endpoint
- Test with sample journal entries

### Commit 9: Semantic Search
```
git commit -m "Add semantic search functionality via Ollama embeddings"
```
- Implement semantic_search method in LLMService
- Connect embeddings to SQLite vector storage
- Add semantic search option to search endpoint
- Create test script for semantic searching

## Phase 5: Frontend Implementation

### Commit 10: Basic HTML/CSS Structure
```
git commit -m "Add initial HTML structure and static file serving"
```
- Create index.html with basic layout
- Implement CSS for simple styling
- Configure FastAPI to serve static files
- Test basic page loading

### Commit 11: Entry Creation & Listing UI
```
git commit -m "Implement UI for creating and listing journal entries"
```
- Add form for entry creation
- Implement entry listing view
- Connect to API endpoints with JavaScript
- Test basic workflow

### Commit 12: Entry Detail View & Search UI
```
git commit -m "Add entry detail view and search functionality to UI"
```
- Implement entry detail page
- Add search box and results display
- Connect to search endpoints
- Test complete basic workflow

## Phase 6: LLM Features in UI

### Commit 13: Summary Feature UI
```
git commit -m "Add entry summarization feature to UI"
```
- Add summary button to entry detail view
- Implement summary display component
- Connect to summary endpoint
- Test summarization functionality

### Commit 14: Advanced Search Options
```
git commit -m "Enhance UI with semantic search toggle and advanced options"
```
- Add semantic search toggle to search UI
- Implement search by date range and tags
- Create advanced search form with expanded options
- Modify search endpoint to support combined filtering
- Add visual indicators for search method in use
- Create utility for embeddings generation
- Add script to generate embeddings for existing entries
- Implement error handling for semantic search failures
- Update documentation with search usage examples
- Test advanced search functionality with various query combinations

## Phase 7: Refinement & Quality Assurance

### Commit 15: Error Handling & UX Improvements
```
git commit -m "Improve error handling and user experience"
```
- Add proper error handling in UI and API
- Improve loading states
- Add confirmation dialogs
- Test edge cases

### Commit 16: Performance Optimization
```
git commit -m "Optimize performance for vector search and entry loading"
```
- Add deletion to Journal Entries, Search results, and Entry details
- Add pagination for entry listing
- Optimize chunking algorithm
- Implement caching where appropriate
- Test with larger dataset

### Commit 17: Documentation & Testing
```
git commit -m "Add comprehensive documentation and testing"
```
- Complete README with setup instructions
- Add inline code documentation
- Write basic usage guide
- Create automated tests for core functionality

## Testing Approach for Each Phase

1. **Manual Testing**: Create test scripts for each component
2. **API Testing**: Use tools like curl or Postman to test endpoints
3. **Integration Testing**: Ensure components work together
4. **UI Testing**: Manual testing of UI workflows

By following this incremental plan, you'll have a working application at each step, allowing you to validate functionality before moving on to the next feature.
