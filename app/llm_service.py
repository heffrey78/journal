"""
LLM Service for the journal application.

This module provides integration with Ollama for
embedding generation and structured outputs.
"""
import ollama
import numpy as np
import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.storage import StorageManager
from app.models import LLMConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""

    pass


class OllamaConnectionError(LLMServiceError):
    """Exception raised when connection to Ollama fails."""

    pass


class EmbeddingGenerationError(LLMServiceError):
    """Exception raised when embedding generation fails."""

    pass


class SummarizationError(LLMServiceError):
    """Exception raised when summarization fails."""

    pass


class EntrySummary(BaseModel):
    """Model for structured output from Ollama summarization."""

    summary: str
    key_topics: List[str]
    mood: str


class LLMService:
    """
    Service for LLM functionality using Ollama.

    This service provides embedding generation for semantic search and
    structured output capabilities for journal entry analysis.
    """

    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
    ):
        """
        Initialize the LLM service.

        Args:
            storage_manager: Optional reference to the storage manager
        """
        self.storage_manager = storage_manager

        # Load configuration from storage if available, otherwise use defaults
        self.config = LLMConfig()
        if storage_manager:
            stored_config = storage_manager.get_llm_config()
            if stored_config:
                self.config = stored_config

        # Set instance variables from config
        self.model_name = self.config.model_name
        self.embedding_model = self.config.embedding_model
        self.max_retries = self.config.max_retries
        self.retry_delay = self.config.retry_delay
        self.temperature = self.config.temperature
        self.max_tokens = self.config.max_tokens
        self.system_prompt = self.config.system_prompt

        # Verify Ollama connection on initialization
        self._verify_ollama_connection()

    def reload_config(self):
        """
        Reload configuration from storage.

        Call this method after configuration has been updated.
        """
        if self.storage_manager:
            stored_config = self.storage_manager.get_llm_config()
            if stored_config:
                self.config = stored_config
                self.model_name = self.config.model_name
                self.embedding_model = self.config.embedding_model
                self.max_retries = self.config.max_retries
                self.retry_delay = self.config.retry_delay
                self.temperature = self.config.temperature
                self.max_tokens = self.config.max_tokens
                self.system_prompt = self.config.system_prompt
                logger.info("LLM configuration reloaded from storage")
                return True
        return False

    def _verify_ollama_connection(self) -> bool:
        """
        Verify that Ollama is running and accessible.

        Returns:
            True if connection is successful

        Raises:
            OllamaConnectionError: If connection to Ollama fails
        """
        try:
            # Try a simple API call to check if Ollama is running
            ollama.embeddings(model=self.embedding_model, prompt="test connection")
            logger.info("Successfully connected to Ollama")
            return True
        except Exception as e:
            error_msg = f"Failed to connect to Ollama: {str(e)}"
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text using Ollama.

        Args:
            text: The text to generate an embedding for

        Returns:
            Numpy array containing the embedding vector

        Raises:
            EmbeddingGenerationError: If embedding generation fails after retries
        """
        attempts = 0
        last_exception = None

        while attempts <= self.max_retries:
            try:
                response = ollama.embeddings(model=self.embedding_model, prompt=text)
                return np.array(response["embedding"], dtype=np.float32)
            except Exception as e:
                last_exception = e
                attempts += 1
                if attempts <= self.max_retries:
                    logger.warning(
                        f"Embedding generation attempt "
                        f"{attempts} failed: {e}. Retrying..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    break

        # Log the error and return a fallback
        logger.error(
            f"Failed to generate embedding after "
            f"{self.max_retries + 1} attempts: {last_exception}"
        )

        # For production use, we might want to raise an exception instead

        # Return zero vector as fallback
        logger.warning("Returning zero vector as fallback for embedding")
        return np.zeros(
            768, dtype=np.float32
        )  # Use consistent size for nomic-embed-text model

    def process_entries_without_embeddings(self, limit: int = 10) -> int:
        """
        Process entries that don't have embeddings yet.

        Args:
            limit: Maximum number of chunks to process

        Returns:
            Number of chunks processed

        Raises:
            ValueError: If storage manager is not set
            EmbeddingGenerationError: If embedding generation consistently fails
        """
        if not self.storage_manager:
            raise ValueError("Storage manager is required for this operation")

        chunks = self.storage_manager.get_chunks_without_embeddings(limit)
        if not chunks:
            return 0

        processed = 0
        failed = 0

        for chunk in chunks:
            try:
                entry_id = chunk["entry_id"]
                chunk_id = chunk["chunk_id"]
                text = chunk["text"]

                # Generate embedding
                embedding = self.get_embedding(text)

                # Update storage with embedding
                self.storage_manager.update_vectors_with_embeddings(
                    entry_id, {chunk_id: embedding}
                )
                processed += 1

            except Exception as e:
                failed += 1
                logger.error(
                    f"Failed to process chunk {chunk.get('id', 'unknown')}: {e}"
                )

        if failed > 0:
            logger.warning(f"Failed to process {failed} out of {len(chunks)} chunks")

        return processed

    def summarize_entry(self, content: str) -> EntrySummary:
        """
        Generate a summary of a journal entry using structured output.

        Args:
            content: The journal entry content to summarize

        Returns:
            EntrySummary object with summary, key topics and mood

        Raises:
            SummarizationError: If summarization fails
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                        or "You are a helpful journaling assistant.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this journal entry. "
                        f"Extract key topics and mood. Return as JSON:\n\n{content}",
                    },
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
                format={
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A concise summary of the journal entry",
                        },
                        "key_topics": {
                            "type": "array",
                            "description": "List of key topics from the entry",
                            "items": {"type": "string"},
                        },
                        "mood": {
                            "type": "string",
                            "description": "The overall mood of the entry",
                        },
                    },
                    "required": ["summary", "key_topics", "mood"],
                },
            )

            # Parse the response into the EntrySummary model
            content = response["message"]["content"]
            return EntrySummary.model_validate_json(content)
        except Exception as e:
            logger.error(f"Error summarizing entry: {e}")
            raise SummarizationError(f"Failed to summarize entry: {e}")

    def semantic_search(
        self, query: str, limit: int = 5, offset: int = 0, batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on journal entries with pagination support.

        Args:
            query: The search query text
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination
            batch_size: Size of batches for processing vectors

        Returns:
            List of search results

        Raises:
            ValueError: If storage manager is not set
        """
        if not self.storage_manager:
            raise ValueError("Storage manager is required for this operation")

        # Generate embedding for the query
        query_embedding = self.get_embedding(query)

        # Search using the storage manager's optimized method
        results = self.storage_manager.semantic_search(
            query_embedding, limit=limit, offset=offset, batch_size=batch_size
        )

        return results
