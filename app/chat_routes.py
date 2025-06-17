"""
API routes for chat functionality.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.models import (
    ChatSession,
    ChatMessage,
    ChatConfig,
    EntryReference,
    ChatSearchResult,
    MessageSearchResult,
    PaginatedSearchResults,
)
from app.storage.chat import ChatStorage
from app.chat_service import ChatService
from app.llm_service import LLMService, CUDAError, CircuitBreakerOpen
from app.utils import get_storage, get_llm_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatSessionCreate(BaseModel):
    """Model for creating a new chat session."""

    title: Optional[str] = None
    temporal_filter: Optional[str] = None
    model_name: Optional[str] = None
    persona_id: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    """Model for updating an existing chat session."""

    title: Optional[str] = None
    context_summary: Optional[str] = None
    temporal_filter: Optional[str] = None
    persona_id: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """Model for creating a new chat message."""

    content: str = Field(
        ..., min_length=1, description="The message content (cannot be empty)"
    )
    model_name: Optional[str] = None  # Optional model override for this message

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Model for chat message responses with optional references."""

    message: ChatMessage
    references: Optional[List[EntryReference]] = None


class ChatResponseWithReferences(BaseModel):
    """Model for chat responses with references included."""

    message: ChatMessage
    references: List[EntryReference] = []


class StreamChatResponse(BaseModel):
    """Model for streaming chat response metadata."""

    message_id: str
    references: List[EntryReference] = []
    tool_results: List[Dict[str, Any]] = []


class PaginatedChatSessions(BaseModel):
    """Model for paginated chat sessions response."""

    sessions: List[ChatSession]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


class LazySessionCreateRequest(BaseModel):
    """Model for creating a session with the first message atomically."""

    message_content: str = Field(
        ..., min_length=1, description="The first message content (cannot be empty)"
    )
    session_title: Optional[str] = None
    temporal_filter: Optional[str] = None
    model_name: Optional[str] = None
    persona_id: Optional[str] = None

    @field_validator("message_content")
    @classmethod
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


@chat_router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate, storage=Depends(get_storage)
) -> ChatSession:
    """
    Create a new chat session.

    Args:
        session_data: Data for the new session

    Returns:
        The created ChatSession
    """
    try:
        # Create a new chat session with current timestamp
        chat_storage = ChatStorage(storage.base_dir)
        now = datetime.now()

        # Generate a default title if none provided
        title = session_data.title or f"Chat on {now.strftime('%B %d, %Y at %H:%M')}"

        # Create the session object
        session = ChatSession(
            title=title,
            created_at=now,
            updated_at=now,
            last_accessed=now,
            temporal_filter=session_data.temporal_filter,
            model_name=session_data.model_name,
            persona_id=session_data.persona_id,
        )

        # Save in database
        created_session = chat_storage.create_session(session)
        logger.info(f"Created new chat session: {created_session.id}")

        return created_session
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create chat session: {str(e)}"
        )


@chat_router.get("/sessions", response_model=PaginatedChatSessions)
async def list_chat_sessions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query(
        "last_accessed",
        description="Field to sort by (last_accessed, updated_at, created_at, title)",
    ),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    storage=Depends(get_storage),
) -> PaginatedChatSessions:
    """
    List existing chat sessions with pagination and sorting.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')

    Returns:
        Paginated response with ChatSession objects and metadata
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Get total count and sessions
        total_count = chat_storage.count_sessions()
        sessions = chat_storage.list_sessions(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )

        # Calculate pagination metadata
        has_next = offset + limit < total_count
        has_previous = offset > 0

        return PaginatedChatSessions(
            sessions=sessions,
            total=total_count,
            limit=limit,
            offset=offset,
            has_next=has_next,
            has_previous=has_previous,
        )
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list chat sessions: {str(e)}"
        )


@chat_router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> ChatSession:
    """
    Get a specific chat session by ID.

    Args:
        session_id: The ID of the chat session to retrieve

    Returns:
        The ChatSession object if found
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        session = chat_storage.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Update last accessed time
        session.last_accessed = datetime.now()
        chat_storage.update_session(session)

        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat session: {str(e)}"
        )


