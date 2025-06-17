# C35-001: Create Chat Personas Data Model

## Priority: High
## Status: Completed
## Estimated Effort: 2-3 hours

## User Story
**As a** journal user
**I want** to define and store different chat personas
**So that** I can have conversations with different AI personalities suited to different purposes

## Problem Description
Currently, the chat feature uses a single system prompt for all conversations. Users would benefit from having multiple personas available, each with their own specialized system prompt and characteristics. This would allow users to switch between different AI personalities like a "Coach", "Journaling Assistant", or "Story Teller" depending on their needs.

## Acceptance Criteria
- [x] Database schema includes a personas table with id, name, description, system_prompt, and icon fields
- [x] Persona model created in app/models.py with proper validation
- [x] Storage module created for persona CRUD operations
- [x] Default personas are seeded on first run (Coach, Journaling Assistant, Story Teller)
- [x] API endpoints for listing and managing personas
- [x] Tests written for persona storage and API endpoints

## Technical Details
- **Components affected**:
  - `app/models.py` - Add Persona and PersonaCreate/Update models
  - `app/storage/personas.py` - New storage module for personas
  - `app/api.py` - Add persona management endpoints
  - Database schema migration needed
- **Current behavior**: Single system prompt for all chats
- **Expected behavior**: Multiple personas available with custom system prompts
- **Database changes**: New personas table with foreign key from chat_sessions

## Implementation Plan
### Phase 1: Data Model and Storage
1. Create personas table schema
2. Implement Persona pydantic models
3. Create PersonaStorage class
4. Add default personas seeding

### Phase 2: API Integration
1. Add GET /api/personas endpoint
2. Add POST/PUT/DELETE endpoints for persona management
3. Update chat session creation to include persona_id

## Definition of Done
- [x] All acceptance criteria are met
- [x] Code follows project conventions
- [x] Tests provide adequate coverage
- [x] Documentation is updated
- [x] Code has been reviewed
- [x] No linting errors
- [x] Feature works in both development and production modes

## Completion Summary
**Completed on:** 2025-01-07

### Changes Made:
- Created Persona, PersonaCreate, and PersonaUpdate Pydantic models in `app/models.py`
- Added persona_id field to ChatSession model
- Implemented PersonaStorage class in `app/storage/personas.py` with full CRUD operations
- Updated ChatStorage to support persona_id in chat sessions
- Added personas table with database schema migration support
- Seeded 5 default personas: Journaling Assistant, Coach, Story Teller, Therapist, Productivity Partner
- Created comprehensive API endpoints for persona management in `app/api.py`
- Implemented proper validation and error handling for persona operations

### Verification:
- All acceptance criteria implemented and verified
- Comprehensive test suite created and passing (test_personas.py)
- Default personas automatically seeded on first database initialization
- API endpoints tested for all CRUD operations
- Database migration handling for existing installations
- Proper foreign key relationships established

### Technical Impact:
- Database schema extended with personas table and chat_sessions.persona_id
- Clean separation of concerns with dedicated PersonaStorage class
- RESTful API design following existing project patterns
- Backward compatibility maintained for existing chat sessions
