"""
Tests for the chat context management functionality.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import tempfile

from app.models import ChatSession, ChatMessage, ChatConfig
from app.storage.chat import ChatStorage
from app.chat_service import ChatService


class TestContextManagement(unittest.TestCase):
    """Tests for context management features in the chat service."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temp dir for test storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = self.temp_dir.name

        # Mock LLM service
        self.mock_llm_service = MagicMock()
        self.mock_llm_service.chat_completion.return_value = {
            "choices": [{"message": {"content": "Test summary of the conversation"}}]
        }

        # Create real storage with fake directory
        self.chat_storage = ChatStorage(self.storage_dir)

        # Mock the storage methods as needed
        self.chat_storage.get_chat_config = MagicMock(
            return_value=self._get_test_config()
        )
        self.chat_storage.update_session = MagicMock(return_value=None)

        # Create the chat service with our mocked dependencies
        self.chat_service = ChatService(self.chat_storage, self.mock_llm_service)

    def tearDown(self):
        """Clean up after each test."""
        self.temp_dir.cleanup()

    def _get_test_config(self):
        """Get a test configuration for chat."""
        return ChatConfig(
            id="default",
            system_prompt="You are a test assistant",
            max_context_tokens=2000,
            conversation_summary_threshold=1000,
            context_window_size=5,
            use_context_windowing=True,
            min_messages_for_summary=3,
        )

    def _create_test_session(self):
        """Create a test chat session."""
        session = ChatSession(
            id="test-session",
            title="Test Session",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_accessed=datetime.now(),
        )
        return session

    def _create_test_messages(self, count=10):
        """Create a list of test messages."""
        messages = []
        for i in range(count):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Test message {i+1}"

            msg = ChatMessage(
                id=f"msg-{i+1}",
                session_id="test-session",
                role=role,
                content=content,
                created_at=datetime.now(),
            )
            messages.append(msg)
        return messages

    def test_estimate_token_count(self):
        """Test the token count estimation function."""
        # Create messages with known content lengths
        messages = [
            ChatMessage(
                id="msg-1",
                session_id="test",
                role="user",
                content="This is exactly twenty chars",  # 20 chars
                created_at=datetime.now(),
            ),
            ChatMessage(
                id="msg-2",
                session_id="test",
                role="assistant",
                content="This is a longer message with approximately forty characters",
                created_at=datetime.now(),
            ),
        ]

        # Expected tokens: (20 / 4) + (40 / 4) = 5 + 10 = 15
        expected_tokens = 15

        # Test the method
        result = self.chat_service._estimate_token_count(messages)

        # Check the result
        self.assertEqual(result, expected_tokens)

        # Test with explicit token count
        messages[0].token_count = 10  # Override estimation
        # Expected: 10 (explicit) + 10 (estimated) = 20
        result = self.chat_service._estimate_token_count(messages)
        self.assertEqual(result, 20)

    def test_apply_context_windowing_below_threshold(self):
        """Test that windowing is not applied when messages are below window size."""
        # Create a small set of messages (less than context_window_size)
        messages = self._create_test_messages(count=3)  # Only 3 messages
        session = self._create_test_session()
        config = self._get_test_config()  # Window size is 5

        # Base conversation with system message
        base_conversation = [{"role": "system", "content": "You are a test assistant"}]

        # Mock the get_session method
        self.chat_storage.get_session = MagicMock(return_value=session)

        # Apply windowing
        result = self.chat_service._apply_context_windowing(
            base_conversation, messages, session, config
        )

        # Since we have fewer messages than window_size, all messages should be included
        # Base conversation (1) + all messages (3) = 4 messages total
        self.assertEqual(len(result), 4)

    def test_apply_context_windowing_with_existing_summary(self):
        """Test that existing summary is used when available."""
        # Create messages (more than window_size)
        messages = self._create_test_messages(count=10)  # 10 messages
        session = self._create_test_session()

        # Add an existing summary to the session
        existing_summary = "This is a pre-existing summary of the conversation"
        session.context_summary = existing_summary

        config = self._get_test_config()  # Window size is 5

        # Base conversation with system message
        base_conversation = [{"role": "system", "content": "You are a test assistant"}]

        # Mock the get_session method
        self.chat_storage.get_session = MagicMock(return_value=session)

        # Apply windowing
        result = self.chat_service._apply_context_windowing(
            base_conversation, messages, session, config
        )

        # Check that the result contains:
        # 1. The system message
        # 2. The summary as a system message
        # 3. The last 5 messages (window_size)
        self.assertEqual(len(result), 7)  # system + summary + 5 latest messages

        # Verify the summary was included
        summary_included = False
        for item in result:
            if item["role"] == "system" and existing_summary in item["content"]:
                summary_included = True
                break

        self.assertTrue(
            summary_included, "Existing summary should be included in context"
        )

    def test_apply_context_windowing_generate_new_summary(self):
        """Test that a new summary is generated when needed."""
        # Create messages (more than window_size)
        messages = self._create_test_messages(count=10)  # 10 messages
        session = self._create_test_session()
        config = self._get_test_config()  # Window size is 5

        # Ensure no existing summary
        session.context_summary = None

        # Base conversation with system message
        base_conversation = [{"role": "system", "content": "You are a test assistant"}]

        # Mock behavior
        self.chat_storage.get_session = MagicMock(return_value=session)

        # Set up the mock for _generate_conversation_summary
        test_summary = "This is a new test summary"
        self.chat_service._generate_conversation_summary = MagicMock(
            return_value=test_summary
        )

        # Apply windowing
        result = self.chat_service._apply_context_windowing(
            base_conversation, messages, session, config
        )

        # Check that the summary generation was called with the right parameters
        # It should be called with the first 5 messages (all except window_size)
        self.chat_service._generate_conversation_summary.assert_called_once()
        args, _ = self.chat_service._generate_conversation_summary.call_args
        self.assertEqual(len(args[0]), 5)  # First 5 messages

        # Verify the session was updated with the new summary
        self.chat_storage.update_session.assert_called_once()

        # Verify the summary is in the result
        summary_included = False
        for item in result:
            if item["role"] == "system" and test_summary in item["content"]:
                summary_included = True
                break

        self.assertTrue(
            summary_included, "Generated summary should be included in context"
        )

    def test_generate_conversation_summary(self):
        """Test generation of conversation summary."""
        # Create test messages to summarize
        messages = self._create_test_messages(count=4)
        config = self._get_test_config()

        # Set up mock response for LLM
        expected_summary = "Test summary of the conversation"
        self.mock_llm_service.chat_completion.return_value = {
            "choices": [{"message": {"content": expected_summary}}]
        }

        # Generate summary
        result = self.chat_service._generate_conversation_summary(messages, config)

        # Verify LLM was called correctly
        self.mock_llm_service.chat_completion.assert_called_once()

        # The conversation history should include our messages plus the summary prompt
        call_args = self.mock_llm_service.chat_completion.call_args[1]
        self.assertEqual(len(call_args["messages"]), len(messages) + 1)

        # Verify the summary prompt was appended
        self.assertEqual(call_args["messages"][-1]["content"], config.summary_prompt)

        # Verify the result
        self.assertEqual(result, expected_summary)

    def test_update_session_summary(self):
        """Test the public method to update session summary."""
        # Create session and messages
        session_id = "test-session"
        session = self._create_test_session()
        messages = self._create_test_messages(count=10)

        # Configure mocks
        self.chat_storage.get_session = MagicMock(return_value=session)
        self.chat_storage.get_messages = MagicMock(return_value=messages)

        # Set up mock for summary generation
        test_summary = "This is a test summary"
        self.chat_service._generate_conversation_summary = MagicMock(
            return_value=test_summary
        )

        # Call the method
        result = self.chat_service.update_session_summary(session_id)

        # Verify it succeeded
        self.assertTrue(result)

        # Verify the summary was generated and session was updated
        self.chat_service._generate_conversation_summary.assert_called_once()
        self.chat_storage.update_session.assert_called_once()

        # Verify session summary was updated
        updated_session = self.chat_storage.update_session.call_args[0][0]
        self.assertEqual(updated_session.context_summary, test_summary)

    def test_clear_session_summary(self):
        """Test clearing the session summary."""
        # Create session with existing summary
        session_id = "test-session"
        session = self._create_test_session()
        session.context_summary = "Existing summary"

        # Configure mocks
        self.chat_storage.get_session = MagicMock(return_value=session)

        # Call the method
        result = self.chat_service.clear_session_summary(session_id)

        # Verify it succeeded
        self.assertTrue(result)

        # Verify session was updated
        self.chat_storage.update_session.assert_called_once()

        # Verify session summary was cleared
        updated_session = self.chat_storage.update_session.call_args[0][0]
        self.assertIsNone(updated_session.context_summary)

    @patch("app.chat_service.ChatService._apply_context_windowing")
    def test_prepare_conversation_history_with_windowing(self, mock_apply_windowing):
        """Test that prepare_conversation_history applies windowing when needed."""
        # Create test data
        session_id = "test-session"
        session = self._create_test_session()
        messages = self._create_test_messages(count=15)  # Many messages
        config = self._get_test_config()

        # Configure mocks
        self.chat_storage.get_session = MagicMock(return_value=session)
        self.chat_storage.get_messages = MagicMock(return_value=messages)

        # Mock estimate_token_count to return a value over threshold
        self.chat_service._estimate_token_count = MagicMock(
            return_value=1500
        )  # Over threshold of 1000

        # Mock apply_context_windowing to return a simple result
        expected_result = [
            {"role": "system", "content": "Test system"},
            {"role": "user", "content": "Test user"},
        ]
        mock_apply_windowing.return_value = expected_result

        # Call the method
        result = self.chat_service._prepare_conversation_history(session_id, config)

        # Verify windowing was applied
        mock_apply_windowing.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_prepare_conversation_history_no_windowing(self):
        """Test prepare_conversation_history without windowing."""
        # Create test data
        session_id = "test-session"
        messages = self._create_test_messages(
            count=3
        )  # Few messages, under min_messages_for_summary
        config = self._get_test_config()

        # Configure mocks
        self.chat_storage.get_messages = MagicMock(return_value=messages)

        # Call the method
        result = self.chat_service._prepare_conversation_history(session_id, config)

        # Verify correct structure: system message + all 3 messages
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["role"], "system")

        # Verify all messages are included
        for i, msg in enumerate(messages):
            self.assertEqual(result[i + 1]["role"], msg.role)
            self.assertEqual(result[i + 1]["content"], msg.content)


if __name__ == "__main__":
    unittest.main()
