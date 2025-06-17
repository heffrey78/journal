# C33-001: Web Search Tool Integration

## Priority: High
## Status: Completed
## Estimated Effort: 6 hours

## User Story
**As a** journal user
**I want** to search the web for information during chat conversations
**So that** I can get current information and enrich my journal entries with external knowledge

## Problem Description
Currently, the chat system can only search within journal entries. Users often need to reference current events, look up facts, or research topics that aren't in their journal. Adding web search capabilities would make the chat assistant more useful for research and fact-checking.

## Acceptance Criteria
- [x] Implement DuckDuckGo search tool that integrates with existing tool framework
- [x] Add configurable settings for web search in the settings panel
- [x] Tool triggers intelligently when users ask about external information
- [x] Search results are displayed clearly with source attribution
- [x] Users can enable/disable web search functionality
- [x] Search API keys/endpoints are configurable (for future extensibility)
- [x] Rate limiting is implemented to prevent abuse
- [x] Search results include title, snippet, and URL
- [x] Frontend displays web search activity in tool indicators

## Technical Details

### Files to be created:
- `app/tools/web_search.py` - DuckDuckGo search tool implementation
- `journal-app-next/src/components/settings/WebSearchSettings.tsx` - Settings UI component

### Files to be modified:
- `app/models.py` - Add WebSearchConfig model
- `app/storage/config.py` - Add web search configuration storage
- `app/tools/__init__.py` - Export new web search tool
- `app/chat_service.py` - Register web search tool
- `app/config_routes.py` - Add web search config endpoints
- `journal-app-next/src/app/settings/page.tsx` - Include web search settings
- `journal-app-next/src/components/chat/ToolUsageIndicator.tsx` - Add web search icon
- `journal-app-next/src/config/api.ts` - Add web search config endpoints

### Implementation approach:
1. Create WebSearchTool class that extends BaseTool
2. Use duckduckgo-search Python library for backend
3. Implement intelligent triggering based on question patterns
4. Add configuration model for enabling/disabling and setting limits
5. Create settings UI with toggle and rate limit configuration
6. Ensure proper error handling for network failures
7. Add caching to avoid duplicate searches

### Key features:
- **Smart triggering**: Detects questions about current events, facts, definitions
- **Rate limiting**: Configurable requests per minute/hour
- **Result formatting**: Clean presentation of search results
- **Privacy focused**: DuckDuckGo doesn't track users
- **Extensible**: Easy to add other search providers later

## Definition of Done
- [x] DuckDuckGo search tool is fully implemented
- [x] Settings panel allows enabling/disabling web search
- [x] Rate limiting is configurable and enforced
- [x] Tool triggers appropriately for web search queries
- [x] Search results are displayed in chat with proper attribution
- [x] Tool usage indicators show web search activity
- [x] Error handling for network issues is implemented
- [x] Tests are written for the web search tool
- [x] Documentation is updated

## Completion Summary
**Completed on:** 2025-01-06

### Changes Made:

#### Backend Implementation:
1. **WebSearchTool class** (`app/tools/web_search.py`)
   - Implemented DuckDuckGo integration using `duckduckgo-search` library
   - Added intelligent triggering based on message patterns
   - Implemented rate limiting and caching mechanisms
   - Added support for general and news searches

2. **WebSearchConfig model** (`app/models.py`)
   - Configuration model for web search settings
   - Includes enabled/disabled flag, rate limits, and regional settings

3. **Configuration storage** (`app/storage/config.py`)
   - Added database table and methods for web search config
   - Integrated with existing ConfigStorage system

4. **Tool registration** (`app/chat_service.py`)
   - Updated ChatService to register and initialize WebSearchTool
   - Added config storage access for tool configuration

5. **API endpoints** (`app/config_routes.py`)
   - Added GET and PUT endpoints for web search configuration
   - Integrated with FastAPI router system

#### Frontend Implementation:
1. **Tool indicator** (`ToolUsageIndicator.tsx`)
   - Added Globe icon and display name for web search tool
   - Shows search activity and results in chat interface

2. **Settings component** (`WebSearchSettings.tsx`)
   - Comprehensive settings UI for web search configuration
   - Rate limiting, region selection, and feature toggles
   - Real-time config saving with feedback

3. **Settings integration** (`app/settings/page.tsx`)
   - Added new "Tools" tab in settings page
   - Integrated WebSearchSettings component

4. **API configuration** (`config/api.ts`)
   - Added web search config endpoint constants

### Verification:
- All acceptance criteria have been met
- Web search tool integrates with existing tool framework
- Settings are persisted and configurable
- Tool triggers intelligently based on query patterns
- Frontend displays tool activity and allows configuration
- Error handling implemented for network failures

## Future Enhancements
- Add support for Google Custom Search API
- Implement Bing Search API integration
- Add image search capabilities
- Support for scholarly article search
- News-specific search mode
- Local file/document search integration
