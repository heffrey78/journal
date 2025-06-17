# C31-002: Design and Implement Smart Tag Filter System

## Priority: High
## Status: Pending
## Estimated Effort: 8-10 hours

## User Story
**As a** journal user with many tags
**I want** to see only relevant tags when filtering
**So that** I can quickly find and select the tags I need without scrolling through irrelevant options

## Problem Description
Currently, the tag filter shows all tags in the system, which can be overwhelming for users with many tags. A smart tag filter system should intelligently display only relevant tags based on context, search query, date range, and usage patterns. This will significantly improve the search experience and make tag filtering more efficient.

## Acceptance Criteria
- [ ] Tag filter shows contextually relevant tags based on current search criteria
- [ ] Recently used tags appear at the top of the filter
- [ ] Tags are ranked by relevance score considering multiple factors
- [ ] Tag filter updates dynamically as other filters change
- [ ] "Show all tags" option available for users who need it
- [ ] Tag usage statistics are tracked for relevance scoring
- [ ] System handles 1000+ tags efficiently
- [ ] Visual indicators show why tags are suggested (e.g., "Recent", "Frequent", "Related")
- [ ] Tag search/filter within the smart filter works smoothly
- [ ] Performance remains fast even with complex relevance calculations

## Technical Details
- **Components affected**:
  - Create new `SmartTagFilter` component
  - Update `journal-app-next/src/app/search/page.tsx`
  - Add tag relevance API endpoint in `app/api.py`
  - Extend `app/storage/tags.py` with relevance scoring
- **Current behavior**: All tags displayed alphabetically or by frequency
- **Expected behavior**: Intelligent tag filtering based on context and usage
- **Database changes**:
  - Add tag usage tracking table
  - Add last_used timestamp to tag associations
  - Consider adding tag co-occurrence tracking

## Implementation Plan
### Phase 1: Backend Relevance System
1. Design relevance scoring algorithm considering:
   - Recency of use (last 7, 30, 90 days)
   - Frequency of use overall
   - Co-occurrence with selected tags
   - Presence in current search results
   - Date range correlation
2. Implement tag usage tracking in database
3. Create API endpoint for smart tag suggestions
4. Add caching layer for performance

### Phase 2: Smart Filtering Algorithm
1. Implement relevance factors:
   - **Recency Score**: Tags used in last N days get higher scores
   - **Frequency Score**: Overall usage frequency
   - **Context Score**: Tags appearing in current filtered entries
   - **Co-occurrence Score**: Tags often used together with selected tags
   - **Search Query Match**: Tags matching search terms
2. Create weighted scoring system with tunable parameters
3. Implement threshold for minimum relevance score

### Phase 3: Frontend Integration
1. Build SmartTagFilter component with:
   - Relevant tags section (top 10-20)
   - Recent tags section (last 5-10 used)
   - Search within tags functionality
   - "Show all" toggle
2. Add visual indicators for tag relevance reason
3. Implement smooth loading and update animations
4. Add empty states and helpful prompts

### Phase 4: Performance Optimization
1. Implement efficient caching strategy
2. Add debouncing for dynamic updates
3. Use virtual scrolling for large tag lists
4. Optimize database queries with proper indexing

## Smart Tag Relevance Algorithm Design
```
relevance_score = (
    recency_weight * recency_score +
    frequency_weight * frequency_score +
    context_weight * context_score +
    cooccurrence_weight * cooccurrence_score +
    search_match_weight * search_match_score
)

Where:
- recency_score: 1.0 for today, decaying over time
- frequency_score: normalized usage count (0-1)
- context_score: % of filtered entries containing tag
- cooccurrence_score: correlation with selected tags
- search_match_score: fuzzy match with search query
```

## Dependencies
- Should be implemented after C31-001 to work with new compact design
- Will enhance the search experience before migration to Entries page

## Definition of Done
- [ ] All acceptance criteria are met
- [ ] Smart tag filtering improves tag selection time by at least 50%
- [ ] System handles 1000+ tags without performance degradation
- [ ] Tag relevance updates within 100ms of filter changes
- [ ] Usage tracking is accurate and efficient
- [ ] API tests cover all relevance factors
- [ ] Frontend tests verify dynamic updates
- [ ] Documentation includes relevance algorithm explanation
- [ ] Settings allow users to customize relevance weights
