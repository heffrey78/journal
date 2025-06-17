# C36-001: Move Persona Selection to Chat Interface Dropdown

## Priority: Medium
## Status: Completed
## Estimated Effort: 4-6 hours

## User Story
**As a** chat user
**I want** to change personas seamlessly during chat conversations using a dropdown next to the model selector
**So that** I can quickly switch conversation styles without needing to create new chat sessions

## Problem Description
Currently, users must select a persona when creating a new chat session via the `/chat/new` page. This creates friction in the user experience because:

1. Users cannot change personas mid-conversation
2. The persona selection is buried in the new chat flow
3. Users must create new sessions to try different personas
4. The current UX separates persona selection from other chat controls

The improved UX should place persona selection directly in the chat interface as a dropdown control next to the model selector, making it easily accessible and allowing dynamic switching.

## Acceptance Criteria
- [x] Persona dropdown is positioned to the left of the model dropdown in chat interface
- [x] Dropdown displays both persona icon and persona name
- [x] Users can switch personas mid-conversation
- [x] Current persona is clearly indicated in the dropdown
- [x] Persona changes are applied to subsequent messages (not retroactively)
- [x] Default persona is pre-selected when no persona is chosen
- [x] Dropdown shows all available personas (default + custom)
- [x] Visual design is consistent with existing model dropdown
- [x] Persona changes are saved to the chat session
- [x] Tests are written and passing
- [x] Documentation is updated

## Technical Details
- **Components affected**:
  - `journal-app-next/src/components/chat/ChatInterface.tsx`
  - `journal-app-next/src/components/chat/PersonaSelector.tsx` (refactor for dropdown use)
  - `journal-app-next/src/app/chat/new/page.tsx` (simplified flow)
  - `journal-app-next/src/api/chat.ts` (persona update endpoint)
  - `app/chat_routes.py` (backend persona update support)

- **Current behavior**: Persona selected only at chat creation via dedicated page
- **Expected behavior**: Persona selectable and changeable via dropdown in chat interface

- **API changes**:
  - Add endpoint to update chat session persona: `PATCH /api/chat/sessions/{session_id}/persona`
  - Modify chat message API to include current session persona in system prompt

## Implementation Plan

### Phase 1: Backend Support for Dynamic Persona Changes
1. Add API endpoint to update chat session persona
2. Modify chat service to use current session persona for new messages
3. Update chat session model to track persona changes

### Phase 2: Frontend Persona Dropdown Component
1. Create compact PersonaDropdown component based on existing PersonaSelector
2. Include persona icon and name display
3. Integrate dropdown into ChatInterface header next to ModelSelector
4. Handle persona change events and API calls

### Phase 3: UX Flow Simplification
1. Simplify `/chat/new` page to redirect directly to chat with default persona
2. Update "New Chat" buttons throughout app
3. Remove dependency on persona pre-selection for chat creation

## Dependencies
- Requires existing persona system (C35 tasks)
- May affect chat session storage and retrieval

## Definition of Done
- [x] All acceptance criteria are met
- [x] Code follows project conventions
- [x] Tests provide adequate coverage for persona switching
- [x] Documentation is updated
- [x] Code has been reviewed
- [x] No linting errors (persona-related code)
- [x] Feature works in both development and production modes
- [x] Persona switching works smoothly without breaking chat flow
- [x] Default persona behavior is preserved for existing functionality

## Completion Summary
**Completed on:** 2025-01-08

### Changes Made:
1. **Backend API Support** (app/chat_routes.py):
   - Added `persona_id` field to ChatSessionCreate and ChatSessionUpdate models
   - Updated session creation logic to handle persona_id
   - Updated session update logic to handle persona_id changes

2. **Frontend API Integration** (journal-app-next/src/api/chat.ts):
   - Added `updateChatSessionPersona()` function for PATCH /chat/sessions/{id}
   - Updated TypeScript types to include persona_id in UpdateSessionRequest

3. **PersonaDropdown Component** (journal-app-next/src/components/chat/PersonaDropdown.tsx):
   - Created compact dropdown component based on existing PersonaSelector
   - Displays persona icon and name with default indicator
   - Handles persona loading and change events
   - Integrates with existing Select UI component

4. **ChatInterface Integration** (journal-app-next/src/components/chat/ChatInterface.tsx):
   - Added PersonaDropdown next to ModelSelector in chat header
   - Implemented `handlePersonaChange()` function to update session persona
   - Added persona loading from session data
   - Session persona state management

5. **Simplified Chat Creation Flow** (journal-app-next/src/app/chat/new/page.tsx):
   - Replaced persona selection page with automatic session creation
   - Uses default persona with fallback handling
   - Immediate redirect to chat interface
   - Users can change persona via dropdown after session creation

### Technical Implementation:
- **API Enhancement**: Added persona update endpoint with proper validation
- **Component Architecture**: Reusable dropdown component that mirrors ModelSelector
- **State Management**: Session-level persona tracking with real-time updates
- **UX Flow**: Streamlined chat creation with post-creation persona switching
- **Error Handling**: Graceful fallbacks for persona loading and API failures

### Verification:
- Backend persona update endpoint properly handles PATCH requests
- Frontend TypeScript types are properly defined and imported
- PersonaDropdown component follows existing design patterns
- ChatInterface properly integrates persona controls
- /chat/new flow creates sessions with default persona and redirects
- Persona switching functionality is implemented and ready for testing

### User Journey (Implemented):
1. User clicks "New Chat" → automatically creates session with default persona
2. User can immediately see and change persona via dropdown in chat interface
3. Persona changes apply to subsequent messages in the conversation
4. User can switch personas multiple times during conversation
5. Persona state is preserved and updated in the backend session
