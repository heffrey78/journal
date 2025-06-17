"""
Tests for favorite summaries functionality in the Journal App.

This module tests both the API endpoints and the LLM service methods
related to saving and retrieving favorite summaries.
"""
import sys
from pathlib import Path
import pytest
import os
import shutil

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing required dependencies
try:
    from fastapi.testclient import TestClient
    from app.api import app, get_storage, get_llm_service
    from app.models import EntrySummary
    from app.storage import StorageManager
    from app.llm_service import LLMService

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    pytest.skip(f"Missing dependencies for API tests: {e}", allow_module_level=True)

if DEPENDENCIES_AVAILABLE:
    client = TestClient(app)

    # Test data directory
    TEST_DATA_DIR = "./test_journal_data"

    @pytest.fixture(scope="module", autouse=True)
    def setup_test_environment():
        """Setup test environment with clean test data directory."""
        # Clean up old test data
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(os.path.join(TEST_DATA_DIR, "entries"), exist_ok=True)

        # Replace the storage manager initialization to use test directory
        original_init = StorageManager.__init__

        def test_init(self):
            # Initialize with test directory - this will call the real __init__ with the test directory
            original_init(self, TEST_DATA_DIR)

        StorageManager.__init__ = test_init

        # Create a mock LLM service for testing
        test_storage = StorageManager()

        class MockLLMService(LLMService):
            def __init__(self):
                self.storage_manager = test_storage
                self.model_name = "mock-model"

            def summarize_entry(
                self, content, prompt_type="default", progress_callback=None
            ):
                summary = EntrySummary(
                    summary=f"Mock summary for prompt type: {prompt_type}",
                    key_topics=["mock", "testing", prompt_type],
                    mood="neutral",
                )
                return summary

        # Override dependencies
        def get_test_storage():
            return test_storage

        def get_test_llm():
            return MockLLMService()

        app.dependency_overrides[get_storage] = get_test_storage
        app.dependency_overrides[get_llm_service] = get_test_llm

        yield

        # Remove overrides
        app.dependency_overrides.clear()
        StorageManager.__init__ = original_init


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason="API test dependencies not available"
)
class TestFavoriteSummaries:
    """Test favorite summaries functionality."""

    def setup_method(self):
        """Set up test data before each test method."""
        # Create a test entry
        entry_data = {
            "title": "Test Entry for Summaries",
            "content": "This is a test entry for testing summary functionality",
            "tags": ["test", "summaries"],
        }
        response = client.post("/entries/", json=entry_data)
        assert (
            response.status_code == 200
        ), f"Failed to create test entry: {response.text}"
        self.entry_id = response.json()["id"]

        # Create a sample summary
        self.test_summary = {
            "summary": "This is a test summary of the entry content",
            "key_topics": ["testing", "summaries", "functionality"],
            "mood": "neutral",
            "prompt_type": "test",
        }

    def test_save_favorite_summary(self):
        """Test saving a summary as a favorite."""
        # Save the summary as a favorite
        response = client.post(
            f"/entries/{self.entry_id}/summaries/favorite", json=self.test_summary
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data

    def test_get_favorite_summaries(self):
        """Test retrieving favorite summaries for an entry."""
        # First save a summary
        client.post(
            f"/entries/{self.entry_id}/summaries/favorite", json=self.test_summary
        )

        # Then try to retrieve it
        response = client.get(f"/entries/{self.entry_id}/summaries/favorite")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check the content of the first summary
        summary = data[0]
        assert "summary" in summary
        assert "key_topics" in summary
        assert "mood" in summary
        assert isinstance(summary["key_topics"], list)

    def test_multiple_favorite_summaries(self):
        """Test saving and retrieving multiple favorite summaries."""
        # Create and save multiple summaries with different prompt types
        summaries = [
            {
                "summary": "Default summary with basic analysis",
                "key_topics": ["basic", "overview"],
                "mood": "neutral",
                "prompt_type": "default",
            },
            {
                "summary": "Detailed analysis with in-depth insights",
                "key_topics": ["detailed", "analysis", "insights"],
                "mood": "analytical",
                "prompt_type": "detailed",
            },
            {
                "summary": "Creative interpretation of the content",
                "key_topics": ["creative", "interpretation"],
                "mood": "imaginative",
                "prompt_type": "creative",
            },
        ]

        # Save each summary
        for summary in summaries:
            client.post(f"/entries/{self.entry_id}/summaries/favorite", json=summary)

        # Retrieve all summaries
        response = client.get(f"/entries/{self.entry_id}/summaries/favorite")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(summaries)

        # Check that we have summaries with different prompt types
        prompt_types = [s.get("prompt_type") for s in data]
        assert "default" in prompt_types
        assert "detailed" in prompt_types
        assert "creative" in prompt_types

    def test_nonexistent_entry(self):
        """Test behavior with non-existent entries."""
        # Try to get favorites for a non-existent entry
        response = client.get("/entries/nonexistent/summaries/favorite")
        assert response.status_code == 404

        # Try to save a favorite for a non-existent entry
        response = client.post(
            "/entries/nonexistent/summaries/favorite", json=self.test_summary
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