@chat_router.patch("/sessions/{session_id}", response_model=ChatSession)
async def update_chat_session(
    update_data: ChatSessionUpdate,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> ChatSession:
    """
    Update an existing chat session.

    Args:
        update_data: Data to update in the session
        session_id: The ID of the chat session to update

    Returns:
        The updated ChatSession
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Get existing session
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Update fields that are present in the request
        if update_data.title is not None:
            session.title = update_data.title

        if update_data.context_summary is not None:
            session.context_summary = update_data.context_summary

        if update_data.temporal_filter is not None:
            session.temporal_filter = update_data.temporal_filter

        if update_data.persona_id is not None:
            session.persona_id = update_data.persona_id

        # Update timestamps
        session.updated_at = datetime.now()
        session.last_accessed = datetime.now()

        # Save changes
        updated_session = chat_storage.update_session(session)
        logger.info(f"Updated chat session: {session_id}")

        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update chat session: {str(e)}"
        )


@chat_router.patch("/sessions/{session_id}/title", response_model=ChatSession)
async def update_session_title(
    title_data: Dict[str, str],
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> ChatSession:
    """
    Update the title of a chat session (manual override for auto-generated titles).

    Args:
        title_data: Dictionary containing the new title
        session_id: The ID of the chat session to update

    Returns:
        The updated ChatSession
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Get existing session
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Extract title from request data
        new_title = title_data.get("title")
        if not new_title:
            raise HTTPException(status_code=400, detail="Title is required")

        # Update the title
        session.title = new_title.strip()
        session.updated_at = datetime.now()
        session.last_accessed = datetime.now()

        # Save changes
        updated_session = chat_storage.update_session(session)
        logger.info(f"Updated title for session {session_id}: '{new_title}'")

        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session title: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update session title: {str(e)}"
        )


@chat_router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> Dict[str, Any]:
    """
    Delete a chat session and all its messages.

    Args:
        session_id: The ID of the chat session to delete

    Returns:
        Status message
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Delete the session
        success = chat_storage.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete chat session {session_id}"
            )

        logger.info(f"Deleted chat session: {session_id}")
        return {
            "status": "success",
            "message": f"Chat session {session_id} deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chat session: {str(e)}"
        )


@chat_router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> List[ChatMessage]:
    """
    Get all messages for a specific chat session.

    Args:
        session_id: The ID of the chat session

    Returns:
        List of ChatMessage objects in chronological order
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get messages
        messages = chat_storage.get_messages(session_id)

        # Update last accessed time
        session.last_accessed = datetime.now()
        chat_storage.update_session(session)

        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat messages: {str(e)}"
        )


@chat_router.post("/sessions/{session_id}/messages", response_model=ChatMessage)
async def add_message(
    message_data: ChatMessageCreate,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> ChatMessage:
    """
    Add a new message to a chat session.

    Args:
        message_data: The message content
        session_id: The ID of the chat session

    Returns:
        The created ChatMessage
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Create a new message
        message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.content,
            created_at=datetime.now(),
            # Store model_name in metadata if provided
            metadata={"model_override": message_data.model_name}
            if message_data.model_name
            else {},
        )

        # Save the message
        saved_message = chat_storage.add_message(message)
        logger.info(f"Added message {saved_message.id} to session {session_id}")

        return saved_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to add message to session: {str(e)}"
        )


@chat_router.get(
    "/sessions/{session_id}/messages/{message_id}", response_model=ChatMessageResponse
)
async def get_message_with_references(
    session_id: str = Path(..., description="The ID of the chat session"),
    message_id: str = Path(..., description="The ID of the message"),
    storage=Depends(get_storage),
) -> ChatMessageResponse:
    """
    Get a specific message with its entry references.

    Args:
        session_id: The ID of the chat session
        message_id: The ID of the message to retrieve

    Returns:
        The message and its entry references
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get all messages for the session
        messages = chat_storage.get_messages(session_id)

        # Find the specific message
        message = next((m for m in messages if m.id == message_id), None)
        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message with ID {message_id} "
                f"not found in session {session_id}",
            )

        # Get references for this message
        references = chat_storage.get_message_entry_references(message_id)

        # Construct response
        response = ChatMessageResponse(message=message, references=references)

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")


