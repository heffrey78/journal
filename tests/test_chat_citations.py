"""
Tests for the chat citation system.
"""
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.chat_service import ChatService
from app.models import ChatMessage, ChatSession, EntryReference, ChatConfig


class TestChatCitations:
    """Tests for the chat citation system."""

    def test_enhance_citations_adds_note_when_missing(self):
        """Test that _enhance_citations adds a note when citations are missing."""
        # Create mock objects
        chat_storage = MagicMock()
        llm_service = MagicMock()
        chat_service = ChatService(chat_storage, llm_service)

        # Create sample references
        references = [
            EntryReference(
                message_id="test-msg-1",
                entry_id="20250503190939",
                similarity_score=0.85,
                entry_title="Test Entry",
                entry_snippet="This is a test entry content snippet.",
            )
        ]

        # Test response without citations
        response_text = "This is a response without any citations."
        result = chat_service._enhance_citations(response_text, references)

        # Verify a note was added
        assert result != response_text
        assert "Note: This response was informed by your journal entry from" in result
        assert "May 03, 2025" in result

    def test_enhance_citations_leaves_intact_when_present(self):
        """Test that _enhance_citations doesn't modify text when
        citations are present."""
        # Create mock objects
        chat_storage = MagicMock()
        llm_service = MagicMock()
        chat_service = ChatService(chat_storage, llm_service)

        # Create sample references
        references = [
            EntryReference(
                message_id="test-msg-1",
                entry_id="20250503190939",
                similarity_score=0.85,
                entry_title="Test Entry 1",
                entry_snippet="This is a test entry content snippet.",
            ),
            EntryReference(
                message_id="test-msg-1",
                entry_id="20250504072752",
                similarity_score=0.75,
                entry_title="Test Entry 2",
                entry_snippet="This is another test entry content snippet.",
            ),
        ]

        # Test response with citations
        response_text = (
            "According to your entry [1], you mentioned something "
            "important. And in your entry [2], you noted something else."
        )
        result = chat_service._enhance_citations(response_text, references)

        # Verify the text was not modified
        assert result == response_text

    def test_format_references_for_context(self):
        """Test that references are formatted correctly for context."""
        # Create mock objects
        chat_storage = MagicMock()
        llm_service = MagicMock()
        chat_service = ChatService(chat_storage, llm_service)

        # Create sample references
        references = [
            EntryReference(
                message_id="test-msg-1",
                entry_id="20250503190939",
                similarity_score=0.85,
                entry_title="Test Entry 1",
                entry_snippet="This is a test entry content snippet.",
                chunk_index=0,
            ),
            EntryReference(
                message_id="test-msg-1",
                entry_id="20250504072752",
                similarity_score=0.75,
                entry_title="Test Entry 2",
                entry_snippet="This is another test entry content snippet.",
                chunk_index=1,
            ),
        ]

        # Format references
        formatted = chat_service._format_references_for_context(references)

        # Verify format
        assert "[1]" in formatted  # Check for reference number
        assert "Entry ID: 20250503190939" in formatted
        assert "Test Entry 1" in formatted
        assert "[2]" in formatted
        assert "Entry ID: 20250504072752" in formatted
        assert "Test Entry 2" in formatted
        assert "May 03, 2025" in formatted
        assert "May 04, 2025" in formatted
        assert "Relevance: 0.85" in formatted
        assert "Relevance: 0.75" in formatted

    @patch("app.chat_service.ChatService._generate_response")
    def test_process_message_instructions_for_citations(self, mock_generate):
        """Test that process_message passes references to _generate_response."""
        # Create mock objects
        chat_storage = MagicMock()
        llm_service = MagicMock()
        chat_service = ChatService(chat_storage, llm_service)

        # Setup mock data
        session_id = "test-session"
        session = ChatSession(
            id=session_id, title="Test Session", created_at=datetime.now()
        )
        message = ChatMessage(
            id="test-msg",
            session_id=session_id,
            role="user",
            content="Tell me about my journal entries",
            created_at=datetime.now(),
        )
        config = ChatConfig()
        references = [
            EntryReference(
                message_id="test-msg",
                entry_id="20250503190939",
                similarity_score=0.85,
                entry_title="Test Entry",
                entry_snippet="This is a test entry content snippet.",
            )
        ]

        # Mock necessary methods
        chat_storage.get_session.return_value = session
        chat_storage.get_chat_config.return_value = config
        chat_storage.add_message.return_value = message

        # Spy on _format_references_for_context instead of mocking it
        format_spy = MagicMock(wraps=chat_service._format_references_for_context)
        chat_service._format_references_for_context = format_spy

        # Mock entry retrieval to return our test references
        chat_service._enhanced_entry_retrieval = MagicMock(return_value=references)

        # Mock _generate_response to return a test message
        mock_generate.return_value = "This is a test response with citation [1]."

        # Call the process_message method
        chat_service.process_message(message)

        # Verify that _generate_response was called with the right parameters
        mock_generate.assert_called_once()

        # The references should be passed to _generate_response as the second argument
        args, _ = mock_generate.call_args
        conversation, refs, sess, conf = args

        # Verify that references were passed correctly
        assert refs == references

        # Test that _enhance_citations is called with responses that have references
        response = chat_service._enhance_citations("Test response", references)
        assert "Note: This response was informed by your journal entry from" in response
