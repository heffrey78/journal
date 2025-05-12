# Chat History and Session Management Implementation Plan

## Overview

This document outlines the plan for implementing a chat history and session management UI for the journal application. The implementation will integrate with the existing Next.js frontend and backend chat services.

## Current State Analysis

1. **Backend**:
   - Chat API routes defined in `app/chat_routes.py`
   - Chat service implementation in `app/chat_service.py`
   - Chat storage handling in `app/storage/chat.py`
   - Models defined in `app/models.py` (ChatSession, ChatMessage, etc.)

2. **Frontend**:
   - Next.js frontend with main layout in `journal-app-next/src/app/layout.tsx`
   - Navigation with chat link already in `Header.tsx`
   - No existing chat UI implementation yet

## Implementation Goals

1. **Backend Enhancement**:
   - Ensure proper API endpoints for listing and managing chat sessions
   - Add sorting and filtering options for sessions
   - Add pagination support for chat history

2. **Frontend Implementation**:
   - Create chat session list view
   - Develop session creation UI
   - Implement session switching
   - Add session deletion functionality
   - Create responsive design for mobile and desktop

## Technical Design

### 1. Backend Enhancements

#### 1.1 API Endpoints

Add or enhance the following endpoints in `chat_routes.py`:

```python
@chat_router.get("/sessions", response_model=List[ChatSession])
async def list_chat_sessions(
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    storage=Depends(get_storage)
)
```

This will allow retrieving chat sessions with sorting and pagination.

#### 1.2 Chat Storage Enhancement

Add methods to `ChatStorage` class in `storage/chat.py`:

```python
def get_sessions(
    self,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "updated_at",
    sort_order: str = "desc"
) -> List[ChatSession]:
    """
    Get a list of chat sessions with pagination and sorting options.

    Args:
        skip: Number of sessions to skip
        limit: Maximum number of sessions to return
        sort_by: Field to sort by ('updated_at', 'created_at', 'title')
        sort_order: Sort order ('asc' or 'desc')

    Returns:
        List of chat sessions
    """
```

Add statistics methods to get session-specific data:

```python
def get_session_stats(self, session_id: str) -> Dict[str, Any]:
    """
    Get statistics for a specific chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Dictionary with message count, unique entry references, etc.
    """
```

### 2. Frontend Implementation

#### 2.1 Route Structure

```
/chat
  ├── page.tsx         # Chat sessions list
  ├── layout.tsx       # Chat layout with sidebar
  ├── new/
  │    └── page.tsx    # New session creation page
  └── [session_id]/
       ├── page.tsx    # Chat interface for specific session
       └── settings/
            └── page.tsx # Session settings page
```

#### 2.2 Chat Session List Interface

Create a component for the session list that will:
- Display session titles and last updated timestamps
- Show message counts
- Provide sorting options
- Include a "New Chat" button
- Allow deletion of sessions

#### 2.3 Components

1. **ChatSessionsList**: Main component for listing all chat sessions
   - Features pagination and sorting
   - Displays session metadata (date, message count)

2. **ChatSessionCard**: Card component for individual sessions
   - Shows title, date, and preview of last message
   - Includes action menu (delete, rename)

3. **NewChatButton**: Button to create new chat sessions

4. **ChatSessionsSidebar**: Sidebar for displaying sessions while in a chat
   - Shows current and recent sessions
   - Allows switching between them

### 3. Data Models

#### 3.1 Frontend Types

Create TypeScript interfaces in `types/chat.ts`:

```typescript
interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_accessed: string;
  context_summary?: string;
  temporal_filter?: string;
  entry_count: number;
}

interface ChatSessionStats {
  message_count: number;
  user_message_count: number;
  assistant_message_count: number;
  reference_count: number;
}
```

### 4. API Clients

Create API client functions in `api/chat.ts`:

```typescript
async function fetchChatSessions(
  page: number = 1,
  limit: number = 10,
  sortBy: string = 'updated_at',
  sortOrder: string = 'desc'
): Promise<{ sessions: ChatSession[], total: number }>
```

```typescript
async function createChatSession(title?: string): Promise<ChatSession>
```

```typescript
async function deleteSession(sessionId: string): Promise<boolean>
```

## Implementation Plan

### Phase 1: Backend Enhancements (2 days)

1. **API Endpoint Refinement**
   - Enhance existing endpoints or add new ones for session listing
   - Add sorting, filtering, and pagination support
   - Implement proper error handling