@chat_router.post(
    "/sessions/{session_id}/messages/{message_id}/references",
    response_model=List[EntryReference],
)
async def add_entry_references(
    references: List[EntryReference],
    session_id: str = Path(..., description="The ID of the chat session"),
    message_id: str = Path(..., description="The ID of the message"),
    storage=Depends(get_storage),
) -> List[EntryReference]:
    """
    Add entry references to a message.

    Args:
        references: List of entry references to add
        session_id: The ID of the chat session
        message_id: The ID of the message

    Returns:
        The entry references that were added
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get all messages for the session
        messages = chat_storage.get_messages(session_id)

        # Find the specific message
        message = next((m for m in messages if m.id == message_id), None)
        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message with ID {message_id} "
                f"not found in session {session_id}",
            )

        # Add references
        chat_storage.add_message_entry_references(message_id, references)
        logger.info(f"Added {len(references)} entry references to message {message_id}")

        return references
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add entry references: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to add entry references: {str(e)}"
        )


@chat_router.get(
    "/sessions/{session_id}/references", response_model=Dict[str, List[EntryReference]]
)
async def get_session_references(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> Dict[str, List[EntryReference]]:
    """
    Get all entry references for a chat session.

    Args:
        session_id: The ID of the chat session

    Returns:
        Dictionary mapping message IDs to lists of entry references
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get all references for this session
        references_by_message = chat_storage.get_session_entry_references(session_id)

        return references_by_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session entry references: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session entry references: {str(e)}"
        )


@chat_router.get("/config", response_model=ChatConfig)
async def get_chat_config(storage=Depends(get_storage)) -> ChatConfig:
    """
    Get chat configuration settings.

    Returns:
        ChatConfig object with current settings
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        config = chat_storage.get_chat_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get chat config: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat configuration: {str(e)}"
        )


@chat_router.put("/config", response_model=ChatConfig)
async def update_chat_config(
    config: ChatConfig, storage=Depends(get_storage)
) -> ChatConfig:
    """
    Update chat configuration settings.

    Args:
        config: Updated ChatConfig object

    Returns:
        The updated ChatConfig
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Ensure ID is always "default"
        config.id = "default"

        # Save config
        chat_storage.update_chat_config(config)
        logger.info("Updated chat configuration")

        # Return the updated config
        return config
    except Exception as e:
        logger.error(f"Failed to update chat config: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update chat configuration: {str(e)}"
        )


