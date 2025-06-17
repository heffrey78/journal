# C36-006: Improve Search Result UI and Information Display

## Priority: Medium
## Status: Completed
## Estimated Effort: 3-4 hours

## User Story
**As a** journal user using chat functionality
**I want** to see meaningful titles and clickable links for search results
**So that** I can quickly identify and access relevant entries and web resources

## Problem Description
Currently, search results in chat tool notifications have two significant UI issues:

1. **Web Search Results**: Tool notifications don't display clickable links, making it difficult to access the actual web sources that were found
2. **Journal Search Results**: All journal entries show generic "Journal Entry" titles instead of their actual titles, obscuring important information about content (e.g., "Favorite Books" shows as just "Journal Entry")

These issues reduce the usefulness of search results by hiding important identifying information and making resources harder to access.

## Acceptance Criteria
- [x] Web search tool notifications display clickable links to actual web sources
- [x] Journal search results show actual entry titles instead of generic "Journal Entry"
- [x] Web search result links open in new tabs/windows
- [x] Journal entry titles are properly escaped and formatted for display
- [x] Tool notification UI remains clean and readable with the additional information
- [x] Changes work consistently across all personas and chat interfaces
- [x] Tests verify proper title extraction and link formatting
- [x] No performance impact on chat interface rendering

## Technical Details
- **Components affected**:
  - `journal-app-next/src/components/chat/ToolUsageIndicator.tsx`
  - `journal-app-next/src/components/chat/ChatMessage.tsx`
  - `app/tools/journal_search.py`
  - `app/tools/web_search.py`
  - `app/chat_service.py` (tool result formatting)

- **Current behavior**:
  - Web search shows "Found X results" without links
  - Journal search shows "Journal Entry" for all results regardless of actual title

- **Expected behavior**:
  - Web search shows "Found X results" with expandable/clickable links
  - Journal search shows actual entry titles (e.g., "Favorite Books", "Daily Reflection", etc.)

- **Frontend changes**: Enhance ToolUsageIndicator to display rich result information
- **Backend changes**: Ensure proper title extraction and metadata inclusion in tool results

## Implementation Plan

### Phase 1: Fix Journal Entry Titles
1. Investigate how journal entry titles are extracted in `journal_search.py`
2. Ensure actual entry titles are included in tool results metadata
3. Update frontend components to display actual titles instead of generic text
4. Test with various entry types (imported docs, manual entries, etc.)

### Phase 2: Add Web Search Links
1. Modify web search tool results to include URLs in metadata
2. Update ToolUsageIndicator to render clickable links for web results
3. Implement proper link formatting (new tab, security attributes)
4. Add UI for expanding/collapsing long lists of results

### Phase 3: Polish and Testing
1. Ensure consistent styling across both result types
2. Test with various result counts (1, 5, 10+ results)
3. Verify accessibility for screen readers
4. Test link security and proper handling of malformed URLs

## Dependencies
- None (independent improvement)

## Completion Summary
**Completed on:** 2025-06-08

### Changes Made:
1. **Enhanced ToolUsage Interface** (`journal-app-next/src/components/chat/types.ts`):
   - Added `results` array to ToolUsage interface
   - Added ToolResult interface to describe individual result structure
   - Support for both journal search and web search result types

2. **Updated Chat Service** (`app/chat_service.py`):
   - Modified both `save_message` and `stream_message` functions
   - Added logic to include actual tool result data in metadata
   - Results are now passed to frontend for enhanced display

3. **Redesigned ToolUsageIndicator** (`journal-app-next/src/components/chat/ToolUsageIndicator.tsx`):
   - Split into multiple components: ToolResultCard and ToolResults
   - Added collapsible/expandable result display
   - Journal search results show actual entry titles instead of "Journal Entry"
   - Web search results display clickable links that open in new tabs
   - Added proper security attributes for external links (noopener, noreferrer)
   - Limited display to first 5 results with "more results" indicator

4. **UI/UX Improvements**:
   - Tool notifications remain clean and compact by default
   - Users can expand to see detailed results when needed
   - Clickable web links with external link icons
   - Proper hover states and accessibility features

### Verification:
- Created and ran comprehensive test to verify data flow
- All tool result data properly flows from backend to frontend
- Journal entries show actual titles (e.g., "My Daily Reflection", "Weekend Project Notes")
- Web search results display as clickable links
- Tool notifications remain visually clean and functional
- Links open safely in new tabs with proper security attributes

## Definition of Done
- [x] All acceptance criteria are met
- [x] Code follows project conventions
- [x] Frontend components properly handle both web and journal results
- [x] Backend tool results include necessary metadata
- [x] No regressions in existing tool functionality
- [x] Changes tested with multiple personas
- [x] Tool notifications remain visually clean and functional
- [x] Links open safely in new tabs
- [x] Journal entry titles are properly extracted and displayed
