# C36-005: Fix Web Search Not Executing and LLM Hallucination

## Priority: High
## Status: Completed
## Estimated Effort: 1 hour

## User Story
**As a** chat user
**I want** web search to execute when I ask general knowledge questions
**So that** I get accurate, factual information instead of hallucinated responses

## Problem Description
The web search tool was not executing when users asked general knowledge questions, causing the LLM to hallucinate responses instead of searching the web for accurate information. This is a critical issue that undermines trust in the system.

## Root Cause
The web search tool was properly registered in the ChatService, but the LLM's tool analysis prompt only mentioned `journal_search` and not `web_search`. This meant the LLM never recommended using web search, even for obvious general knowledge queries.

## Acceptance Criteria
- [x] Web search tool is recognized by the LLM tool selector
- [x] General knowledge questions trigger web search
- [x] Web search results are properly formatted in responses
- [x] LLM uses web search results instead of hallucinating
- [x] System prompt emphasizes using actual search results

## Technical Details
- **Files affected**:
  - `app/llm_service.py` - Tool analysis and response synthesis

- **Current behavior**: LLM never recommends web search, hallucinating answers
- **Expected behavior**: LLM uses web search for factual queries and cites sources

## Changes Made

### 1. Updated Tool Analysis Prompt (app/llm_service.py)
Added web_search to the available tools list in `analyze_message_for_tools`:
- Listed web_search with clear description of when to use it
- Added guidelines for choosing between journal_search and web_search
- Allowed for both tools to be recommended when appropriate

### 2. Enhanced Web Search Result Formatting (app/llm_service.py)
In `synthesize_response_with_tools`, added proper formatting for web search results:
- Displays search results with title, source, snippet, and URL
- Makes results easy for LLM to parse and cite

### 3. Updated System Prompt (app/llm_service.py)
Enhanced the response synthesis prompt to:
- Mention web search capability
- Emphasize using actual search results
- Explicitly instruct not to hallucinate information
- Require citing sources from web search results

## Verification
To verify the fix works:
1. Ask general knowledge questions (e.g., "What is the capital of France?")
2. Check that web search tool indicator appears
3. Verify response cites web sources instead of hallucinating
4. Test with current events questions that require web search

## Impact
- **Accuracy**: Responses now based on real web search results
- **Trust**: Users can rely on factual information with sources
- **Transparency**: Tool indicators show when web search is used
- **Reduced Hallucination**: LLM explicitly instructed to use search results

## Completion Summary
**Completed on:** 2025-01-08

The fix was straightforward - the web search tool was fully implemented and working, but the LLM simply didn't know it existed. By updating the tool selection prompt and response synthesis logic, web search now executes properly for general knowledge queries, preventing hallucination and providing accurate, sourced information.