@chat_router.post(
    "/sessions/{session_id}/process", response_model=ChatResponseWithReferences
)
async def process_user_message(
    message_data: ChatMessageCreate,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponseWithReferences:
    """
    Process a user message and get an AI-generated response.

    Args:
        message_data: The user message content
        session_id: The ID of the chat session

    Returns:
        AI response with references to relevant entries
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Try to extract and apply temporal filter from message
        chat_service.update_session_temporal_filter(session_id, message_data.content)

        # Create a new message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.content,
            created_at=datetime.now(),
            # Store model_name in metadata if provided
            metadata={"model_override": message_data.model_name}
            if message_data.model_name
            else {},
        )

        # Save the user message
        saved_user_message = chat_storage.add_message(user_message)

        # Process message and get response
        assistant_message, references = chat_service.process_message(saved_user_message)

        # Construct response
        response = ChatResponseWithReferences(
            message=assistant_message, references=references
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


@chat_router.post("/sessions/{session_id}/stream", response_model=StreamChatResponse)
async def stream_user_message(
    message_data: ChatMessageCreate,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """
    Process a user message and stream an AI-generated response.

    Args:
        message_data: The user message content
        session_id: The ID of the chat session

    Returns:
        Streaming response with AI-generated content
    """
    try:
        logger.info(f"Starting streaming response for session {session_id}")
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Try to extract and apply temporal filter from message
        chat_service.update_session_temporal_filter(session_id, message_data.content)

        # Create a new message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.content,
            created_at=datetime.now(),
            # Store model_name in metadata if provided
            metadata={"model_override": message_data.model_name}
            if message_data.model_name
            else {},
        )

        # Save the user message
        saved_user_message = chat_storage.add_message(user_message)
        logger.info(f"Saved user message: {saved_user_message.id}")

        # Get streaming response, references, message ID, and tool results
        logger.info("Getting streaming response from chat service")
        (
            response_iterator,
            references,
            message_id,
            tool_results,
        ) = chat_service.stream_message(saved_user_message)
        logger.info(
            f"Got message_id: {message_id} with {len(references)} references "
            f"and {len(tool_results)} tool results"
        )

        # Create an async generator to convert the sync iterator to async
        async def event_generator():
            import json

            # Send the message ID, references, and tool results as the first event
            metadata = StreamChatResponse(
                message_id=message_id, references=references, tool_results=tool_results
            )
            logger.info(
                f"Sending initial metadata event with message_id: {message_id} "
                f"and {len(tool_results)} tool results"
            )
            yield f"data: {metadata.json()}\n\n"

            # Stream the actual content - simplified approach
            chunk_count = 0
            try:
                for chunk in response_iterator:
                    chunk_count += 1
                    # Log the chunk we received
                    if isinstance(chunk, str):
                        logger.debug(f"Received chunk {chunk_count}: '{chunk}'")
                    else:
                        logger.debug(
                            f"Received non-string chunk {chunk_count}: "
                            f"{type(chunk)}: {chunk}"
                        )

                    # We're just expecting string chunks here since we already
                    # extracted the content in _generate_streaming_response
                    if chunk and isinstance(chunk, str):
                        message_json = json.dumps({"text": chunk})
                        logger.debug(f"Sending chunk to client: '{chunk}'")
                        yield f"data: {message_json}\n\n"
                    else:
                        logger.warning(f"Skipping invalid chunk: {chunk}")

                logger.info(f"Finished streaming {chunk_count} chunks")
            except (CUDAError, CircuitBreakerOpen) as e:
                logger.error(f"GPU-related error during streaming: {str(e)}")
                error_json = json.dumps(
                    {
                        "error": (
                            "AI service temporarily unavailable due to GPU issues. "
                            "Please try again in a moment."
                        ),
                        "error_type": "gpu_error",
                        "retry_after": 30,
                    }
                )
                yield f"data: {error_json}\n\n"
            except Exception as e:
                logger.error(f"Error during streaming: {str(e)}")
                error_json = json.dumps({"error": str(e)})
                yield f"data: {error_json}\n\n"

            # Signal the end of the stream
            logger.info("Sending [DONE] event")
            yield "data: [DONE]\n\n"

        # Return a streaming response
        logger.info("Returning streaming response")
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except HTTPException:
        raise
    except (CUDAError, CircuitBreakerOpen) as e:
        logger.error(f"GPU-related error in stream endpoint: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=(
                "AI service temporarily unavailable due to GPU issues. "
                "Please try again in a moment."
            ),
        )
    except Exception as e:
        logger.error(f"Failed to stream message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stream message: {str(e)}"
        )


@chat_router.post("/sessions/{session_id}/summary", response_model=Dict[str, Any])
async def update_session_summary(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Force the creation or update of a conversation summary for the chat session.

    This is useful when a conversation has grown long and needs to be condensed.

    Args:
        session_id: The ID of the chat session to summarize

    Returns:
        Status of the operation
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Update the summary
        success = chat_service.update_session_summary(session_id)

        if success:
            # Get updated session
            updated_session = chat_storage.get_session(session_id)
            return {
                "status": "success",
                "message": "Session summary updated successfully",
                "summary": updated_session.context_summary,
            }
        else:
            return {
                "status": "warning",
                "message": "Could not update session summary. "
                "The conversation may be too short to summarize.",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update session summary: {str(e)}"
        )


@chat_router.delete("/sessions/{session_id}/summary", response_model=Dict[str, Any])
async def clear_session_summary(
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Clear the conversation summary for the chat session.

    This restores full context for the conversation.

    Args:
        session_id: The ID of the chat session

    Returns:
        Status of the operation
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Clear the summary
        success = chat_service.clear_session_summary(session_id)

        if success:
            return {
                "status": "success",
                "message": "Session summary cleared successfully",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to clear session summary",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear session summary: {str(e)}"
        )


@chat_router.get("/sessions/{session_id}/stats", response_model=Dict[str, Any])
async def get_session_stats(
    session_id: str = Path(..., description="The ID of the session to get stats for"),
    storage=Depends(get_storage),
) -> Dict[str, Any]:
    """
    Get statistics for a specific chat session.

    Args:
        session_id: The chat session ID

    Returns:
        Dictionary with message count, unique entry references, etc.
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # First check if the session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session {session_id} not found"
            )

        # Get the stats
        stats = chat_storage.get_session_stats(session_id)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session stats: {str(e)}"
        )


class SaveConversationRequest(BaseModel):
    """Model for saving conversation as journal entry request."""

    title: str = Field(..., min_length=1, description="Title for the journal entry")
    message_ids: Optional[List[str]] = None  # If None, save entire conversation
    additional_notes: Optional[str] = None  # Optional notes to add
    tags: List[str] = []  # Tags for the journal entry
    folder: Optional[str] = None  # Folder for the journal entry

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        """Validate that title is not empty."""
        if not v or not v.strip():
            raise ValueError("Entry title cannot be empty")
        return v.strip()


