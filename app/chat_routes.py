"""
API routes for chat functionality.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from app.models import ChatSession, ChatMessage, ChatConfig, EntryReference
from app.storage.chat import ChatStorage
from app.chat_service import ChatService
from app.llm_service import LLMService
from app.utils import get_storage, get_llm_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatSessionCreate(BaseModel):
    """Model for creating a new chat session."""

    title: Optional[str] = None
    temporal_filter: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    """Model for updating an existing chat session."""

    title: Optional[str] = None
    context_summary: Optional[str] = None
    temporal_filter: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """Model for creating a new chat message."""

    content: str = Field(
        ..., min_length=1, description="The message content (cannot be empty)"
    )

    @validator("content")
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


@chat_router.get("/sessions", response_model=List[ChatSession])
async def list_chat_sessions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    storage=Depends(get_storage),
) -> List[ChatSession]:
    """
    List existing chat sessions with pagination.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of ChatSession objects sorted by last_accessed (most recent first)
    """
    try:
        chat_storage = ChatStorage(storage.base_dir)
        sessions = chat_storage.list_sessions(limit, offset)
        return sessions
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
        chat_service = ChatService(chat_storage, llm_service)

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
        chat_service = ChatService(chat_storage, llm_service)

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
        )

        # Save the user message
        saved_user_message = chat_storage.add_message(user_message)
        logger.info(f"Saved user message: {saved_user_message.id}")

        # Get streaming response, references, and message ID
        logger.info("Getting streaming response from chat service")
        response_iterator, references, message_id = chat_service.stream_message(
            saved_user_message
        )
        logger.info(f"Got message_id: {message_id} with {len(references)} references")

        # Create an async generator to convert the sync iterator to async
        async def event_generator():
            import json

            # Send the message ID and references as the first event
            metadata = StreamChatResponse(message_id=message_id, references=references)
            logger.info(f"Sending initial metadata event with message_id: {message_id}")
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
        chat_service = ChatService(chat_storage, llm_service)

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
        chat_service = ChatService(chat_storage, llm_service)

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
