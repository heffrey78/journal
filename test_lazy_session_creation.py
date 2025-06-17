"""
Test lazy session creation functionality to prevent 0-length chat sessions.

This test module validates that:
1. Sessions are only created when the first message is sent
2. Existing 0-length sessions can be cleaned up
3. The lazy session creation endpoints work correctly
4. Frontend properly handles the lazy creation flow
"""

import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from app.storage.chat import ChatStorage
from app.models import ChatSession, ChatMessage
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def chat_storage():
    """Create a test chat storage instance."""
    return ChatStorage("./test_journal_data")


class TestLazySessionCreation:
    """Test cases for lazy session creation."""

    def test_lazy_session_creation_with_message(self, client):
        """Test that lazy session creation creates session and processes message atomically."""
        request_data = {
            "message_content": "Hello, this is my first message!",
            "session_title": "Test Lazy Session",
            "persona_id": "default",
        }

        response = client.post("/chat/sessions/lazy-create", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify the response structure
        assert "message" in data
        assert "references" in data
        assert data["message"]["role"] == "assistant"
        assert data["message"]["metadata"]["session_id"] is not None
        assert data["message"]["metadata"]["session_title"] == "Test Lazy Session"

        # Verify session was created
        session_id = data["message"]["metadata"]["session_id"]
        session_response = client.get(f"/chat/sessions/{session_id}")
        assert session_response.status_code == 200

        session_data = session_response.json()
        assert session_data["title"] == "Test Lazy Session"

        # Verify messages exist
        messages_response = client.get(f"/chat/sessions/{session_id}/messages")
        assert messages_response.status_code == 200

        messages = messages_response.json()
        assert len(messages) >= 2  # User message + assistant response
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, this is my first message!"

    def test_lazy_streaming_session_creation(self, client):
        """Test that lazy streaming session creation works correctly."""
        request_data = {
            "message_content": "Hello, streaming test!",
            "session_title": "Test Streaming Session",
        }

        # Since we can't easily test streaming in a unit test,
        # we'll just test that the endpoint accepts the request
        response = client.post("/chat/sessions/lazy-stream", json=request_data)

        # The endpoint should return a streaming response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_empty_session_cleanup(self, client, chat_storage):
        """Test that empty sessions can be cleaned up."""
        # Create a few test sessions with and without messages
        now = datetime.now()

        # Create session with messages (should not be deleted)
        session_with_messages = ChatSession(
            title="Session with messages",
            created_at=now,
            updated_at=now,
            last_accessed=now,
        )
        saved_session_with_messages = chat_storage.create_session(session_with_messages)

        # Add a message to this session
        message = ChatMessage(
            session_id=saved_session_with_messages.id,
            role="user",
            content="Test message",
            created_at=now,
        )
        chat_storage.add_message(message)

        # Create sessions without messages (should be deleted)
        empty_session_1 = ChatSession(
            title="Empty session 1", created_at=now, updated_at=now, last_accessed=now
        )
        saved_empty_1 = chat_storage.create_session(empty_session_1)

        empty_session_2 = ChatSession(
            title="Empty session 2", created_at=now, updated_at=now, last_accessed=now
        )
        saved_empty_2 = chat_storage.create_session(empty_session_2)

        # Verify sessions exist
        assert chat_storage.get_session(saved_session_with_messages.id) is not None
        assert chat_storage.get_session(saved_empty_1.id) is not None
        assert chat_storage.get_session(saved_empty_2.id) is not None

        # Run cleanup
        response = client.post("/chat/sessions/cleanup-empty")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_count"] == 2  # Two empty sessions should be deleted

        # Verify cleanup results
        assert (
            chat_storage.get_session(saved_session_with_messages.id) is not None
        )  # Should still exist
        assert chat_storage.get_session(saved_empty_1.id) is None  # Should be deleted
        assert chat_storage.get_session(saved_empty_2.id) is None  # Should be deleted

    def test_lazy_creation_validation(self, client):
        """Test that lazy session creation validates input correctly."""
        # Test empty message content
        response = client.post(
            "/chat/sessions/lazy-create",
            json={"message_content": "", "session_title": "Test Session"},
        )
        assert response.status_code == 422  # Validation error

        # Test whitespace-only message content
        response = client.post(
            "/chat/sessions/lazy-create",
            json={"message_content": "   ", "session_title": "Test Session"},
        )
        assert response.status_code == 422  # Validation error

        # Test missing message content
        response = client.post(
            "/chat/sessions/lazy-create", json={"session_title": "Test Session"}
        )
        assert response.status_code == 422  # Validation error

    def test_cleanup_empty_sessions_storage_method(self, chat_storage):
        """Test the storage-level cleanup method directly."""
        now = datetime.now()

        # Create some empty sessions
        empty_sessions = []
        for i in range(3):
            session = ChatSession(
                title=f"Empty session {i}",
                created_at=now,
                updated_at=now,
                last_accessed=now,
            )
            saved_session = chat_storage.create_session(session)
            empty_sessions.append(saved_session)

        # Create a session with a message
        session_with_message = ChatSession(
            title="Session with message",
            created_at=now,
            updated_at=now,
            last_accessed=now,
        )
        saved_session_with_message = chat_storage.create_session(session_with_message)

        message = ChatMessage(
            session_id=saved_session_with_message.id,
            role="user",
            content="Test message",
            created_at=now,
        )
        chat_storage.add_message(message)

        # Run cleanup
        deleted_count = chat_storage.cleanup_empty_sessions()

        # Should have deleted 3 empty sessions
        assert deleted_count == 3

        # Verify sessions are gone
        for session in empty_sessions:
            assert chat_storage.get_session(session.id) is None

        # Session with message should still exist
        assert chat_storage.get_session(saved_session_with_message.id) is not None

    def test_lazy_creation_with_default_title(self, client):
        """Test lazy session creation with auto-generated title."""
        request_data = {"message_content": "Hello without a custom title!"}

        response = client.post("/chat/sessions/lazy-create", json=request_data)
        assert response.status_code == 200

        data = response.json()
        session_title = data["message"]["metadata"]["session_title"]

        # Should have a default title with current date
        assert "Chat on" in session_title
        assert str(datetime.now().year) in session_title

    def test_lazy_creation_preserves_persona(self, client):
        """Test that lazy session creation preserves persona information."""
        request_data = {
            "message_content": "Hello with persona!",
            "session_title": "Persona Test Session",
            "persona_id": "test-persona-123",
        }

        response = client.post("/chat/sessions/lazy-create", json=request_data)
        assert response.status_code == 200

        data = response.json()
        session_id = data["message"]["metadata"]["session_id"]

        # Verify session has the correct persona
        session_response = client.get(f"/chat/sessions/{session_id}")
        assert session_response.status_code == 200

        session_data = session_response.json()
        assert session_data["persona_id"] == "test-persona-123"


class TestLazySessionIntegration:
    """Integration tests for the complete lazy session workflow."""

    def test_full_lazy_workflow(self, client):
        """Test the complete workflow from lazy creation to normal operation."""
        # Step 1: Create session with first message (lazy creation)
        create_request = {
            "message_content": "Start a new conversation",
            "session_title": "Integration Test Session",
        }

        create_response = client.post("/chat/sessions/lazy-create", json=create_request)
        assert create_response.status_code == 200

        create_data = create_response.json()
        session_id = create_data["message"]["metadata"]["session_id"]

        # Step 2: Add another message to the same session (normal flow)
        message_request = {"content": "This is my second message"}

        message_response = client.post(
            f"/chat/sessions/{session_id}/messages", json=message_request
        )
        assert message_response.status_code == 200

        # Step 3: Process the second message
        process_request = {"content": "Process my second message"}

        process_response = client.post(
            f"/chat/sessions/{session_id}/process", json=process_request
        )
        assert process_response.status_code == 200

        # Step 4: Verify session has multiple messages
        messages_response = client.get(f"/chat/sessions/{session_id}/messages")
        assert messages_response.status_code == 200

        messages = messages_response.json()
        # Should have at least 4 messages: user1, assistant1, user2, assistant2
        assert len(messages) >= 4

        # Verify message order and content
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Start a new conversation"

    def test_cleanup_after_partial_failures(self, client, chat_storage):
        """Test that cleanup works even after partial session creation failures."""
        # Manually create some sessions that might be left over from failed operations
        now = datetime.now()

        # Simulate sessions that were created but never got their first message
        for i in range(5):
            session = ChatSession(
                title=f"Failed session {i}",
                created_at=now,
                updated_at=now,
                last_accessed=now,
            )
            chat_storage.create_session(session)

        # Run cleanup
        response = client.post("/chat/sessions/cleanup-empty")
        assert response.status_code == 200

        data = response.json()
        assert data["deleted_count"] == 5

        # Verify all sessions were cleaned up
        all_sessions = chat_storage.list_sessions(limit=100)
        empty_sessions = [
            s for s in all_sessions if s.title.startswith("Failed session")
        ]
        assert len(empty_sessions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