@chat_router.post("/sessions/{session_id}/save-as-entry")
async def save_conversation_as_entry(
    save_request: SaveConversationRequest,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Save a chat conversation or selected messages as a journal entry.

    Args:
        save_request: Details about what to save and how to format it
        session_id: The ID of the chat session

    Returns:
        Information about the created journal entry
    """
    try:
        from app.storage.entries import EntryStorage
        from app.models import JournalEntry

        chat_storage = ChatStorage(storage.base_dir)
        entry_storage = EntryStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get messages to save
        if save_request.message_ids:
            # Save only specific messages
            all_messages = chat_storage.get_messages(session_id)
            messages_to_save = [
                msg for msg in all_messages if msg.id in save_request.message_ids
            ]
            if not messages_to_save:
                raise HTTPException(
                    status_code=400, detail="No valid messages found with provided IDs"
                )
        else:
            # Save entire conversation
            messages_to_save = chat_storage.get_messages(session_id)
            if not messages_to_save:
                raise HTTPException(
                    status_code=400, detail="No messages found in this conversation"
                )

        # Format conversation content
        content = f"# {save_request.title}\n\n"
        content += f"*Saved from chat session: {session.title or session_id}*\n"
        session_created = session.created_at.strftime("%B %d, %Y at %H:%M")
        content += f"*Session created: {session_created}*\n\n"

        if save_request.additional_notes:
            content += f"## Notes\n\n{save_request.additional_notes.strip()}\n\n"

        content += "## Conversation\n\n"

        for message in messages_to_save:
            role_label = "**User:**" if message.role == "user" else "**Assistant:**"
            timestamp = message.created_at.strftime("%H:%M")
            content += f"{role_label} *(at {timestamp})*\n\n"
            content += f"{message.content}\n\n---\n\n"

        # Add metadata about the original chat
        content += "## Metadata\n\n"
        content += f"- **Original Session ID:** `{session_id}`\n"
        content += f"- **Messages Saved:** {len(messages_to_save)}\n"
        start_time = messages_to_save[0].created_at.strftime("%Y-%m-%d %H:%M")
        end_time = messages_to_save[-1].created_at.strftime("%Y-%m-%d %H:%M")
        content += f"- **Date Range:** {start_time} to {end_time}\n"
        saved_time = datetime.now().strftime("%Y-%m-%d at %H:%M")
        content += f"- **Saved on:** {saved_time}\n"

        # Handle "None" string from request
        folder = save_request.folder
        if folder == "None":
            folder = None

        # Create journal entry
        # Combine user tags with default tags
        entry_tags = save_request.tags + ["chat-conversation", "saved-chat"]

        entry = JournalEntry(
            title=save_request.title,
            content=content,
            tags=entry_tags,
            folder=folder,
            created_at=datetime.now(),
        )

        # Save the entry
        entry_id = entry_storage.save_entry(entry)

        logger.info(f"Saved chat conversation {session_id} as journal entry {entry_id}")

        return {
            "status": "success",
            "message": "Conversation saved as journal entry successfully",
            "entry_id": entry_id,
            "entry_title": save_request.title,
            "messages_saved": len(messages_to_save),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save conversation as entry: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save conversation as entry: {str(e)}"
        )


class UpdateMessageRequest(BaseModel):
    """Model for updating a chat message."""

    content: str = Field(..., min_length=1, description="The updated message content")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


@chat_router.put(
    "/sessions/{session_id}/messages/{message_id}", response_model=ChatMessage
)
async def update_message(
    update_request: UpdateMessageRequest,
    session_id: str = Path(..., description="The ID of the chat session"),
    message_id: str = Path(..., description="The ID of the message to update"),
    storage=Depends(get_storage),
) -> ChatMessage:
    """
    Update the content of an existing chat message.

    Args:
        update_request: The new content for the message
        session_id: The ID of the chat session
        message_id: The ID of the message to update

    Returns:
        The updated ChatMessage
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get the message to verify it belongs to this session
        message = chat_storage.get_message(message_id)
        if not message:
            raise HTTPException(
                status_code=404, detail=f"Message with ID {message_id} not found"
            )

        if message.session_id != session_id:
            raise HTTPException(
                status_code=400,
                detail=f"Message {message_id} does not belong to session {session_id}",
            )

        # Update the message
        success = chat_storage.update_message(message_id, update_request.content)
        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to update message {message_id}"
            )

        # Get and return the updated message
        updated_message = chat_storage.get_message(message_id)
        logger.info(f"Updated message {message_id} in session {session_id}")

        return updated_message

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update message: {str(e)}"
        )


