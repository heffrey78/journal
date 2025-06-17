"""
Tests for saving chat conversations as journal entries.
Tests the C32-002 functionality.
"""

import pytest
import tempfile
import shutil
from datetime import datetime

from app.storage.chat import ChatStorage
from app.storage.entries import EntryStorage
from app.chat_service import ChatService
from app.models import ChatSession, ChatMessage


class MockLLMService:
    """Mock LLM service for testing."""

    def semantic_search(self, query, limit=5, date_filter=None):
        return []

    def get_embedding(self, text):
        # Return a dummy embedding
        return [0.1] * 1536


@pytest.fixture
def test_storage():
    """Create temporary storage for testing."""
    test_dir = tempfile.mkdtemp(prefix="journal_test_")
    chat_storage = ChatStorage(test_dir)
    entry_storage = EntryStorage(test_dir)
    llm_service = MockLLMService()
    chat_service = ChatService(chat_storage, llm_service)

    yield {
        "chat_storage": chat_storage,
        "entry_storage": entry_storage,
        "chat_service": chat_service,
        "test_dir": test_dir,
    }

    # Cleanup
    shutil.rmtree(test_dir)


@pytest.fixture
def sample_chat_session(test_storage):
    """Create a sample chat session with messages."""
    chat_storage = test_storage["chat_storage"]

    # Create a test chat session
    session = ChatSession(
        title="Test Chat Session",
        created_at=datetime.now(),
    )
    created_session = chat_storage.create_session(session)
    session_id = created_session.id

    # Add some test messages
    messages = [
        ChatMessage(
            session_id=session_id,
            role="user",
            content="What did I write about coding yesterday?",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content="Based on your entries, you wrote about implementing the chat feature with streaming responses.",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=session_id,
            role="user",
            content="Can you help me plan my next coding session?",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content="Sure! I suggest focusing on the frontend components next.",
            created_at=datetime.now(),
        ),
    ]

    saved_messages = []
    for msg in messages:
        saved_msg = chat_storage.add_message(msg)
        saved_messages.append(saved_msg)

    return {
        "session_id": session_id,
        "messages": saved_messages,
        "session": created_session,
    }


def test_save_entire_conversation(test_storage, sample_chat_session):
    """Test saving an entire chat conversation as a journal entry."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]

    # Save the conversation
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id,
        title="Chat about Coding Progress",
        tags=["coding", "planning"],
        folder="conversations",
        additional_notes="This was a helpful conversation.",
    )

    # Verify the entry was created
    saved_entry = entry_storage.get_entry(entry_id)
    assert saved_entry is not None
    assert saved_entry.title == "Chat about Coding Progress"
    assert "chat-conversation" in saved_entry.tags
    assert "saved-chat" in saved_entry.tags
    assert "coding" in saved_entry.tags
    assert "planning" in saved_entry.tags
    assert saved_entry.folder == "conversations"
    assert saved_entry.source_metadata is not None
    assert saved_entry.source_metadata["source_type"] == "chat_conversation"
    assert saved_entry.source_metadata["original_session_id"] == session_id
    assert saved_entry.source_metadata["partial_save"] is False


def test_save_partial_conversation(test_storage, sample_chat_session):
    """Test saving only specific messages from a conversation."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]
    messages = sample_chat_session["messages"]

    # Save only the first two messages
    message_ids_to_save = [messages[0].id, messages[1].id]
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id,
        title="Initial Chat Exchange",
        message_ids=message_ids_to_save,
        tags=["excerpt"],
        additional_notes="Just the first exchange.",
    )

    # Verify the partial save
    saved_entry = entry_storage.get_entry(entry_id)
    assert saved_entry is not None
    assert saved_entry.title == "Initial Chat Exchange"
    assert saved_entry.source_metadata["partial_save"] is True
    assert saved_entry.source_metadata["message_count"] == 2
    assert "excerpt" in saved_entry.tags