2. **Storage Layer Updates**
   - Add session statistics methods
   - Optimize queries for performance

3. **Testing**
   - Unit tests for new functionality
   - Integration tests for API endpoints

### Phase 2: Frontend Chat Sessions List (3 days)

1. **Session List Page**
   - Create `/chat` route and page component
   - Implement session listing with pagination
   - Add sorting and filtering options

2. **New Chat Functionality**
   - Implement "New Chat" button
   - Add session creation modal or page
   - Handle successful creation and redirection

3. **Session Actions**
   - Add delete functionality with confirmation dialog
   - Implement session renaming
   - Add session stats display

4. **Visual Design**
   - Apply existing theme and styling
   - Ensure responsive design for mobile

### Phase 3: Chat Session Management (2 days)

1. **Chat Sidebar**
   - Implement session switching sidebar
   - Show recent and favorite sessions
   - Allow quick creation of new sessions

2. **Session Settings**
   - Create settings page for individual sessions
   - Allow updating title and other metadata
   - Add option to clear chat history

3. **Session Context**
   - Add context provider for active session
   - Handle session state management

### Phase 4: Testing and Refinement (3 days)

1. **Integration Testing**
   - End-to-end tests for session workflows
   - Test across devices and screen sizes

2. **Performance Optimization**
   - Lazy loading for session content
   - Optimize state management
   - Add caching for frequently accessed data

3. **UX Improvements**
   - Add loading states
   - Implement error handling UI
   - Add animations and transitions

## UI Mockups

### Chat Sessions List
```
+-----------------------------------------------+
| Journal App                            Theme  |
+-----------------------------------------------+
|                                               |
| Chat Sessions                  + New Chat     |
|                                               |
| Sort by: Last Updated ▼      10 per page ▼    |
|                                               |
| +-------------------------------------------+ |
| | Weekly Planning Discussion          5/10  | |
| | Last message: Let me help you plan...     | |
| | 15 messages · 3 references                | |
| +-------------------------------------------+ |
|                                               |
| +-------------------------------------------+ |
| | Journal Reflections                 5/8   | |
| | Last message: Your entries show...        | |
| | 22 messages · 7 references                | |
| +-------------------------------------------+ |
|                                               |
| +-------------------------------------------+ |
| | Goal Setting Conversation          5/5    | |
| | Last message: Based on your goals...      | |
| | 8 messages · 2 references                 | |
| +-------------------------------------------+ |
|                                               |
|           ◁   1 2 3 ... 8   ▷                |
|                                               |
+-----------------------------------------------+
```

### Chat Interface with Session Sidebar
```
+-----------------------------------------------+
| Journal App                            Theme  |
+-----------------------------------------------+
|                                               |
| +-----------+-----------------------------+   |
| | Sessions  | Weekly Planning Discussion  |   |
| |           |                             |   |
| | + New     | [User]                      |   |
| |           | What are my upcoming tasks? |   |
| | Weekly... |                             |   |
| |           | [Assistant]                 |   |
| | Journal.. | Based on your journal       |   |
| |           | entries, you have:          |   |
| | Goal S... | - Project deadline on 5/15  |   |
| |           | - Meeting with team on 5/12 |   |
| | Recent... | - Dentist appointment 5/14  |   |
| |           |                             |   |
| +-----------+ [Message input field]       |   |
|                                               |
+-----------------------------------------------+
```

## Migration Plan

1. **Database Updates**
   - No schema changes needed (using existing tables)
   - Add indexes for optimized queries if needed

2. **API Updates**
   - Add new endpoints incrementally
   - Maintain backward compatibility for existing clients

3. **UI Integration**
   - Integrate with existing layout components
   - Match application theme and design patterns

## Security Considerations

1. **Authentication**
   - Ensure all endpoints are properly authenticated
   - Use existing authentication mechanisms

2. **Authorization**
   - Validate session ownership before operations
   - Prevent access to other users' sessions

3. **Input Validation**
   - Validate all request parameters
   - Sanitize inputs to prevent injection attacks

## Conclusion

This implementation plan provides a comprehensive approach to adding chat history and session management functionality to the journal application. By following the outlined phases, the development team can incrementally build and test this feature while maintaining compatibility with the existing codebase.

The plan prioritizes user experience by focusing on intuitive navigation, clear visual design, and efficient session management workflows. Once implemented, users will be able to easily navigate between chat sessions, manage their conversation history, and maintain context across interactions with the journal assistant.