@chat_router.delete("/sessions/{session_id}/messages/{message_id}")
async def delete_message(
    session_id: str = Path(..., description="The ID of the chat session"),
    message_id: str = Path(..., description="The ID of the message to delete"),
    storage=Depends(get_storage),
) -> Dict[str, Any]:
    """
    Delete a chat message.

    Args:
        session_id: The ID of the chat session
        message_id: The ID of the message to delete

    Returns:
        Status message
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Get the message to verify it belongs to this session
        message = chat_storage.get_message(message_id)
        if not message:
            raise HTTPException(
                status_code=404, detail=f"Message with ID {message_id} not found"
            )

        if message.session_id != session_id:
            raise HTTPException(
                status_code=400,
                detail=f"Message {message_id} does not belong to session {session_id}",
            )

        # Delete the message
        success = chat_storage.delete_message(message_id)
        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete message {message_id}"
            )

        logger.info(f"Deleted message {message_id} from session {session_id}")

        return {
            "status": "success",
            "message": f"Message {message_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete message: {str(e)}"
        )


class DeleteMessagesRangeRequest(BaseModel):
    """Model for deleting a range of messages."""

    start_index: int = Field(..., ge=0, description="Starting index (inclusive)")
    end_index: int = Field(..., ge=0, description="Ending index (inclusive)")

    @field_validator("end_index")
    @classmethod
    def validate_range(cls, v, info):
        """Validate that end_index is not less than start_index."""
        if info.data and "start_index" in info.data and v < info.data["start_index"]:
            raise ValueError("end_index must be greater than or equal to start_index")
        return v


@chat_router.delete("/sessions/{session_id}/messages")
async def delete_messages_range(
    range_request: DeleteMessagesRangeRequest,
    session_id: str = Path(..., description="The ID of the chat session"),
    storage=Depends(get_storage),
) -> Dict[str, Any]:
    """
    Delete a range of messages from a chat session.

    Args:
        range_request: The range of messages to delete
        session_id: The ID of the chat session

    Returns:
        Status message
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Delete the message range
        success = chat_storage.delete_messages_range(
            session_id, range_request.start_index, range_request.end_index
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="No messages found in the specified range"
            )

        messages_deleted = range_request.end_index - range_request.start_index + 1
        logger.info(f"Deleted {messages_deleted} messages from session {session_id}")

        return {
            "status": "success",
            "message": f"Deleted {messages_deleted} messages successfully",
            "start_index": range_request.start_index,
            "end_index": range_request.end_index,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message range: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete message range: {str(e)}"
        )


