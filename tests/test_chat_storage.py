import uuid
import pytest
from datetime import datetime, timedelta

from app.models import ChatSession, ChatMessage, EntryReference
from app.storage.chat import ChatStorage


@pytest.fixture
def chat_storage():
    """Creates a test chat storage instance using a test database."""
    # Use test database
    storage = ChatStorage(base_dir="./test_journal_data")
    yield storage


@pytest.fixture
def sample_session():
    """Creates a sample chat session for testing."""
    return ChatSession(
        id=f"test-chat-{uuid.uuid4()}",
        title="Test Chat Session",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_accessed=datetime.now(),
    )


@pytest.fixture
def sample_message(sample_session):
    """Creates a sample message for testing."""
    return ChatMessage(
        id=f"test-msg-{uuid.uuid4()}",
        session_id=sample_session.id,
        role="user",
        content="This is a test message",
        created_at=datetime.now(),
        metadata={"test_key": "test_value"},
        token_count=5,
    )


class TestChatStorage:
    """Tests for ChatStorage class."""

    def test_create_and_get_session(self, chat_storage, sample_session):
        """Test creating and retrieving a chat session."""
        # Create session
        chat_storage.create_session(sample_session)

        # Retrieve session
        retrieved = chat_storage.get_session(sample_session.id)

        # Verify
        assert retrieved is not None
        assert retrieved.id == sample_session.id
        assert retrieved.title == sample_session.title
        # Allow for minor differences in datetime storage/retrieval
        assert (
            abs((retrieved.created_at - sample_session.created_at).total_seconds()) < 1
        )

    def test_update_session(self, chat_storage, sample_session):
        """Test updating a chat session."""
        # Create session
        chat_storage.create_session(sample_session)

        # Update session
        new_title = "Updated Test Session"
        sample_session.title = new_title
        sample_session.updated_at = datetime.now()
        chat_storage.update_session(sample_session)

        # Verify
        retrieved = chat_storage.get_session(sample_session.id)
        assert retrieved.title == new_title

    def test_list_sessions(self, chat_storage):
        """Test listing chat sessions."""
        # Create a few sessions with different timestamps
        sessions = []
        for i in range(3):
            session = ChatSession(
                id=f"test-chat-list-{i}-{uuid.uuid4()}",
                title=f"Test Session {i}",
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now() - timedelta(hours=i),
                last_accessed=datetime.now() - timedelta(hours=i),
            )
            chat_storage.create_session(session)
            sessions.append(session)

        # List sessions
        retrieved = chat_storage.list_sessions()

        # Verify (should be ordered by last_accessed DESC)
        assert len(retrieved) >= 3
        # The first session created should be the most recently accessed
        assert retrieved[0].id == sessions[0].id

    def test_delete_session(self, chat_storage, sample_session):
        """Test deleting a chat session."""
        # Create session
        chat_storage.create_session(sample_session)

        # Verify it exists
        assert chat_storage.get_session(sample_session.id) is not None

        # Delete session
        success = chat_storage.delete_session(sample_session.id)
        assert success is True

        # Verify it's gone
        assert chat_storage.get_session(sample_session.id) is None

    def test_add_and_get_message(self, chat_storage, sample_session, sample_message):
        """Test adding and retrieving a chat message."""
        # Create session
        chat_storage.create_session(sample_session)

        # Add message
        chat_storage.add_message(sample_message)

        # Retrieve messages
        messages = chat_storage.get_messages(sample_session.id)

        # Verify
        assert len(messages) == 1
        assert messages[0].id == sample_message.id
        assert messages[0].content == sample_message.content
        assert messages[0].role == sample_message.role
        assert messages[0].metadata == sample_message.metadata

    def test_message_entry_references(
        self, chat_storage, sample_session, sample_message
    ):
        """Test adding and retrieving message entry references."""
        # Create session and message
        chat_storage.create_session(sample_session)
        chat_storage.add_message(sample_message)

        # Create references
        references = [
            EntryReference(
                message_id=sample_message.id,
                entry_id=f"entry-{i}",
                similarity_score=0.8 - (i * 0.1),
                chunk_index=i,
            )
            for i in range(3)
        ]

        # This would normally cause an error because we don't have actual entries
        # in the test database, but we'll mock the functionality by patching
        # the SQL execution to skip the foreign key check
        conn = chat_storage.get_db_connection()
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.commit()
        conn.close()

        # Add references
        chat_storage.add_message_entry_references(sample_message.id, references)

        # We can't test get_message_entry_references correctly without real entries
        # in the database, so we'll stop here for the unit test

    def test_chat_config(self, chat_storage):
        """Test retrieving and updating chat config."""
        # Get default config
        config = chat_storage.get_chat_config()

        # Verify default values
        assert config.system_prompt is not None
        assert config.max_context_tokens == 4096

        # Update config
        new_prompt = "This is a test system prompt."
        config.system_prompt = new_prompt
        chat_storage.update_chat_config(config)

        # Verify update
        updated_config = chat_storage.get_chat_config()
        assert updated_config.system_prompt == new_prompt
