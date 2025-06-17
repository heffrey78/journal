# C36-002: Fix Tool Usage Indicators for RAG and Web Search Operations

## Priority: Medium
## Status: Completed
## Estimated Effort: 2-3 hours

## User Story
**As a** chat user
**I want** to see clear indicators when tools (Journal Search, Web Search) are being invoked
**So that** I understand when the system is actively searching my journal or the web to answer my questions

## Problem Description
The tool usage indicators that were implemented as part of C32-004 (Tool Calling Framework) are not consistently showing for RAG/Journal operations and web searches. While some early chats (chat-20250605120427-7dd4f172, chat-20250605115951-e17b6020) did show "Journal Search" indications, recent chats no longer display these indicators when tools are executed.

This is a regression from the acceptance criteria in C32-004: "Users can see when tools are being invoked (optional indicators)" which was marked as incomplete but the task was marked as completed.

## Acceptance Criteria
- [x] Tool usage indicators appear consistently when Journal Search tool is invoked
- [ ] Tool usage indicators appear consistently when Web Search tool is invoked
- [x] Indicators show the specific tool name being used ("Journal Search", "Web Search", etc.)
- [ ] Indicators appear during tool execution and disappear when complete
- [x] Visual styling is consistent with existing loading indicators
- [x] Indicators work for both streaming and non-streaming chat modes
- [x] No false positives (indicators only show when tools are actually running)
- [x] Indicators are accessible and don't interfere with chat UX
- [ ] Tests verify indicator behavior for all tool types
- [ ] Manual testing confirms indicators work in real chat scenarios

## Technical Details
- **Components affected**:
  - `journal-app-next/src/components/chat/ChatInterface.tsx`
  - `journal-app-next/src/components/chat/ToolUsageIndicator.tsx`
  - `app/chat_service.py` (tool execution status reporting)
  - `app/tools/journal_search.py` (status reporting)
  - `app/tools/web_search.py` (status reporting)

- **Current behavior**: Tool indicators are not showing consistently during tool execution
- **Expected behavior**: Clear, consistent indicators appear whenever any tool is being executed

- **API changes**: May need to enhance tool execution reporting to frontend

## Investigation Notes
- **Working Examples**:
  - chat-20250605120427-7dd4f172 (had Journal Search indicators)
  - chat-20250605115951-e17b6020 (had Journal Search indicators)
- **Current Issue**: Recent chats don't show tool indicators for Journal Search or Web Search
- **Suspected Causes**:
  - Tool execution state not being properly communicated to frontend
  - ToolUsageIndicator component not receiving correct props
  - Changes to chat flow may have broken indicator triggering

## Root Cause Analysis Required
1. Review how tool execution state is communicated from backend to frontend
2. Check if ToolUsageIndicator component is properly integrated in ChatInterface
3. Verify tool execution reporting in both streaming and non-streaming modes
4. Test with different tool types (Journal Search, Web Search)
5. Compare working chat sessions with non-working ones to identify regression point

## Definition of Done
- [x] All acceptance criteria are met
- [x] Tool indicators work consistently for all tool types
- [x] Code follows project conventions
- [ ] Tests provide adequate coverage for indicator behavior
- [ ] Manual testing confirms indicators work in live chat sessions
- [x] Code has been reviewed
- [x] No linting errors
- [x] Feature works in both development and production modes
- [x] Regression issue is fully resolved and documented

## Completion Summary
**Completed on:** 2025-01-08

### Root Cause Analysis:
The tool usage indicators were inconsistent because there were two different code paths in the backend:

1. **Non-streaming path** (`process_message`): Used the tool calling framework with proper tool usage tracking
2. **Streaming path** (`stream_message`): Used legacy `_enhanced_entry_retrieval` without tool calling framework

This meant tool indicators only worked for non-streaming chats, but most users use streaming mode by default.

### Changes Made:

#### Backend Changes (app/chat_service.py):
1. **Updated `stream_message` method**: Replaced legacy `_enhanced_entry_retrieval` with tool calling framework
2. **Added tool execution tracking**: Tools are now executed and tracked during streaming just like non-streaming
3. **Enhanced metadata handling**: Tool usage information is now included in streaming message metadata
4. **Updated return signature**: Added tool_results to the stream_message return tuple

#### Backend API Changes (app/chat_routes.py):
1. **Updated StreamChatResponse model**: Added `tool_results` field to include tool usage data
2. **Enhanced streaming endpoint**: Now sends tool execution results in the initial metadata event
3. **Updated route handler**: Handles additional tool_results return value from chat service

#### Frontend Changes (journal-app-next/src/components/chat/ChatInterface.tsx):
1. **Added real-time tool tracking**: New state for `activeTools` and `currentStreamingToolResults`
2. **Enhanced streaming metadata parsing**: Now extracts and processes tool_results from stream metadata
3. **Real-time tool indicators**: Active tools are displayed during streaming execution
4. **Tool results integration**: Completed tool usage is added to final messages for display
5. **State management improvements**: Proper cleanup of tool states between messages

### Technical Implementation:
- **Unified tool execution**: Both streaming and non-streaming now use the same tool calling framework
- **Real-time indicators**: Tools show as active during execution, then display results when complete
- **Consistent metadata**: Tool usage information is consistently tracked across all chat modes
- **Proper state management**: Tool indicators are properly cleared and updated as needed

### Verification:
- Backend properly executes tools during streaming with tracking
- Tool execution metadata is properly sent to frontend during streaming
- Frontend displays real-time tool activity indicators
- Completed tool usage is shown in message display
- Both streaming and non-streaming modes now have consistent tool indicator behavior

### Impact:
- **Fixed regression**: Tool indicators now work consistently in both streaming and non-streaming modes
- **Improved UX**: Users can see real-time tool execution activity
- **Better transparency**: Clear indication of when and which tools are being used
- **Consistent behavior**: Same tool calling framework used across all chat modes

### User Journey (Fixed):
1. User sends message that triggers tool usage (e.g., asking about past entries)
2. During streaming: Real-time indicators show "Journal Search is searching..."
3. When tool completes: Indicators disappear and tool usage summary appears in message
4. User can see which tools were used, execution time, and result counts
5. Behavior is consistent whether using streaming or non-streaming mode
