# Chat Feature Implementation Plan

## Critical Missing Elements (Fix These First)

### 1. Response Streaming
**Problem**: Ollama takes 5-30s for responses. Users will think the app is broken.
**Solution**: Implement SSE (Server-Sent Events) for streaming responses.

### 2. Citation/Attribution System
**Problem**: Users need to know which journal entries informed the chat response.
**Solution**: Return entry references with responses and make them clickable.

### 3. Chat Session Lifecycle
**Problem**: When do chats end? How do we handle partial conversations?
**Solution**: Define session timeout (30 min), auto-save on navigation, explicit "New Chat" action.

### 4. Caching Strategy
**Problem**: Re-running embeddings for every chat query is expensive.
**Solution**: Cache conversation state, pre-compute temporal indices.

## Implementation Plan by Component

### Database Schema

```sql
-- Chat sessions
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    context_summary TEXT,
    temporal_filter TEXT,
    entry_count INTEGER DEFAULT 0
);

-- Chat messages
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    token_count INTEGER,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- Message-entry relationships
CREATE TABLE chat_message_entries (
    message_id TEXT,
    entry_id TEXT,
    similarity_score REAL,
    chunk_index INTEGER,
    PRIMARY KEY (message_id, entry_id),
    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

-- Chat configuration
CREATE TABLE chat_config (
    id TEXT PRIMARY KEY DEFAULT 'default',
    system_prompt TEXT NOT NULL,
    max_context_tokens INTEGER DEFAULT 4096,
    temperature REAL DEFAULT 0.7,
    retrieval_limit INTEGER DEFAULT 10,
    chunk_size INTEGER DEFAULT 500,
    conversation_summary_threshold INTEGER DEFAULT 2000
);
```

### API Endpoints

```python
# app/chat_api.py
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions")
async def create_chat_session() -> ChatSession:
    """Create new chat session"""

@router.get("/sessions")
async def list_chat_sessions(
    limit: int = 10,
    offset: int = 0
) -> List[ChatSession]:
    """List chat sessions with pagination"""

@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str) -> ChatSession:
    """Get specific chat session with messages"""

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete chat session and all messages"""

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message: ChatMessage
) -> EventSourceResponse:
    """Send message and stream response"""

@router.get("/sessions/{session_id}/entries")
async def get_session_referenced_entries(
    session_id: str
) -> List[EntryReference]:
    """Get all entries referenced in session"""
```

### Service Layer

```python
# app/chat_service.py
class ChatService:
    def __init__(self, storage: StorageManager, llm: LLMService):
        self.storage = storage
        self.llm = llm
        self.max_context_tokens = 4096

    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> AsyncGenerator[ChatResponse, None]:
        """Process message with streaming response"""

        # 1. Parse temporal filters from message
        temporal_filter = self._parse_temporal_filter(user_message)

        # 2. Get session context
        session_context = await self._build_session_context(session_id)

        # 3. Retrieve relevant entries
        relevant_entries = await self._retrieve_relevant_entries(
            user_message,
            temporal_filter,
            session_context
        )

        # 4. Build LLM context
        llm_context = self._build_llm_context(
            session_context,
            relevant_entries,
            user_message
        )

        # 5. Stream response
        async for chunk in self.llm.stream_chat_response(llm_context):
            yield chunk

        # 6. Save conversation
        await self._save_conversation_turn(
            session_id,
            user_message,
            chunk.full_response,
            relevant_entries
        )

    def _parse_temporal_filter(self, message: str) -> TemporalFilter:
        """Parse natural language dates"""
        # Use spaCy or simple regex patterns
        # Examples: "last week", "yesterday", "past month"
        pass

    def _build_session_context(self, session_id: str) -> SessionContext:
        """Build context with smart truncation"""
        messages = self.storage.get_chat_messages(session_id)

        # Apply moving window with summarization
        if self._estimate_tokens(messages) > self.max_context_tokens * 0.8:
            summary = self.llm.summarize_conversation(messages[:len(messages)//2])
            recent_messages = messages[len(messages)//2:]
            return SessionContext(summary=summary, messages=recent_messages)

        return SessionContext(messages=messages)

    def _retrieve_relevant_entries(
        self,
        query: str,
        temporal_filter: TemporalFilter,
        session_context: SessionContext
    ) -> List[RetrievedEntry]:
        """Retrieve with chunking and deduplication"""

        # Apply temporal pre-filtering
        candidate_entries = self.storage.get_entries(
            date_from=temporal_filter.start,
            date_to=temporal_filter.end,
            limit=50
        )

        # Semantic search within candidates
        relevant_chunks = []
        for entry in candidate_entries:
            chunks = self._chunk_entry(entry)
            ranked_chunks = self.llm.rank_chunks_by_relevance(chunks, query)
            relevant_chunks.extend(ranked_chunks[:2])

        # Deduplicate against session context
        return self._deduplicate_against_context(
            relevant_chunks,
            session_context
        )
```

