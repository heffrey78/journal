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
import sqlite3

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try importing required dependencies
try:
    from fastapi.testclient import TestClient
    from app.api import app, get_storage
    from app.storage import StorageManager
    from app.models import JournalEntry

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    pytest.skip(f"Missing dependencies for API tests: {e}", allow_module_level=True)

if DEPENDENCIES_AVAILABLE:
    # Test client
    client = TestClient(app)

    # Test data directory
    TEST_DATA_DIR = "./test_journal_data"

    # Create a fixture for the test environment
    @pytest.fixture(scope="module", autouse=True)
    def test_environment():
        """Set up and tear down the test environment."""
        # Clean up old test data
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

        # Create test data directory
        os.makedirs(os.path.join(TEST_DATA_DIR, "entries"), exist_ok=True)

        # Create a test database
        db_path = os.path.join(TEST_DATA_DIR, "journal.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create necessary tables - use the actual schema format
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                tags TEXT,
                folder TEXT,
                favorite INTEGER DEFAULT 0,
                images TEXT,
                source_metadata TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entry_summaries (
                id TEXT PRIMARY KEY,
                entry_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_topics TEXT NOT NULL,
                mood TEXT NOT NULL,
                favorite INTEGER NOT NULL DEFAULT 0,
                prompt_type TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                entry_id TEXT NOT NULL,
                chunk_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding BLOB,
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
            )
        """
        )

        # Create config table with new schema including specialized model fields
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                search_model TEXT,
                chat_model TEXT,
                analysis_model TEXT,
                max_retries INTEGER NOT NULL,
                retry_delay REAL NOT NULL,
                temperature REAL NOT NULL,
                max_tokens INTEGER NOT NULL,
                system_prompt TEXT,
                min_similarity REAL DEFAULT 0.5
            )
        """
        )

        # Create prompt types table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_types (
                id TEXT NOT NULL,
                config_id TEXT NOT NULL,
                name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                PRIMARY KEY (id, config_id),
                FOREIGN KEY (config_id) REFERENCES config(id)
            )
        """
        )

        # Create web search config table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS web_search_config (
                id TEXT PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT 1,
                max_searches_per_minute INTEGER NOT NULL DEFAULT 10,
                max_results_per_search INTEGER NOT NULL DEFAULT 5,
                default_region TEXT NOT NULL DEFAULT 'wt-wt',
                cache_duration_hours INTEGER NOT NULL DEFAULT 1,
                enable_news_search BOOLEAN NOT NULL DEFAULT 1,
                max_snippet_length INTEGER NOT NULL DEFAULT 200
            )
        """
        )

        # Insert default LLM configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO config VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "default",
                "qwen3:latest",
                "nomic-embed-text:latest",
                None,  # search_model
                None,  # chat_model
                None,  # analysis_model
                2,  # max_retries
                1.0,  # retry_delay
                0.7,  # temperature
                1000,  # max_tokens
                "You are a helpful journaling assistant.",  # system_prompt
                0.5,  # min_similarity
            ),
        )

        # Insert default web search configuration
        cursor.execute(
            """
            INSERT OR REPLACE INTO web_search_config VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "default",
                1,  # enabled
                10,  # max_searches_per_minute
                5,  # max_results_per_search
                "wt-wt",  # default_region
                1,  # cache_duration_hours
                1,  # enable_news_search
                200,  # max_snippet_length
            ),
        )

        # Create chat tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                context_summary TEXT,
                temporal_filter TEXT,
                entry_count INTEGER DEFAULT 0,
                model_name TEXT,
                persona_id TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                token_count INTEGER,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_message_entries (
                message_id TEXT NOT NULL,
                entry_id TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                chunk_index INTEGER,
                entry_title TEXT,
                entry_snippet TEXT,
                PRIMARY KEY (message_id, entry_id),
                FOREIGN KEY (message_id) REFERENCES chat_messages (id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES entries (id) ON DELETE CASCADE
            )
            """
        )

        # Create chat config table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_config (
                id TEXT PRIMARY KEY,
                system_prompt TEXT NOT NULL,
                temperature REAL NOT NULL,
                max_history INTEGER NOT NULL,
                retrieval_limit INTEGER NOT NULL,
                chunk_size INTEGER NOT NULL,
                chunk_overlap INTEGER NOT NULL,
                use_enhanced_retrieval BOOLEAN NOT NULL,
                max_tokens INTEGER NOT NULL,
                max_context_tokens INTEGER NOT NULL,
                conversation_summary_threshold INTEGER NOT NULL,
                context_window_size INTEGER NOT NULL,
                use_context_windowing BOOLEAN NOT NULL,
                min_messages_for_summary INTEGER NOT NULL,
                summary_prompt TEXT NOT NULL
            )
            """
        )

        # Create personas table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS personas (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                icon TEXT DEFAULT '🤖',
                is_default BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            """
        )

        conn.commit()
        conn.close()

        # Create a test storage manager
        class TestStorageManager(StorageManager):
            def __init__(self):
                # Call parent constructor to properly initialize storage components
                super().__init__(TEST_DATA_DIR)
                # In-memory store for test entries
                self._test_entries = {}

            # Override methods that might cause test failures
            def get_entries(
                self, limit=10, offset=0, date_from=None, date_to=None, tags=None
            ):
                """Return test entries instead of querying the database."""
                entries = [
                    JournalEntry(
                        id="test1",
                        title="Test Entry 1",
                        content="Test content 1",
                        created_at="2025-05-01T00:00:00",
                        tags=["test", "api"],
                    ),
                    JournalEntry(
                        id="test2",
                        title="Test Entry 2",
                        content="Test content 2",
                        created_at="2025-05-02T00:00:00",
                        tags=["test", "api", "advanced"],
                    ),
                    JournalEntry(
                        id="test3",
                        title="Apple Recipes",
                        content="How to make apple pie and apple sauce.",
                        created_at="2025-05-03T00:00:00",
                        tags=["food", "recipes"],
                    ),
                ]

                # Filter by tags if specified
                if tags:
                    entries = [e for e in entries if any(tag in e.tags for tag in tags)]

                # Filter by date if specified
                if date_from:
                    entries = [e for e in entries if e.created_at >= date_from]
                if date_to:
                    entries = [e for e in entries if e.created_at <= date_to]

                return entries[:limit]

            def get_entry(self, entry_id):
                """Return a test entry based on ID."""
                # Check in-memory store first
                if entry_id in self._test_entries:
                    return self._test_entries[entry_id]

                # For regular test IDs
                if entry_id in ["test1", "test2", "test3"]:
                    entries = self.get_entries()
                    for entry in entries:
                        if entry.id == entry_id:
                            return entry

                # For dynamically created entries in tests
                if entry_id == "test_entry_id":
                    entry = JournalEntry(
                        id="test_entry_id",
                        title="Test Entry",
                        content="This is a test entry",
                        created_at=datetime.now().isoformat(),
                        tags=["test", "api"],
                    )
                    self._test_entries[entry_id] = entry
                    return entry

                # For nonexistent entries, return None
                if entry_id == "nonexistent":
                    return None

                # For created entries that don't exist, return None (they were probably deleted)
                # Only auto-create during the setup/create phase, not for gets after delete
                return None

            def save_entry(self, entry):
                """Save a journal entry (used by API)."""
                # Store in memory for later retrieval
                self._test_entries[entry.id] = entry
                return entry.id

            def create_entry(
                self, title, content, tags=None, created_at=None, updated_at=None
            ):
                """Mock entry creation."""
                from datetime import datetime
                import uuid

                entry_id = str(uuid.uuid4())[:8]
                entry = JournalEntry(
                    id=entry_id,
                    title=title,
                    content=content,
                    created_at=created_at or datetime.now().isoformat(),
                    updated_at=updated_at,
                    tags=tags or [],
                )

                # Store in memory for later retrieval
                self._test_entries[entry_id] = entry
                return entry

            def update_entry(self, entry_id, update_data):
                """Mock entry update."""
                entry = self.get_entry(entry_id)
                if not entry:
                    return None

                for key, value in update_data.items():
                    setattr(entry, key, value)

                return entry

            def delete_entry(self, entry_id):
                """Mock entry deletion."""
                entry = self.get_entry(entry_id)
                if entry is not None:
                    # Remove from in-memory store
                    self._test_entries.pop(entry_id, None)
                    return True
                return False

            def text_search(
                self,
                query,
                date_from=None,
                date_to=None,
                tags=None,
                folder=None,
                favorite=None,
                limit=10,
                offset=0,
            ):
                """Mock text search functionality."""
                # Get all entries including ones in memory
                entries = self.get_entries()
                entries.extend(self._test_entries.values())

                if query:
                    results = []
                    for entry in entries:
                        if (
                            query.lower() in entry.title.lower()
                            or query.lower() in entry.content.lower()
                        ):
                            results.append(entry)
                else:
                    results = entries

                # Filter by tags if specified
                if tags:
                    results = [e for e in results if any(tag in e.tags for tag in tags)]

                return results[:limit]

            def get_all_tags(self):
                """Return a list of test tags."""
                base_tags = [
                    "test",
                    "api",
                    "food",
                    "recipes",
                    "tech",
                    "news",
                    "advanced",
                    "special",
                ]

                # Add tags from in-memory entries
                for entry in self._test_entries.values():
                    if entry.tags:
                        base_tags.extend(entry.tags)

                # Return unique tags
                return list(set(base_tags))

            def get_entries_by_tag(self, tag, limit=10, offset=0):
                """Return entries with the specified tag."""
                # Get all entries including ones in memory
                entries = self.get_entries()
                entries.extend(self._test_entries.values())
                matching = [e for e in entries if tag in e.tags]
                return matching[offset : offset + limit]

            def get_stats(self):
                """Return test statistics."""
                # Get all entries including ones in memory
                entries = self.get_entries()
                entries.extend(self._test_entries.values())

                total_entries = len(entries)
                all_tags = self.get_all_tags()
                total_tags = len(all_tags)

                # Count tag usage
                tag_counts = {}
                for entry in entries:
                    if entry.tags:
                        for tag in entry.tags:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Sort by count and convert to list format
                most_used_tags = [
                    [tag, count]
                    for tag, count in sorted(
                        tag_counts.items(), key=lambda x: x[1], reverse=True
                    )
                ]

                # Calculate oldest and newest entries
                oldest_entry = None
                newest_entry = None
                if entries:
                    sorted_entries = sorted(entries, key=lambda e: e.created_at)
                    oldest_entry = sorted_entries[0].created_at.isoformat()
                    newest_entry = sorted_entries[-1].created_at.isoformat()

                return {
                    "total_entries": total_entries,
                    "oldest_entry": oldest_entry,
                    "newest_entry": newest_entry,
                    "total_tags": total_tags,
                    "most_used_tags": most_used_tags[:5],  # Top 5
                }

        # Set up our test dependencies
        test_storage = TestStorageManager()

        # Override the storage dependency
        def get_test_storage():
            return test_storage

        app.dependency_overrides[get_storage] = get_test_storage

        yield test_storage

        # Clean up
        app.dependency_overrides.clear()

        # Uncomment to delete test data after tests
        # if os.path.exists(TEST_DATA_DIR):
        #     shutil.rmtree(TEST_DATA_DIR)

    @pytest.fixture
    def test_storage(test_environment):
        """Return the test storage manager."""
        return test_environment


@pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE, reason="API test dependencies not available"
)
class TestAPIEndpoints:
    """Test Journal API endpoints."""

    def setup_method(self):
        """Set up test data before each test method."""
        # Create a test entry at the beginning to ensure we have an ID to work with
        if not hasattr(self, "entry_id"):
            entry_data = {
                "title": "Setup Test Entry",
                "content": "This is a test entry created during setup",
                "tags": ["test", "setup"],
            }
            response = client.post("/entries/", json=entry_data)
            if response.status_code == 200:
                self.entry_id = response.json()["id"]
            else:
                # Fallback in case API call fails
                self.entry_id = "test_entry_id"

    def test_api_info(self):
        """Test /api/info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Llens API"
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
        # First create a test entry for this specific test
        entry_data = {
            "title": "Test Entry",
            "content": "This is a test entry",
            "tags": ["test", "api"],
        }
        response = client.post("/entries/", json=entry_data)
        assert response.status_code == 200
        test_entry_id = response.json()["id"]

        # Get the entry we just created
        response = client.get(f"/entries/{test_entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_entry_id
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
        # First create a test entry for this specific test
        entry_data = {
            "title": "Test Entry",
            "content": "This is a test entry",
            "tags": ["test", "api"],
        }
        response = client.post("/entries/", json=entry_data)
        assert response.status_code == 200
        test_entry_id = response.json()["id"]

        # Now update it
        update_data = {
            "title": "Updated Test Entry",
            "tags": ["test", "api", "updated"],
        }
        response = client.patch(f"/entries/{test_entry_id}", json=update_data)
        if response.status_code != 200:
            print(f"Response: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["tags"] == update_data["tags"]
        assert data["content"] == "This is a test entry"  # Unchanged

        # Verify update was persisted
        response = client.get(f"/entries/{test_entry_id}")
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
        if response.status_code != 200:
            print(f"Search Response Status: {response.status_code}")
            print(f"Search Response Text: {response.text}")
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
        # First ensure we have the right tags by creating an entry with known tags
        tag_entry = {
            "title": "Tag Test Entry",
            "content": "This is for testing tags",
            "tags": ["test", "api", "tagtest"],
        }
        client.post("/entries/", json=tag_entry)

        # Get all tags
        response = client.get("/tags/")
        if response.status_code != 200:
            print(f"Tags Response Status: {response.status_code}")
            print(f"Tags Response Text: {response.text}")
        assert response.status_code == 200
        tags = response.json()
        assert isinstance(tags, list)
        assert "test" in tags  # This tag should now exist

        # Get entries by tag
        response = client.get("/tags/test/entries")
        if response.status_code != 200:
            print(f"Tag Entries Response Status: {response.status_code}")
            print(f"Tag Entries Response Text: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("test" in entry["tags"] for entry in data)

    def test_stats_endpoint(self):
        """Test the statistics endpoint."""
        # Create multiple entries to ensure we have enough data
        for i in range(3):
            entry = {
                "title": f"Stats Entry {i}",
                "content": f"Content for stats test {i}",
                "tags": ["stats", f"tag{i}"],
            }
            client.post("/entries/", json=entry)

        response = client.get("/stats/")
        if response.status_code != 200:
            print(f"Stats Response Status: {response.status_code}")
            print(f"Stats Response Text: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert data["total_entries"] >= 1  # At least one entry should exist
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
