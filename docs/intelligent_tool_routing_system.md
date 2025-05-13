# Intelligent Tool Routing System for Chat Interface

## Overview

This document outlines the design and implementation approach for an intelligent tool routing system for the journal application's chat interface. The goal is to move from the current approach (where semantic search runs for every message) to a more flexible and efficient system that classifies user messages and routes them to the appropriate tools only when necessary.

## Current Implementation

Currently, every user message goes through the following process:

1. Frontend sends message to backend via `/chat/messages` endpoint
2. `ChatService.process_message()` or `ChatService.stream_message()` handles the message
3. `_enhanced_entry_retrieval()` is called for every message, which:
   - Always executes semantic search on the full journal corpus
   - Applies date filters when specified
4. The LLM generates a response using the message, conversation history, and retrieved entries
5. Response is sent back to the frontend

**Limitations of Current Approach:**

- Semantic search is executed for every message, regardless of whether it's needed
- No ability to route different types of queries to specialized tools (web search, calendar, etc.)
- Inefficient use of LLM tokens and computational resources
- No mechanism for handling queries that don't require journal context
- Limited flexibility for different query types

## Proposed Tool Routing System

### System Components

1. **Message Classifier**
   - Lightweight LLM classifier that determines message intent
   - Routes messages to appropriate tools based on classification

2. **Tool Registry**
   - Central registry of available tools
   - Each tool provides metadata about its capabilities

3. **Tool Executor**
   - Orchestrates tool execution based on classifier output
   - Handles sequential or parallel tool execution when needed

4. **Response Generator**
   - Formats the outputs from tools into coherent responses
   - Handles citations, references, and structured data

### Available Tools

1. **RAG (Retrieval Augmented Generation) Tool**
   - Uses semantic search to find relevant journal entries
   - Only activated when the message requires personal context

2. **Direct Chat Tool**
   - Handles general conversation without requiring journal context
   - More efficient for simple queries or follow-ups

3. **Web Search Tool** (Future)
   - Searches the web for information not in the journal
   - Used for factual queries or current events

4. **Calendar/Timeline Tool** (Future)
   - Specialized handling of temporal queries
   - More precise date-based filtering and visualization

5. **Insight Generator Tool** (Future)
   - Performs analysis on journal data to generate insights
   - Used for reflection, pattern recognition, and advice

### Message Flow

1. User sends a message
2. Message Classifier determines the intent and required tools
3. Tool Executor activates the appropriate tools
4. Tools process the query and return structured results
5. Response Generator formats a coherent response
6. Response is returned to the user

## Implementation Plan

### Phase 1: Core Tool Routing Infrastructure

1. Create a `ToolRegistry` class to manage available tools
2. Implement base `Tool` abstract class with standard interface
3. Develop `MessageClassifier` to determine message intent
4. Refactor `ChatService` to use the tool routing system
5. Implement initial tools:
   - `RagTool` (wrapper around current semantic search)
   - `DirectChatTool` (chat without retrieval)

### Phase 2: Enhanced Tool Capabilities

1. Improve classification accuracy with feedback mechanism
2. Add tool combination capability for complex queries
3. Implement `WebSearchTool` for external information
4. Develop more sophisticated handling of temporal queries

### Phase 3: Frontend Integration and User Control

1. Update frontend to display tool usage in responses
2. Add user controls to override tool selection
3. Implement UI for tool-specific interactions
4. Develop visualization components for different response types

## Technical Design

### Tool Interface

```python
class Tool:
    """Base class for all tools in the system."""

    @property
    def name(self) -> str:
        """Name of the tool."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Description of what the tool does."""
        raise NotImplementedError

    @property
    def required_capabilities(self) -> List[str]:
        """Capabilities required by this tool."""
        raise NotImplementedError

    def can_handle(self, message: str, metadata: Dict[str, Any]) -> float:
        """
        Determines if this tool can handle the given message.

        Returns a confidence score between 0 and 1.
        """
        raise NotImplementedError

    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool on the given message with context.

        Returns structured output that can be used by the response generator.
        """
        raise NotImplementedError
```

### Message Classifier

