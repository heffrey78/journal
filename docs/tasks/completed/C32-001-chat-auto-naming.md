# C32-001: Automatic Chat Session Naming

## Priority: Medium
## Status: Completed
## Estimated Effort: 3-4 hours

## User Story
**As a** journal user
**I want** chat sessions to be automatically named based on their content
**So that** I can easily identify and find previous conversations without having to manually name them

## Problem Description
Currently, chat sessions have generic names or require manual naming. This makes it difficult to identify the content or purpose of previous chat sessions when browsing chat history. Users need an intelligent auto-naming system that generates meaningful names based on the conversation context.

## Acceptance Criteria
- [x] Chat sessions are automatically named after the first few message exchanges
- [x] Names are generated based on the main topic or theme of the conversation
- [x] Names are concise (2-6 words) but descriptive
- [x] Auto-generated names can be manually overridden by users
- [x] Names are updated if the conversation topic shifts significantly
- [x] Fallback naming pattern for conversations that can't be categorized

## Technical Details
- **Components affected**:
  - `app/chat_service.py` (add naming logic)
  - `app/llm_service.py` (add title generation method)
  - `app/storage/chat.py` (update session title)
  - `journal-app-next/src/components/chat/ChatSessionsSidebar.tsx` (display auto-generated names)
- **Current behavior**: Chat sessions have generic names or require manual naming
- **Expected behavior**: Sessions automatically get meaningful names based on content
- **Database changes**: None (title field already exists in ChatSession model)
- **API changes**: Add endpoint for manual title updates

## Implementation Plan
### Phase 1: Core Auto-Naming Logic
1. Add `generate_session_title()` method to LLMService
2. Update ChatService to trigger naming after 2-3 message exchanges
3. Implement title generation using conversation context

### Phase 2: Smart Naming Features
1. Add topic shift detection for title updates
2. Implement fallback naming patterns
3. Add manual title override functionality

## Definition of Done
- [x] All acceptance criteria are met
- [x] Auto-naming works reliably for various conversation types
- [x] Manual override functionality is implemented
- [x] Tests cover auto-naming logic
- [x] Code follows project conventions
- [x] No linting errors
- [x] Feature works in both development and production modes

## Completion Summary
**Completed on:** 2025-01-03

### Changes Made:
1. **LLMService Enhancement**: Added `generate_session_title()` method that uses the LLM to create concise, descriptive titles from conversation context with fallback handling
2. **ChatService Integration**: Added `_check_and_generate_session_title()` method that triggers auto-naming after 2+ message exchanges and includes topic shift detection
3. **API Endpoint**: Added `PATCH /chat/sessions/{session_id}/title` endpoint for manual title overrides
4. **Topic Shift Detection**: Implemented `_has_topic_shifted()` method that compares keyword similarity between current and potential new titles
5. **Comprehensive Testing**: Created 7 test cases covering all auto-naming scenarios including edge cases and error handling

### Verification:
- All 7 tests pass successfully
- Auto-naming triggers after 2 complete exchanges (4 messages)
- Meaningful titles are preserved from manual override
- Topic shift detection works for long conversations (8+ exchanges)
- LLM failures gracefully fall back to "Chat Session"
- Frontend already displays session titles correctly
- API endpoint supports manual title updates
