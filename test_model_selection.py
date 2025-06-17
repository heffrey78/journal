"""
Test suite for specialized model configuration and selection.

This test validates the model selection logic implemented in the LLM service.
"""

import pytest
from unittest.mock import Mock, patch
from app.models import LLMConfig
from app.llm_service import LLMService


class TestModelSelection:
    """Test the model selection logic for different operations."""

    def setup_method(self):
        """Set up test environment."""
        # Create a mock storage manager
        self.mock_storage = Mock()

        # Create test configuration with specialized models
        self.test_config = LLMConfig(
            model_name="qwen3:latest",
            embedding_model="nomic-embed-text:latest",
            search_model="qwen3:7b",
            chat_model="qwen3:14b",
            analysis_model="qwen3:32b",
        )

        # Mock the config retrieval
        self.mock_storage.get_llm_config.return_value = self.test_config

    @patch("app.llm_service.ollama")
    def test_get_model_for_operation_with_specialized_models(self, mock_ollama):
        """Test that correct specialized models are selected for operations."""
        # Mock available models
        mock_ollama.list.return_value = {
            "models": [
                {"name": "qwen3:latest"},
                {"name": "qwen3:7b"},
                {"name": "qwen3:14b"},
                {"name": "qwen3:32b"},
                {"name": "nomic-embed-text:latest"},
            ]
        }

        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # Test search model selection
        search_model = llm_service._get_model_for_operation("search")
        assert search_model == "qwen3:7b"

        # Test chat model selection
        chat_model = llm_service._get_model_for_operation("chat")
        assert chat_model == "qwen3:14b"

        # Test analysis model selection
        analysis_model = llm_service._get_model_for_operation("analysis")
        assert analysis_model == "qwen3:32b"

        # Test embedding model selection
        embedding_model = llm_service._get_model_for_operation("embedding")
        assert embedding_model == "nomic-embed-text:latest"

    @patch("app.llm_service.ollama")
    def test_fallback_to_default_model(self, mock_ollama):
        """Test fallback to default model when specialized models are not configured."""
        # Create config without specialized models
        basic_config = LLMConfig(
            model_name="qwen3:latest", embedding_model="nomic-embed-text:latest"
        )
        self.mock_storage.get_llm_config.return_value = basic_config

        # Mock available models
        mock_ollama.list.return_value = {
            "models": [{"name": "qwen3:latest"}, {"name": "nomic-embed-text:latest"}]
        }

        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # All non-embedding operations should fall back to default model
        assert llm_service._get_model_for_operation("search") == "qwen3:latest"
        assert llm_service._get_model_for_operation("chat") == "qwen3:latest"
        assert llm_service._get_model_for_operation("analysis") == "qwen3:latest"
        assert (
            llm_service._get_model_for_operation("embedding")
            == "nomic-embed-text:latest"
        )

    @patch("app.llm_service.ollama")
    def test_fallback_when_specialized_model_unavailable(self, mock_ollama):
        """Test fallback when specialized model is configured but not available."""
        # Mock available models (missing the specialized models)
        mock_ollama.list.return_value = {
            "models": [{"name": "qwen3:latest"}, {"name": "nomic-embed-text:latest"}]
        }

        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # Should fall back to default model when specialized models are unavailable
        assert llm_service._get_model_for_operation("search") == "qwen3:latest"
        assert llm_service._get_model_for_operation("chat") == "qwen3:latest"
        assert llm_service._get_model_for_operation("analysis") == "qwen3:latest"

    @patch("app.llm_service.ollama")
    def test_invalid_operation_type(self, mock_ollama):
        """Test that invalid operation types raise ValueError."""
        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # Should raise ValueError for invalid operation type
        with pytest.raises(ValueError, match="Unknown operation type"):
            llm_service._get_model_for_operation("invalid_operation")

    @patch("app.llm_service.ollama")
    def test_model_validation_caching(self, mock_ollama):
        """Test that model availability is cached to avoid repeated API calls."""
        # Mock available models
        mock_ollama.list.return_value = {
            "models": [
                {"name": "qwen3:latest"},
                {"name": "qwen3:7b"},
                {"name": "nomic-embed-text:latest"},
            ]
        }

        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # First call should fetch models
        assert llm_service._validate_model_availability("qwen3:7b") is True

        # Second call should use cached models
        assert llm_service._validate_model_availability("qwen3:7b") is True

        # Verify ollama.list was called only once during initialization
        mock_ollama.list.assert_called_once()

    @patch("app.llm_service.ollama")
    def test_config_reload_clears_cache(self, mock_ollama):
        """Test that reloading configuration clears the model cache."""
        # Mock available models
        mock_ollama.list.return_value = {
            "models": [{"name": "qwen3:latest"}, {"name": "nomic-embed-text:latest"}]
        }

        # Mock embedding call for connection verification
        mock_ollama.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        # Create LLM service instance
        llm_service = LLMService(storage_manager=self.mock_storage)

        # Trigger model validation to populate cache
        llm_service._validate_model_availability("qwen3:latest")
        assert hasattr(llm_service, "_cached_models")

        # Reload configuration
        llm_service.reload_config()

        # Cache should be cleared
        assert not hasattr(llm_service, "_cached_models")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
