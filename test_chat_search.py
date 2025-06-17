"""
Test chat search functionality.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from main import app
from app.storage.chat import ChatStorage
from app.models import ChatSession, ChatMessage

client = TestClient(app)


@pytest.fixture
def chat_storage():
    """Create a test chat storage instance."""
    storage = ChatStorage("./test_journal_data")
    storage._init_tables()
    return storage


@pytest.fixture
def sample_session(chat_storage):
    """Create a sample chat session for testing."""
    session = ChatSession(
        title="Test Chat Session",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_accessed=datetime.now(),
    )
    return chat_storage.create_session(session)


@pytest.fixture
def sample_messages(chat_storage, sample_session):
    """Create sample messages for testing."""
    messages = [
        ChatMessage(
            session_id=sample_session.id,
            role="user",
            content="Tell me about artificial intelligence and machine learning",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=sample_session.id,
            role="assistant",
            content="Artificial intelligence is a broad field that encompasses machine learning, deep learning, and neural networks. It aims to create systems that can perform tasks typically requiring human intelligence.",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=sample_session.id,
            role="user",
            content="What are the applications of AI in healthcare?",
            created_at=datetime.now(),
        ),
        ChatMessage(
            session_id=sample_session.id,
            role="assistant",
            content="AI has numerous applications in healthcare including medical imaging, drug discovery, personalized treatment plans, and diagnostic assistance. Machine learning algorithms can analyze medical data to identify patterns and make predictions.",
            created_at=datetime.now(),
        ),
    ]

    for message in messages:
        chat_storage.add_message(message)

    return messages


def test_search_sessions_endpoint():
    """Test the chat sessions search endpoint."""
    # First create a test session with messages
    response = client.post(
        "/chat/sessions",
        json={"title": "AI Discussion Session", "temporal_filter": None},
    )
    assert response.status_code == 200
    session_data = response.json()
    session_id = session_data["id"]

    # Add some test messages
    client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "What is machine learning and how does it work?"},
    )

    # Now test searching
    response = client.get("/chat/search?q=machine learning&limit=10&offset=0")
    assert response.status_code == 200

    search_results = response.json()
    assert "results" in search_results
    assert "total" in search_results
    assert "query" in search_results
    assert search_results["query"] == "machine learning"


def test_search_within_session_endpoint():
    """Test searching within a specific session."""
    # Create a test session
    response = client.post(
        "/chat/sessions",
        json={
            "title": "Test Session for Search",
        },
    )
    assert response.status_code == 200
    session_id = response.json()["id"]

    # Add messages
    client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "Tell me about Python programming"},
    )
    client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "What are the best practices for testing?"},
    )

    # Search within the session
    response = client.get(f"/chat/sessions/{session_id}/search?q=Python&limit=10")
    assert response.status_code == 200

    results = response.json()
    assert isinstance(results, list)


def test_chat_storage_search_sessions(chat_storage, sample_session, sample_messages):
    """Test the ChatStorage search_sessions method."""
    # Test basic search
    results = chat_storage.search_sessions(
        query="artificial intelligence", limit=10, offset=0
    )

    assert len(results) > 0
    assert any(session.id == sample_session.id for session in results)

    # Test search with no results
    results = chat_storage.search_sessions(
        query="nonexistentquery12345", limit=10, offset=0
    )

    assert len(results) == 0


def test_chat_storage_search_messages_in_session(
    chat_storage, sample_session, sample_messages
):
    """Test the ChatStorage search_messages_in_session method."""
    # Test search within session
    results = chat_storage.search_messages_in_session(
        session_id=sample_session.id, query="machine learning"
    )

    assert len(results) > 0
    assert any("machine learning" in msg.content.lower() for msg in results)

    # Test search with no results
    results = chat_storage.search_messages_in_session(
        session_id=sample_session.id, query="nonexistentquery12345"
    )

    assert len(results) == 0


def test_search_count_results(chat_storage, sample_session, sample_messages):
    """Test the count_search_results method."""
    # Test counting search results
    count = chat_storage.count_search_results(query="artificial intelligence")

    assert count > 0

    # Test count with no results
    count = chat_storage.count_search_results(query="nonexistentquery12345")

    assert count == 0


def test_search_with_date_filters(chat_storage, sample_session, sample_messages):
    """Test search functionality with date filters."""
    # Test search with date range
    today = datetime.now().isoformat()
    yesterday = datetime.now().replace(day=datetime.now().day - 1).isoformat()

    results = chat_storage.search_sessions(
        query="artificial", date_from=yesterday, date_to=today
    )

    # Should return results since our test session was created today
    assert len(results) > 0


def test_search_sorting(chat_storage, sample_session, sample_messages):
    """Test search result sorting."""
    # Test sorting by relevance (default)
    results_relevance = chat_storage.search_sessions(
        query="intelligence", sort_by="relevance"
    )

    # Test sorting by date
    results_date = chat_storage.search_sessions(query="intelligence", sort_by="date")

    # Test sorting by title
    results_title = chat_storage.search_sessions(query="intelligence", sort_by="title")

    # All should return results
    assert len(results_relevance) > 0
    assert len(results_date) > 0
    assert len(results_title) > 0


def test_rebuild_search_index(chat_storage, sample_session, sample_messages):
    """Test rebuilding the search index."""
    # This should not raise an exception
    chat_storage.rebuild_search_index()

    # Search should still work after rebuilding
    results = chat_storage.search_sessions(query="artificial intelligence")

    assert len(results) > 0


def test_search_api_error_handling():
    """Test error handling in search endpoints."""
    # Test search with non-existent session
    response = client.get("/chat/sessions/nonexistent-session/search?q=test")
    assert response.status_code == 404

    # Test search with empty query
    response = client.get("/chat/search?q=&limit=10&offset=0")
    assert response.status_code == 200
    # Should handle empty query gracefully


def test_search_pagination():
    """Test search result pagination."""
    # Create multiple sessions to test pagination
    session_ids = []
    for i in range(5):
        response = client.post(
            "/chat/sessions", json={"title": f"Test Session {i} about programming"}
        )
        assert response.status_code == 200
        session_ids.append(response.json()["id"])

    # Test first page
    response = client.get("/chat/search?q=programming&limit=2&offset=0")
    assert response.status_code == 200

    results = response.json()
    assert len(results["results"]) <= 2
    assert "has_next" in results
    assert "has_previous" in results

    # Test second page
    response = client.get("/chat/search?q=programming&limit=2&offset=2")
    assert response.status_code == 200

    results_page2 = response.json()
    assert len(results_page2["results"]) <= 2


if __name__ == "__main__":
    pytest.main([__file__])
