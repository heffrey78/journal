"""
Automated tests for Journal API endpoints.

This module uses FastAPI's TestClient to test the API endpoints
without requiring a running server.
"""
import sys
from pathlib import Path
import pytest
import os
import shutil
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing required dependencies
try:
    from fastapi.testclient import TestClient
    from app.api import app

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    pytest.skip(f"Missing dependencies for API tests: {e}", allow_module_level=True)

if DEPENDENCIES_AVAILABLE:
    # Test client
    client = TestClient(app)

    # Test data directory
    TEST_DATA_DIR = "./test_journal_data"

    @pytest.fixture(scope="module", autouse=True)
    def setup_test_environment():
        """Setup test environment with clean test data directory."""
        # Configure app to use test data
        from app.storage import StorageManager

        StorageManager.__init__ = (
            lambda self: setattr(self, "base_dir", TEST_DATA_DIR)
            or setattr(self, "entries_dir", os.path.join(TEST_DATA_DIR, "entries"))
            or setattr(self, "db_path", os.path.join(TEST_DATA_DIR, "journal.db"))
            or os.makedirs(self.entries_dir, exist_ok=True)
            or self._init_sqlite()
        )

        # Clean up old test data
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(os.path.join(TEST_DATA_DIR, "entries"), exist_ok=True)

        yield

        # Clean up after tests complete
        # Comment this out if you want to inspect test data
        # if os.path.exists(TEST_DATA_DIR):
        #     shutil.rmtree(TEST_DATA_DIR)


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason="API test dependencies not available"
)
class TestAPIEndpoints:
    """Test Journal API endpoints."""

    def test_api_info(self):
        """Test /api/info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Journal API"
        assert "version" in data

    def test_create_entry(self):
        """Test creating a journal entry."""
        entry_data = {
            "title": "Test Entry",
            "content": "This is a test entry",
            "tags": ["test", "api"],
        }
        response = client.post("/entries/", json=entry_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == entry_data["title"]
        assert data["content"] == entry_data["content"]
        assert data["tags"] == entry_data["tags"]
        assert "id" in data

        # Store ID for later tests
        self.entry_id = data["id"]

    def test_get_entry(self):
        """Test retrieving a specific entry."""
        # Get the entry we created earlier
        response = client.get(f"/entries/{self.entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.entry_id
        assert data["title"] == "Test Entry"

        # Try to get a non-existent entry
        response = client.get("/entries/nonexistent")
        assert response.status_code == 404

    def test_list_entries(self):
        """Test listing journal entries."""
        response = client.get("/entries/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Test pagination
        response = client.get("/entries/?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_update_entry(self):
        """Test updating an entry."""
        update_data = {
            "title": "Updated Test Entry",
            "tags": ["test", "api", "updated"],
        }
        response = client.patch(f"/entries/{self.entry_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["tags"] == update_data["tags"]
        assert data["content"] == "This is a test entry"  # Unchanged

        # Verify update was persisted
        response = client.get(f"/entries/{self.entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]

    def test_text_search(self):
        """Test text search functionality."""
        # Create two more entries for search testing
        entries = [
            {
                "title": "Apple Recipes",
                "content": "How to make apple pie and apple sauce.",
                "tags": ["food", "recipes"],
            },
            {
                "title": "Technology News",
                "content": "Latest news about smartphones and computers.",
                "tags": ["tech", "news"],
            },
        ]

        for entry in entries:
            client.post("/entries/", json=entry)

        # Search for entries containing "apple"
        response = client.get("/entries/search/?query=apple")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        apple_entry = next((e for e in data if e["title"] == "Apple Recipes"), None)
        assert apple_entry is not None

        # Search for entries containing "test"
        response = client.get("/entries/search/?query=test")
        assert response.status_code == 200
        data = response.json()
        test_entry = next((e for e in data if "test" in e["title"].lower()), None)
        assert test_entry is not None

    def test_tag_endpoints(self):
        """Test tag-related endpoints."""
        # Get all tags
        response = client.get("/tags/")
        assert response.status_code == 200
        tags = response.json()
        assert isinstance(tags, list)
        assert "test" in tags
        assert "api" in tags

        # Get entries by tag
        response = client.get("/tags/test/entries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all("test" in entry["tags"] for entry in data)

    def test_stats_endpoint(self):
        """Test the statistics endpoint."""
        response = client.get("/stats/")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert data["total_entries"] >= 3  # We created at least 3 entries
        assert "most_used_tags" in data
        assert isinstance(data["most_used_tags"], list)

    def test_advanced_search(self):
        """Test advanced search with filters."""
        # Create another entry with specific date for testing
        entry_with_date = {
            "title": "Special Entry",
            "content": "This entry has a specific date for testing",
            "tags": ["special", "test"],
            "created_at": datetime(2025, 5, 1).isoformat(),
        }
        client.post("/entries/", json=entry_with_date)

        # Test search with date filter
        search_params = {
            "query": "specific",
            "date_from": "2025-05-01T00:00:00",
            "date_to": "2025-05-02T00:00:00",
            "tags": ["special"],
        }
        response = client.post("/entries/search/", json=search_params)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(entry["title"] == "Special Entry" for entry in data)

        # Test search with tags only
        tag_search = {"query": "", "tags": ["special"]}
        response = client.post("/entries/search/", json=tag_search)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        special_entries = [e for e in data if "special" in e["tags"]]
        assert len(special_entries) >= 1

    def test_delete_entry(self):
        """Test deleting an entry."""
        # Create an entry specifically for deletion
        delete_entry = {
            "title": "Delete Me",
            "content": "This entry will be deleted",
        }
        response = client.post("/entries/", json=delete_entry)
        delete_id = response.json()["id"]

        # Verify entry exists
        response = client.get(f"/entries/{delete_id}")
        assert response.status_code == 200

        # Delete the entry
        response = client.delete(f"/entries/{delete_id}")
        assert response.status_code == 200

        # Verify it's gone
        response = client.get(f"/entries/{delete_id}")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