@chat_router.post("/sessions/lazy-create", response_model=ChatResponseWithReferences)
async def lazy_create_session_with_message(
    request: LazySessionCreateRequest,
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponseWithReferences:
    """
    Create a new chat session with the first message atomically.

    This endpoint implements lazy session creation - the session is only created
    when the first message is sent, preventing 0-length sessions.

    Args:
        request: The session data and first message content

    Returns:
        ChatResponseWithReferences containing the assistant's response and session info
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)
        now = datetime.now()

        # Generate a default title if none provided
        title = request.session_title or f"Chat on {now.strftime('%B %d, %Y at %H:%M')}"

        # Create the session object
        session = ChatSession(
            title=title,
            created_at=now,
            updated_at=now,
            last_accessed=now,
            temporal_filter=request.temporal_filter,
            model_name=request.model_name,
            persona_id=request.persona_id,
        )

        # Save the session in database
        created_session = chat_storage.create_session(session)
        logger.info(
            f"Created new chat session with lazy creation: {created_session.id}"
        )

        # Try to extract and apply temporal filter from message
        chat_service.update_session_temporal_filter(
            created_session.id, request.message_content
        )

        # Create the first user message
        user_message = ChatMessage(
            session_id=created_session.id,
            role="user",
            content=request.message_content,
            created_at=datetime.now(),
            # Store model_name in metadata if provided
            metadata={"model_override": request.model_name}
            if request.model_name
            else {},
        )

        # Save the user message
        saved_user_message = chat_storage.add_message(user_message)

        # Process message and get response
        assistant_message, references = chat_service.process_message(saved_user_message)

        # Construct response
        response = ChatResponseWithReferences(
            message=assistant_message, references=references
        )

        # Add session info to response metadata for frontend
        response.message.metadata = response.message.metadata or {}
        response.message.metadata["session_id"] = created_session.id
        response.message.metadata["session_title"] = created_session.title

        return response

    except Exception as e:
        logger.error(f"Failed to create session with first message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session with first message: {str(e)}",
        )


@chat_router.post("/sessions/lazy-stream", response_model=StreamChatResponse)
async def lazy_create_session_with_stream(
    request: LazySessionCreateRequest,
    storage=Depends(get_storage),
    llm_service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """
    Create a new chat session with the first message and stream the response.

    This endpoint implements lazy session creation with streaming response.

    Args:
        request: The session data and first message content

    Returns:
        Streaming response with AI-generated content
    """
    try:
        logger.info(f"Starting lazy streaming session creation")
        chat_storage = ChatStorage(storage.base_dir)
        chat_service = ChatService(chat_storage, llm_service, storage)
        now = datetime.now()

        # Generate a default title if none provided
        title = request.session_title or f"Chat on {now.strftime('%B %d, %Y at %H:%M')}"

        # Create the session object
        session = ChatSession(
            title=title,
            created_at=now,
            updated_at=now,
            last_accessed=now,
            temporal_filter=request.temporal_filter,
            model_name=request.model_name,
            persona_id=request.persona_id,
        )

        # Save the session in database
        created_session = chat_storage.create_session(session)
        logger.info(
            f"Created new chat session with lazy streaming: {created_session.id}"
        )

        # Try to extract and apply temporal filter from message
        chat_service.update_session_temporal_filter(
            created_session.id, request.message_content
        )

        # Create the first user message
        user_message = ChatMessage(
            session_id=created_session.id,
            role="user",
            content=request.message_content,
            created_at=datetime.now(),
            # Store model_name in metadata if provided
            metadata={"model_override": request.model_name}
            if request.model_name
            else {},
        )

        # Save the user message
        saved_user_message = chat_storage.add_message(user_message)
        logger.info(f"Saved user message: {saved_user_message.id}")

        # Get streaming response, references, message ID, and tool results
        logger.info("Getting streaming response from chat service")
        (
            response_iterator,
            references,
            message_id,
            tool_results,
        ) = chat_service.stream_message(saved_user_message)
        logger.info(
            f"Got message_id: {message_id} with {len(references)} references "
            f"and {len(tool_results)} tool results"
        )

        # Create an async generator to convert the sync iterator to async
        async def event_generator():
            import json

            # Send the session info, message ID, references, and tool results as the first event
            metadata = StreamChatResponse(
                message_id=message_id, references=references, tool_results=tool_results
            )
            # Add session info to metadata
            metadata_dict = metadata.dict()
            metadata_dict["session_id"] = created_session.id
            metadata_dict["session_title"] = created_session.title

            logger.info(
                f"Sending initial metadata event with session_id: {created_session.id} and message_id: {message_id}"
            )
            yield f"data: {json.dumps(metadata_dict)}\n\n"

            # Stream the actual content - simplified approach
            chunk_count = 0
            try:
                for chunk in response_iterator:
                    chunk_count += 1
                    # Log the chunk we received
                    if isinstance(chunk, str):
                        logger.debug(f"Received chunk {chunk_count}: '{chunk}'")
                    else:
                        logger.debug(
                            f"Received non-string chunk {chunk_count}: "
                            f"{type(chunk)}: {chunk}"
                        )

                    # We're just expecting string chunks here since we already
                    # extracted the content in _generate_streaming_response
                    if chunk and isinstance(chunk, str):
                        message_json = json.dumps({"text": chunk})
                        logger.debug(f"Sending chunk to client: '{chunk}'")
                        yield f"data: {message_json}\n\n"
                    else:
                        logger.warning(f"Skipping invalid chunk: {chunk}")

                logger.info(f"Finished streaming {chunk_count} chunks")
            except (CUDAError, CircuitBreakerOpen) as e:
                logger.error(f"GPU-related error during streaming: {str(e)}")
                error_json = json.dumps(
                    {
                        "error": (
                            "AI service temporarily unavailable due to GPU issues. "
                            "Please try again in a moment."
                        ),
                        "error_type": "gpu_error",
                        "retry_after": 30,
                    }
                )
                yield f"data: {error_json}\n\n"
            except Exception as e:
                logger.error(f"Error during streaming: {str(e)}")
                error_json = json.dumps({"error": str(e)})
                yield f"data: {error_json}\n\n"

            # Signal the end of the stream
            logger.info("Sending [DONE] event")
            yield "data: [DONE]\n\n"

        # Return a streaming response
        logger.info("Returning streaming response")
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except HTTPException:
        raise
    except (CUDAError, CircuitBreakerOpen) as e:
        logger.error(f"GPU-related error in lazy stream endpoint: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=(
                "AI service temporarily unavailable due to GPU issues. "
                "Please try again in a moment."
            ),
        )
    except Exception as e:
        logger.error(f"Failed to create session with streaming: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create session with streaming: {str(e)}"
        )


@chat_router.post("/sessions/cleanup-empty")
async def cleanup_empty_sessions(
    storage=Depends(get_storage),
) -> Dict[str, Any]:
    """
    Clean up chat sessions that have no messages (0-length sessions).

    This endpoint removes sessions that were created but never used,
    which can happen when users navigate to a new chat but don't send any messages.

    Returns:
        Status and count of cleaned up sessions
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Clean up empty sessions
        deleted_count = chat_storage.cleanup_empty_sessions()

        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} empty chat sessions",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup empty sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup empty sessions: {str(e)}"
        )


