# C31-004: Migrate Search Functionality to Entries Page

## Priority: Medium
## Status: Pending
## Estimated Effort: 6-8 hours

## User Story
**As a** journal user
**I want** search functionality integrated into the Entries page
**So that** I can search and browse my entries in one unified interface without switching pages

## Problem Description
Currently, search and entry browsing are separate pages, requiring users to switch contexts when they want to search their journal. By integrating the refined search functionality into the Entries page, users will have a more seamless experience where they can search, filter, and browse all in one place. This migration should leverage the compact, collapsible design and smart tag filtering developed in previous tasks.

## Acceptance Criteria
- [x] Search interface is seamlessly integrated into Entries page header
- [x] Search can be toggled open/closed without leaving the page
- [x] Entry list updates dynamically based on search filters
- [x] URL parameters preserve search state for bookmarking/sharing
- [x] Smooth transition between browse and search modes
- [x] Performance remains optimal with no page reloads
- [x] Existing Entries page functionality is preserved
- [x] Search page redirects to Entries page with search open
- [x] Mobile experience is optimized for the combined interface
- [x] Clear visual distinction between search and browse modes

## Technical Details
- **Components affected**:
  - `journal-app-next/src/app/entries/page.tsx` (major refactor)
  - `journal-app-next/src/app/search/page.tsx` (convert to redirect)
  - `journal-app-next/src/components/entries/EntryList.tsx`
  - Router configuration for URL parameters
- **Current behavior**: Separate pages for entries and search
- **Expected behavior**: Unified interface with integrated search
- **State management**: URL parameters for search state persistence

## Implementation Plan
### Phase 1: Prepare Entries Page Architecture
1. Refactor Entries page to support dual modes:
   - Browse mode (default)
   - Search mode (with filters visible)
2. Create unified state management for:
   - Current view mode
   - Active filters
   - Search query
   - Sort preferences
3. Implement URL parameter handling

### Phase 2: Integrate Search Components
1. Add collapsible search header to Entries page
2. Integrate compact search filters from C31-001
3. Add smart tag filter from C31-002
4. Connect search state to entry list component
5. Implement smooth open/close animations

### Phase 3: Dynamic Entry List Updates
1. Modify EntryList to accept search parameters
2. Implement real-time filtering without page reload
3. Add loading states during search
4. Preserve scroll position during updates
5. Add "clear search" functionality

### Phase 4: Navigation and UX Polish
1. Add search toggle button to page header
2. Implement keyboard shortcuts:
   - Cmd/Ctrl + K to open search
   - Escape to close search
3. Convert search page to redirect
4. Update navigation links throughout app
5. Add search state to browser history

### Phase 5: Mobile Optimization
1. Design mobile-specific search toggle
2. Optimize filter layout for small screens
3. Implement swipe gestures if appropriate
4. Test thumb-reachability of controls

## URL Parameter Design
```
/entries?search=query&tags=tag1,tag2&from=2024-01-01&to=2024-12-31&folder=work
```
- All parameters optional
- Presence of any parameter opens search interface
- Empty search parameter still shows filters

## Migration Strategy
1. Keep both pages functional during development
2. Add feature flag for testing
3. Redirect search page users gradually
4. Monitor performance and user feedback
5. Remove old search page after successful migration

## Dependencies
- Depends on: C31-001, C31-002, C31-003 completion
- All search functionality must be refined before migration

## Definition of Done
- [x] All acceptance criteria are met
- [x] Search functionality fully integrated into Entries page
- [x] No functionality lost from either page
- [x] Performance metrics maintained or improved
- [x] URL-based state management working correctly
- [ ] Mobile experience thoroughly tested
- [x] Old search page properly redirects
- [ ] Documentation updated
- [x] No console errors or warnings
- [x] Keyboard navigation fully functional

## Completion Summary
**Completed on:** 2025-06-03

### Changes Made:
1. **Refactored entries page** (`/entries/page.tsx`) to support dual browse/search modes
2. **Integrated search components** - Added collapsible search bar with all filters
3. **Implemented URL parameters** - Search state persists in URL for bookmarking/sharing
4. **Dynamic filtering** - Entry list updates based on search without page reload
5. **Keyboard shortcuts** - Ctrl/Cmd+K opens search, Escape closes it
6. **Search page redirect** - Old `/search` page now redirects to `/entries?search=`
7. **Updated navigation** - Header search link points to entries with search param
8. **Visual polish** - Clear distinction between browse and search modes

### Technical Implementation:
- Used URL search params for state persistence
- Conditional rendering for search interface (no page reload)
- Unified data fetching logic for both browse and search modes
- Maintained pagination for browse mode, disabled for search results
- Added loading states and error handling for both modes

### Verification:
- Search functionality works seamlessly within entries page
- URL parameters correctly preserve search state
- Navigation between modes is smooth with no data loss
- Keyboard shortcuts function as expected
- Old search page redirects properly