```python
class MessageClassifier:
    """
    Classifies messages to determine which tools should handle them.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    async def classify(self, message: str, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Classify a message to determine which tools should handle it.

        Returns a dictionary mapping tool names to confidence scores.
        """
        # Implementation options:
        # 1. Use LLM to classify message intent
        # 2. Use a simpler ML classifier for efficiency
        # 3. Use heuristics for common patterns
        pass
```

### ChatService Integration

The `ChatService.process_message` method would be refactored to:

```python
async def process_message(self, message: ChatMessage) -> Tuple[ChatMessage, List[EntryReference]]:
    """Process a user message using the tool routing system."""

    # Get session and config
    session = self.chat_storage.get_session(message.session_id)
    config = self.chat_storage.get_chat_config()

    # Step 1: Classify the message
    classification = await self.message_classifier.classify(
        message.content,
        {"session": session}
    )

    # Step 2: Select tools based on classification
    selected_tools = self.tool_selector.select_tools(classification)

    # Step 3: Execute the selected tools
    tool_results = await self.tool_executor.execute_tools(
        selected_tools,
        message.content,
        {"session": session, "config": config}
    )

    # Step 4: Generate response from tool outputs
    response_text = await self.response_generator.generate(
        message.content,
        tool_results,
        {"session": session}
    )

    # Step 5: Create and save assistant message (similar to current implementation)
    # ...

    return assistant_message, references
```

## Example Tools

### RAG Tool (Retrieval Augmented Generation)

```python
class RagTool(Tool):
    """Tool for retrieving relevant journal entries and generating responses."""

    @property
    def name(self) -> str:
        return "rag"

    @property
    def description(self) -> str:
        return "Retrieves relevant information from journal entries to answer queries"

    def can_handle(self, message: str, metadata: Dict[str, Any]) -> float:
        # Determine if message needs journal context
        # This could use heuristics or a simple classifier
        return 0.8  # Example confidence score

    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        session = context["session"]
        config = context["config"]

        # This reuses the existing semantic search functionality
        references = self._enhanced_entry_retrieval(message, session, config)
        conversation_history = self._prepare_conversation_history(session.id, config)

        return {
            "references": references,
            "conversation_history": conversation_history
        }
```

### Direct Chat Tool

```python
class DirectChatTool(Tool):
    """Tool for handling general conversation without journal context."""

    @property
    def name(self) -> str:
        return "direct_chat"

    @property
    def description(self) -> str:
        return "Handles general conversation without retrieving journal entries"

    def can_handle(self, message: str, metadata: Dict[str, Any]) -> float:
        # Determine if message is general conversation
        return 0.5  # Lower confidence than RAG for most cases

    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        session = context["session"]
        config = context["config"]

        conversation_history = self._prepare_conversation_history(session.id, config)

        return {
            "references": [],  # No references
            "conversation_history": conversation_history
        }
```

## Frontend Integration

The frontend needs to be updated to:

1. Display which tools were used for each response
2. Allow users to override tool selection if needed
3. Provide tool-specific UI components when appropriate

### Example Response Format

```json
{
  "message_id": "abc123",
  "content": "Your response text here...",
  "tools_used": ["rag", "calendar"],
  "references": [
    { "entry_id": "entry1", "relevance": 0.92, "text": "..." }
  ],
  "metadata": {
    "tool_outputs": {
      "rag": { "reference_count": 3 },
      "calendar": { "events_found": 2, "date_range": "May 2023" }
    }
  }
}
```

## Next Steps and Implementation Roadmap

1. **Month 1**: Design and implement core infrastructure
   - Tool registry and base classes
   - Initial message classifier
   - Integration with ChatService

2. **Month 2**: Implement initial tools
   - RAG Tool (refactored from current semantic search)
   - Direct Chat Tool
   - Unit tests and performance benchmarks

3. **Month 3**: Frontend integration and feedback loop
   - Update ChatInterface.tsx to handle tool-based responses
   - Add tool usage indicators
   - Implement feedback mechanism for classifier improvement

## Conclusion

The intelligent tool routing system will make the chat interface more efficient, flexible, and capable. By only running semantic search when needed and adding support for specialized tools, the system will provide better responses while using fewer resources. This architecture also allows for easy addition of new tools and capabilities in the future.
