import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch

from app.api import app
from app.models import JournalEntry  # Import JournalEntry model


@pytest.fixture
def mock_ollama():
    """Fixture to mock ollama for all tests."""
    with patch("app.llm_service.ollama") as mock_ollama:
        # Mock ollama for LLMService initialization
        mock_ollama.list.return_value = {
            "models": [
                {"name": "qwen3:latest"},
                {"name": "qwen2.5:3b"},
                {"name": "nomic-embed-text:latest"},
            ]
        }
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Mock ollama.chat for tool analysis and other operations
        mock_ollama.chat.return_value = {
            "message": {
                "role": "assistant",
                "content": '{"should_use_tools": false, "recommended_tools": [], "analysis": "No tools needed"}',
            }
        }
        yield mock_ollama


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    return TestClient(app)


class TestChatAPI:
    """Tests for the Chat API endpoints."""

    def test_create_and_get_session(self, client):
        """Test creating and retrieving a chat session."""
        # Create a new session
        response = client.post("/chat/sessions", json={"title": "Test Chat Session"})
        assert response.status_code == 200

        # Extract session data and verify
        session_data = response.json()
        assert "id" in session_data
        assert session_data["title"] == "Test Chat Session"
        assert "created_at" in session_data

        # Get the session by ID
        session_id = session_data["id"]
        response = client.get(f"/chat/sessions/{session_id}")

        assert response.status_code == 200
        retrieved_session = response.json()
        assert retrieved_session["id"] == session_id
        assert retrieved_session["title"] == "Test Chat Session"

        # Delete the session when done
        response = client.delete(f"/chat/sessions/{session_id}")
        assert response.status_code == 200

    def test_list_sessions(self, client):
        """Test listing chat sessions."""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            response = client.post(
                "/chat/sessions", json={"title": f"Test Session {i}"}
            )
            assert response.status_code == 200
            session_ids.append(response.json()["id"])

        # List sessions
        response = client.get("/chat/sessions")
        assert response.status_code == 200

        # Verify sessions are returned
        paginated_response = response.json()
        assert len(paginated_response["sessions"]) >= 3
        assert paginated_response["total"] >= 3
        assert "limit" in paginated_response
        assert "offset" in paginated_response
        assert "has_next" in paginated_response
        assert "has_previous" in paginated_response

        # Verify pagination
        response = client.get("/chat/sessions?limit=2")
        assert response.status_code == 200
        paginated_response = response.json()
        assert len(paginated_response["sessions"]) <= 2
        assert paginated_response["limit"] == 2

        # Clean up
        for session_id in session_ids:
            client.delete(f"/chat/sessions/{session_id}")

    def test_update_session(self, client):
        """Test updating a chat session."""
        # Create a session
        response = client.post("/chat/sessions", json={"title": "Original Title"})
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Update the session
        response = client.patch(
            f"/chat/sessions/{session_id}",
            json={
                "title": "Updated Title",
                "context_summary": "This is a test summary",
                "temporal_filter": "past_week",
            },
        )

        assert response.status_code == 200
        updated = response.json()
        assert updated["title"] == "Updated Title"
        assert updated["context_summary"] == "This is a test summary"
        assert updated["temporal_filter"] == "past_week"

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_delete_session(self, client):
        """Test deleting a chat session."""
        # Create a session
        response = client.post("/chat/sessions", json={"title": "Session to Delete"})
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Delete the session
        response = client.delete(f"/chat/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify it's gone
        response = client.get(f"/chat/sessions/{session_id}")
        assert response.status_code == 404

    def test_get_nonexistent_session(self, client):
        """Test getting a session that doesn't exist."""
        response = client.get("/chat/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_get_chat_config(self, client):
        """Test retrieving chat configuration."""
        response = client.get("/chat/config")
        assert response.status_code == 200
        config = response.json()

        # Verify default config fields
        assert "system_prompt" in config
        assert "max_tokens" in config  # Changed from max_context_tokens to max_tokens
        assert config["id"] == "default"

    def test_update_chat_config(self, client):
        """Test updating chat configuration."""
        # Get current config
        response = client.get("/chat/config")
        assert response.status_code == 200
        original_config = response.json()

        # Update config with new values
        test_prompt = "This is a test system prompt."
        original_config["system_prompt"] = test_prompt
        original_config[
            "max_tokens"
        ] = 2048  # Changed from max_context_tokens to max_tokens

        response = client.put("/chat/config", json=original_config)
        assert response.status_code == 200

        # Verify update
        response = client.get("/chat/config")
        assert response.status_code == 200
        updated_config = response.json()
        assert updated_config["system_prompt"] == test_prompt
        assert updated_config["max_tokens"] == 2048

        # Reset to original values
        response = client.put(
            "/chat/config",
            json={
                "id": "default",
                "system_prompt": "You are a helpful assistant that helps users "
                "explore their journal entries. Always cite specific entries "
                "when making claims about the user's experiences.",
                "max_tokens": 2048,  # Changed from max_context_tokens to max_tokens
                "temperature": 0.7,
                "retrieval_limit": 10,
                "chunk_size": 500,
                # Remove conversation_summary_threshold as it doesn't exist in the model
            },
        )

    def test_add_and_get_message(self, client):
        """Test adding and retrieving a message in a chat session."""
        # Create a session
        response = client.post("/chat/sessions", json={"title": "Message Test Session"})
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Add a message to the session
        message_content = "This is a test message"
        response = client.post(
            f"/chat/sessions/{session_id}/messages", json={"content": message_content}
        )
        assert response.status_code == 200
        message_data = response.json()
        assert message_data["content"] == message_content
        assert message_data["role"] == "user"
        assert message_data["session_id"] == session_id
        message_id = message_data["id"]

        # Retrieve all messages
        response = client.get(f"/chat/sessions/{session_id}/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 1
        assert messages[0]["id"] == message_id
        assert messages[0]["content"] == message_content

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_message_with_references(self, client, mock_ollama):
        """Test adding and retrieving a message with references."""
        # Create a session
        response = client.post(
            "/chat/sessions", json={"title": "References Test Session"}
        )
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Mock LLM service for processing
        with patch(
            "app.llm_service.LLMService.analyze_message_for_tools"
        ) as mock_tool_analysis, patch(
            "app.tools.journal_search.JournalSearchTool.execute"
        ) as mock_journal_tool, patch(
            "app.llm_service.LLMService.synthesize_response_with_tools"
        ) as mock_synthesis:
            # Mock tool analysis to recommend journal search
            mock_tool_analysis.return_value = {
                "should_use_tools": True,
                "recommended_tools": [
                    {
                        "tool_name": "journal_search",
                        "confidence": 0.9,
                        "reason": "User asking about journal entries",
                        "suggested_query": "journal entries",
                    }
                ],
                "analysis": "User wants to search journal entries",
            }

            # Mock journal search tool results
            from app.tools.base import ToolResult

            mock_journal_tool.return_value = ToolResult(
                success=True,
                data={
                    "results": [
                        {
                            "id": "20250503190939",
                            "title": "Test Entry 1",
                            "content_preview": "Content 1",
                            "relevance": 0.85,
                        },
                        {
                            "id": "20250504072752",
                            "title": "Test Entry 2",
                            "content_preview": "Content 2",
                            "relevance": 0.75,
                        },
                    ]
                },
            )

            # Mock response synthesis
            mock_synthesis.return_value = (
                "This is a response with references to your journal."
            )

            # Process a message which should create references
            response = client.post(
                f"/chat/sessions/{session_id}/process",
                json={"content": "Tell me about my journal entries"},
            )
            assert response.status_code == 200
            result = response.json()

            # Verify message was created with references
            assert "message" in result
            assert "references" in result
            assert len(result["references"]) == 2

            # Check references have expected entry IDs
            reference_ids = [ref["entry_id"] for ref in result["references"]]
            assert "20250503190939" in reference_ids
            assert "20250504072752" in reference_ids

            # Get the message ID
            message_id = result["message"]["id"]

            # Get the message specifically to verify references are attached
            response = client.get(f"/chat/sessions/{session_id}/messages/{message_id}")
            assert response.status_code == 200
            message_data = response.json()

            # Check that references are included when retrieving message
            assert "references" in message_data
            assert len(message_data["references"]) == 2

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_get_nonexistent_message(self, client):
        """Test getting a message that doesn't exist."""
        # Create a session
        response = client.post(
            "/chat/sessions", json={"title": "Nonexistent Message Test Session"}
        )
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Try to get a message that doesn't exist
        response = client.get(f"/chat/sessions/{session_id}/messages/nonexistent-id")
        assert response.status_code == 404

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_session_context(self, client):
        """Test adding multiple messages to create conversation context."""
        # Create a session
        response = client.post("/chat/sessions", json={"title": "Context Test Session"})
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Add multiple messages to build context
        message_texts = [
            "Hello, this is message 1",
            "This is message 2",
            "And this is message 3",
        ]

        message_ids = []
        for text in message_texts:
            response = client.post(
                f"/chat/sessions/{session_id}/messages", json={"content": text}
            )
            assert response.status_code == 200
            message_ids.append(response.json()["id"])

        # Get all messages and verify order
        response = client.get(f"/chat/sessions/{session_id}/messages")
        assert response.status_code == 200
        messages = response.json()

        assert len(messages) == 3
        for i, message in enumerate(messages):
            assert message["content"] == message_texts[i]

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_process_message(self, client):
        """Test processing a message with LLM integration."""
        # We'll use mocking to avoid actual LLM calls during tests
        with patch("app.llm_service.ollama") as mock_ollama, patch(
            "app.llm_service.LLMService.semantic_search"
        ) as mock_search, patch(
            "app.llm_service.LLMService.chat_completion"
        ) as mock_completion:
            # Mock ollama for LLMService initialization
            # Create proper mock objects that match ollama.list() structure
            class MockModel:
                def __init__(self, name):
                    self.model = name

            class MockListResponse:
                def __init__(self, models):
                    self.models = [MockModel(name) for name in models]

            mock_ollama.list.return_value = MockListResponse(
                ["qwen3:latest", "qwen2.5:3b", "nomic-embed-text:latest"]
            )
            mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

            # Mock ollama.chat for tool analysis and other operations
            mock_ollama.chat.return_value = {
                "message": {
                    "role": "assistant",
                    "content": '{"should_use_tools": true, "recommended_tools": [{"tool_name": "journal_search", "confidence": 0.8, "reason": "User asking about journal entries", "suggested_query": "journal entries"}], "analysis": "User wants to search journal entries"}',
                }
            }
            # Create a proper JournalEntry object for the mock
            from app.models import JournalEntry

            mock_entry = JournalEntry(
                id="20250503190939",
                title="Test Entry",
                content="This is a test entry for testing the chat feature.",
                created_at=datetime.now(),
            )

            # Mock the semantic search to return properly structured results
            mock_search.return_value = [
                {"entry": mock_entry, "similarity": 0.85, "entry_id": "20250503190939"}
            ]

            # Mock the LLM to return a properly structured response (like Ollama would)
            mock_completion.return_value = {
                "message": {
                    "role": "assistant",
                    "content": "This is a test response that references your "
                    "journal entry about the chat feature.",
                }
            }

            # Create a test session
            response = client.post(
                "/chat/sessions", json={"title": "Message Processing Test"}
            )
            assert response.status_code == 200
            session_id = response.json()["id"]

            # Process a message
            message_content = "Tell me about my journal entries"
            response = client.post(
                f"/chat/sessions/{session_id}/process",
                json={"content": message_content},
            )
            assert response.status_code == 200

            # Verify we got a response with expected structure
            response_data = response.json()
            assert "message" in response_data
            assert response_data["message"]["role"] == "assistant"
            assert len(response_data["message"]["content"]) > 0

            # Verify references were included
            assert "references" in response_data
            assert len(response_data["references"]) > 0
            assert response_data["references"][0]["entry_id"] == "20250503190939"

            # Clean up
            client.delete(f"/chat/sessions/{session_id}")

    def test_process_message_error_handling(self, client):
        """Test error handling in message processing."""
        # Create a session
        response = client.post("/chat/sessions", json={"title": "Error Handling Test"})
        assert response.status_code == 200
        session_id = response.json()["id"]

        # Test with non-existent session
        response = client.post(
            "/chat/sessions/nonexistent-id/process",
            json={"content": "This should fail"},
        )
        assert response.status_code == 404

        # Test with invalid message (empty content)
        response = client.post(
            f"/chat/sessions/{session_id}/process", json={"content": ""}
        )
        assert response.status_code in [400, 422]  # Validation error

        # Clean up
        client.delete(f"/chat/sessions/{session_id}")

    def test_conversation_context(self, client, mock_ollama):
        """Test multi-turn conversation with context."""
        # We'll use mocking to avoid actual LLM calls
        with patch("app.llm_service.LLMService.semantic_search") as mock_search, patch(
            "app.llm_service.LLMService.generate_response_with_model"
        ) as mock_completion:
            # Mock the semantic search to return dummy results
            mock_search.return_value = [
                {
                    "entry": {
                        "id": "20250509073557",
                        "title": "Journal App Progress",
                        "content": "Made progress on the chat feature.",
                        "created_at": datetime.now(),
                    },
                    "similarity": 0.9,
                }
            ]

            # Set up mock responses for a multi-turn conversation
            mock_completion.side_effect = [
                "Yes, you've been making progress on the chat feature.",
                "According to your journal, you worked on this yesterday.",
            ]

            # Create a test session
            response = client.post(
                "/chat/sessions", json={"title": "Conversation Context Test"}
            )
            assert response.status_code == 200
            session_id = response.json()["id"]

            # First message
            response = client.post(
                f"/chat/sessions/{session_id}/process",
                json={"content": "Have I been making progress on the app?"},
            )
            assert response.status_code == 200
            assert (
                "Yes, you've been making progress"
                in response.json()["message"]["content"]
            )

            # Second message should include context from first exchange
            response = client.post(
                f"/chat/sessions/{session_id}/process",
                json={"content": "When did I work on it?"},
            )
            assert response.status_code == 200
            assert "yesterday" in response.json()["message"]["content"]

            # Clean up
            client.delete(f"/chat/sessions/{session_id}")