def test_conversation_content_formatting(test_storage, sample_chat_session):
    """Test that conversation content is properly formatted."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]

    # Save the conversation
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id, title="Formatting Test", additional_notes="Test notes"
    )

    # Verify content formatting
    saved_entry = entry_storage.get_entry(entry_id)
    content = saved_entry.content

    assert "# Formatting Test" in content
    assert "## Notes" in content
    assert "Test notes" in content
    assert "## Conversation" in content
    assert "**User:**" in content
    assert "**Assistant:**" in content
    assert "## Metadata" in content
    assert "Original Session ID" in content
    assert "Messages Saved:" in content
    assert "Saved on:" in content


def test_conversation_searchability(test_storage, sample_chat_session):
    """Test that saved conversations are searchable."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]

    # Save the conversation
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id, title="Searchable Chat about Coding", tags=["coding"]
    )

    # Search for the saved conversation
    search_results = entry_storage.text_search("coding")
    found_entry = any(entry.id == entry_id for entry in search_results)
    assert found_entry, "Saved conversation should be searchable"

    # Test tag search
    tag_results = entry_storage.get_entries(tags=["coding"])
    found_by_tag = any(entry.id == entry_id for entry in tag_results)
    assert found_by_tag, "Saved conversation should be findable by tag"


def test_source_metadata_tracking(test_storage, sample_chat_session):
    """Test that source metadata is properly tracked."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]
    session = sample_chat_session["session"]

    # Save the conversation
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id, title="Metadata Test"
    )

    # Verify source metadata
    saved_entry = entry_storage.get_entry(entry_id)
    metadata = saved_entry.source_metadata

    assert metadata is not None
    assert metadata["source_type"] == "chat_conversation"
    assert metadata["original_session_id"] == session_id
    assert metadata["session_title"] == session.title
    assert metadata["session_created_at"] == session.created_at.isoformat()
    assert metadata["message_count"] == 4  # All 4 messages
    assert "saved_at" in metadata
    assert metadata["partial_save"] is False


def test_conversation_format_helper_method(test_storage, sample_chat_session):
    """Test the format_conversation_for_entry helper method."""
    chat_service = test_storage["chat_service"]
    session_id = sample_chat_session["session_id"]
    messages = sample_chat_session["messages"]

    # Test formatting entire conversation
    content = chat_service.format_conversation_for_entry(
        session_id=session_id, title="Test Title", additional_notes="Test notes"
    )

    assert "# Test Title" in content
    assert "## Notes" in content
    assert "Test notes" in content
    assert "## Conversation" in content
    assert "## Metadata" in content

    # Test formatting partial conversation
    partial_content = chat_service.format_conversation_for_entry(
        session_id=session_id, message_ids=[messages[0].id], title="Partial Test"
    )

    assert "# Partial Test" in partial_content
    # Should only contain the first message
    lines = partial_content.split("\n")
    user_lines = [line for line in lines if "**User:**" in line]
    assistant_lines = [line for line in lines if "**Assistant:**" in line]
    assert len(user_lines) == 1
    assert len(assistant_lines) == 0  # Only saved the user message


def test_error_handling(test_storage):
    """Test error handling for invalid inputs."""
    chat_service = test_storage["chat_service"]

    # Test with non-existent session
    with pytest.raises(ValueError, match="Chat session .* not found"):
        chat_service.save_conversation_as_entry(
            session_id="non-existent-session", title="Error Test"
        )

    # Test with invalid message IDs
    session = ChatSession(title="Empty Session")
    chat_storage = test_storage["chat_storage"]
    created_session = chat_storage.create_session(session)

    with pytest.raises(ValueError, match="No valid messages found"):
        chat_service.save_conversation_as_entry(
            session_id=created_session.id,
            title="Error Test",
            message_ids=["non-existent-message"],
        )


def test_duplicate_tag_removal(test_storage, sample_chat_session):
    """Test that duplicate tags are removed while preserving order."""
    chat_service = test_storage["chat_service"]
    entry_storage = test_storage["entry_storage"]
    session_id = sample_chat_session["session_id"]

    # Save with duplicate tags
    entry_id = chat_service.save_conversation_as_entry(
        session_id=session_id,
        title="Duplicate Tag Test",
        tags=["coding", "chat-conversation", "coding", "saved-chat"],  # Duplicates
    )

    # Verify duplicates are removed but order is preserved
    saved_entry = entry_storage.get_entry(entry_id)
    expected_tags = ["coding", "chat-conversation", "saved-chat"]  # Deduped
    assert saved_entry.tags == expected_tags