@chat_router.get("/search", response_model=PaginatedSearchResults)
async def search_chat_sessions(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    sort_by: str = Query(
        "relevance", description="Sort order (relevance, date, title)"
    ),
    date_from: Optional[str] = Query(
        None, description="Start date filter (ISO format)"
    ),
    date_to: Optional[str] = Query(None, description="End date filter (ISO format)"),
    storage=Depends(get_storage),
) -> PaginatedSearchResults:
    """
    Search chat sessions and messages using full-text search.

    Args:
        q: Search query string
        limit: Maximum number of results to return
        offset: Number of results to skip for pagination
        sort_by: Sort order (relevance, date, title)
        date_from: Start date filter in ISO format
        date_to: End date filter in ISO format

    Returns:
        Paginated search results with matching chat sessions
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Validate sort_by parameter
        allowed_sort_options = ["relevance", "date", "title"]
        if sort_by not in allowed_sort_options:
            sort_by = "relevance"

        # Perform search
        search_results = chat_storage.search_sessions(
            query=q,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            date_from=date_from,
            date_to=date_to,
        )

        # Get total count for pagination
        total_count = chat_storage.count_search_results(
            query=q, date_from=date_from, date_to=date_to
        )

        # Convert ChatSession objects to ChatSearchResult objects
        chat_search_results = []
        for session in search_results:
            # Determine match type based on search content
            match_type = (
                "session_title"
                if q.lower() in (session.title or "").lower()
                else "message_content"
            )

            # Create search result
            search_result = ChatSearchResult(
                session=session,
                match_type=match_type,
                relevance_score=1.0,  # FTS handles ranking internally
                matched_messages=[],
                highlighted_snippets=[],
            )
            chat_search_results.append(search_result)

        # Calculate pagination metadata
        has_next = offset + limit < total_count
        has_previous = offset > 0

        return PaginatedSearchResults(
            results=chat_search_results,
            total=total_count,
            limit=limit,
            offset=offset,
            query=q,
            has_next=has_next,
            has_previous=has_previous,
        )

    except Exception as e:
        logger.error(f"Failed to search chat sessions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search chat sessions: {str(e)}"
        )


@chat_router.get(
    "/sessions/{session_id}/search", response_model=List[MessageSearchResult]
)
async def search_within_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    q: str = Query(..., description="Search query string"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    storage=Depends(get_storage),
) -> List[MessageSearchResult]:
    """
    Search within a specific chat session's messages.

    Args:
        session_id: The ID of the chat session to search within
        q: Search query string
        limit: Maximum number of message results

    Returns:
        List of matching messages with highlighting and relevance scoring
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)

        # Check if session exists
        session = chat_storage.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Chat session with ID {session_id} not found"
            )

        # Search messages within the session
        matching_messages = chat_storage.search_messages_in_session(
            session_id=session_id, query=q, limit=limit
        )

        # Convert to MessageSearchResult objects with highlighting
        search_results = []
        for message in matching_messages:
            # Create highlighted content (simple case-insensitive highlighting)
            highlighted_content = message.content
            if q.strip():
                import re

                pattern = re.compile(re.escape(q), re.IGNORECASE)
                highlighted_content = pattern.sub(
                    r"<mark>\g<0></mark>", message.content
                )

            # Calculate relevance score based on query matches
            relevance_score = 1.0
            if q.strip():
                query_lower = q.lower()
                content_lower = message.content.lower()
                match_count = content_lower.count(query_lower)
                relevance_score = min(
                    match_count / 10.0 + 0.1, 1.0
                )  # Normalize to 0.1-1.0

            search_result = MessageSearchResult(
                message=message,
                highlighted_content=highlighted_content,
                relevance_score=relevance_score,
                context_before=None,  # Could add context in future
                context_after=None,
            )
            search_results.append(search_result)

        # Sort by relevance score (descending)
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return search_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search within session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search within session: {str(e)}"
        )