### Frontend Components

```javascript
// static/js/chat.js
class ChatInterface {
    constructor() {
        this.currentSessionId = null;
        this.eventSource = null;
        this.messageQueue = [];
    }

    async sendMessage(message) {
        if (!this.currentSessionId) {
            this.currentSessionId = await this.createNewSession();
        }

        this.addMessageToUI('user', message);

        // Start streaming response
        this.eventSource = new EventSource(
            `/chat/sessions/${this.currentSessionId}/messages`
        );

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chunk') {
                this.appendToLastMessage(data.content);
            } else if (data.type === 'complete') {
                this.markMessageComplete(data.citations);
                this.eventSource.close();
            }
        };
    }

    addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="message-content">${this.renderMarkdown(content)}</div>
            <div class="message-meta">
                <span class="timestamp">${new Date().toLocaleString()}</span>
                ${role === 'assistant' ? '<div class="citations"></div>' : ''}
            </div>
        `;
        this.chatContainer.appendChild(messageDiv);
    }

    renderCitations(citations) {
        // Render clickable citations from journal entries
        return citations.map(cite =>
            `<a href="/entries/${cite.entry_id}" class="citation">
                ${cite.title} (${cite.similarity.toFixed(2)})
            </a>`
        ).join('');
    }
}
```

### Configuration Support

```python
# app/models.py
class ChatConfig(BaseModel):
    system_prompt: str = """You are a helpful assistant that helps users explore their journal entries.
    Always cite specific entries when making claims about the user's experiences."""
    max_context_tokens: int = 4096
    temperature: float = 0.7
    retrieval_limit: int = 10
    chunk_size: int = 500
    conversation_summary_threshold: int = 2000

    # Temporal prompt templates
    temporal_prompts: Dict[str, str] = {
        "recent": "focusing on the user's most recent journal entries from the past week",
        "last_week": "looking at entries from last week",
        "last_month": "reviewing entries from the past month",
        "specific_date": "examining entries from {date}"
    }
```

## Testing Strategy (TDD Approach)

### Unit Tests
1. `test_temporal_parser.py` - Verify date parsing accuracy
2. `test_context_management.py` - Test conversation truncation logic
3. `test_retrieval_chunking.py` - Verify chunk extraction and ranking
4. `test_citation_generation.py` - Ensure proper entry attribution

### Integration Tests
1. `test_chat_api.py` - Full chat flow with mocked Ollama
2. `test_session_persistence.py` - Chat session CRUD operations
3. `test_streaming_response.py` - SSE response integrity

### End-to-End Tests
1. `test_full_chat_workflow.py` - Complete user journey
2. `test_temporal_queries.py` - Real queries with date filters
3. `test_multi_session_management.py` - Session isolation

## Implementation Order

1. **Database Schema** (1 day)
   - Create tables, test migrations

2. **Basic Chat API** (2 days)
   - Session CRUD, message saving

3. **Context Management Service** (3 days)
   - Implement moving window + chunking

4. **Temporal Parsing** (2 days)
   - NLP date extraction, filtering logic

5. **Streaming Response** (2 days)
   - SSE implementation, error handling

6. **Frontend Chat UI** (3 days)
   - Chat interface, history view

7. **Citations System** (2 days)
   - Entry references, clickable links

8. **Configuration UI** (1 day)
   - Settings page for chat config

9. **Testing & Polish** (2 days)
   - Full test suite, edge cases

## Performance Considerations

1. **Indexing**: Create composite indices on chat_messages(session_id, created_at)
2. **Caching**: Cache conversation summaries to avoid re-computation
3. **Lazy Loading**: Load chat history on demand, not all at once
4. **Background Tasks**: Run embeddings and summarization in background threads

## Security Considerations

1. **Session Timeout**: 30-minute inactivity timeout
2. **Input Validation**: Sanitize all chat inputs
3. **Rate Limiting**: 10 messages per minute per session
4. **Context Isolation**: Each chat session is completely isolated

## Gotchas to Watch For

1. **Context Bleeding**: Sessions sharing context unexpectedly
2. **Token Explosion**: Conversations growing beyond manageable size
3. **Citation Accuracy**: Ensuring retrieved entries actually influenced the response
4. **Temporal Ambiguity**: "Last week" vs "the week of March 5th"
5. **Performance Degradation**: Chat history growing too large

This plan balances pragmatism with completeness. Start with the database schema and work your way up. Don't overcomplicate the temporal parsing - simple regex patterns will handle 80% of cases.
