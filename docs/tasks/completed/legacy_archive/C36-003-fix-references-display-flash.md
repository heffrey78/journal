# C36-003: Fix References Display Flash and Disappear Issue

## Priority: Medium
## Status: Pending
## Estimated Effort: 2-3 hours

## User Story
**As a** chat user
**I want** references to display consistently when they are returned with chat responses
**So that** I can reliably see the journal entries that informed the AI's response

## Problem Description
When a chat response includes references for the first time in a session, the references may briefly flash on screen but then disappear. However, subsequent chat replies with references display properly, and if the page is refreshed, the references appear correctly below the reply.

This suggests a frontend rendering or state management issue where the initial references are not being properly persisted or displayed in the component state.

## Acceptance Criteria
- [ ] References display consistently on first appearance in a chat session
- [ ] No flashing or disappearing behavior when references are first shown
- [ ] References remain visible after initial display
- [ ] Behavior is consistent across page refreshes and new sessions
- [ ] References display correctly for both streaming and non-streaming responses
- [ ] No regression in existing reference display functionality
- [ ] Manual testing confirms stable reference display in various scenarios
- [ ] Component state properly manages references through the entire chat session

## Technical Details
- **Components affected**:
  - `journal-app-next/src/components/chat/ChatMessage.tsx`
  - `journal-app-next/src/components/chat/EntryReferences.tsx`
  - `journal-app-next/src/components/chat/ChatInterface.tsx`
  - `journal-app-next/src/api/chat.ts` (if related to API response handling)

- **Current behavior**: References flash and disappear on first display, work properly on subsequent displays and after page refresh
- **Expected behavior**: References display consistently and remain visible from first appearance

- **Suspected causes**:
  - Component re-rendering causing references to be cleared
  - State management issue with references not being properly persisted
  - Race condition between message display and references loading
  - CSS/styling issue causing references to be temporarily hidden

## Investigation Steps
1. Review ChatMessage component for state management of references
2. Check if references are being properly passed as props and maintained
3. Investigate component lifecycle and re-rendering behavior
4. Test reference display with both streaming and non-streaming chat modes
5. Check browser console for any errors during reference display
6. Compare working behavior (after refresh) with failing behavior (first display)

## Root Cause Analysis Required
- **Component State**: Verify references are properly stored in component state
- **Props Handling**: Ensure references props are not being cleared or overwritten
- **Rendering Logic**: Check if conditional rendering logic is causing disappearance
- **API Integration**: Verify references are consistently received from backend
- **CSS/Styling**: Rule out visibility issues caused by styling conflicts

## Definition of Done
- [ ] All acceptance criteria are met
- [ ] References display consistently across all scenarios
- [ ] No flashing or disappearing behavior
- [ ] Code follows project conventions
- [ ] Manual testing confirms fix across different browsers
- [ ] No performance regression in chat interface
- [ ] Code has been reviewed
- [ ] No linting errors
- [ ] Feature works in both development and production modes
