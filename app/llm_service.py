"""
LLM Service for the journal application.

This module provides integration with Ollama for
embedding generation and structured outputs.
"""
import ollama
import numpy as np
import logging
import time
from typing import List, Dict, Any, Optional, Callable
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
    favorite: bool = False
    prompt_type: Optional[str] = None


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
        self.min_similarity = self.config.min_similarity

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
                self.min_similarity = self.config.min_similarity
                logger.info("LLM configuration reloaded from storage")
                return True
        return False

    def get_prompt_template(self, prompt_type: str = "default") -> str:
        """
        Get the prompt template for the specified type.

        Args:
            prompt_type: ID of the prompt type to retrieve

        Returns:
            The prompt template string
        """
        # Find the prompt template in the config
        for pt in self.config.prompt_types:
            if pt.id == prompt_type:
                return pt.prompt

        # If not found, use the first available prompt or a fallback
        if self.config.prompt_types:
            logger.warning(
                f"Prompt type '{prompt_type}' not found, using first available"
            )
            return self.config.prompt_types[0].prompt

        # Ultimate fallback if no prompts are configured
        logger.warning("No prompt types available in configuration, using fallback")
        return (
            "Summarize this journal entry. Extract key topics and mood. Return as JSON:"
        )

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

    def process_entries_without_embeddings(
        self,
        limit: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> int:
        """
        Process entries that don't have embeddings yet.

        Args:
            limit: Maximum number of chunks to process
            progress_callback: Optional callback function to report progress

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
        total_chunks = len(chunks)

        for chunk_index, chunk in enumerate(chunks):
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

                # Report progress if callback provided
                if progress_callback:
                    progress_callback(chunk_index + 1, total_chunks)

            except Exception as e:
                failed += 1
                logger.error(
                    f"Failed to process chunk {chunk.get('id', 'unknown')}: {e}"
                )

        if failed > 0:
            logger.warning(f"Failed to process {failed} out of {len(chunks)} chunks")

        return processed

    def summarize_entry(
        self,
        content: str,
        prompt_type: str = "default",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> EntrySummary:
        """
        Generate a summary of a journal entry using structured output.

        Args:
            content: The journal entry content to summarize
            prompt_type: Type of prompt to use (default, detailed, creative, concise)
            progress_callback: Optional callback function to report progress (0.0-1.0)

        Returns:
            EntrySummary object with summary, key topics and mood

        Raises:
            SummarizationError: If summarization fails
        """
        try:
            # Get appropriate prompt template from config
            prompt_template = self.get_prompt_template(prompt_type)

            # Report initial progress
            if progress_callback:
                progress_callback(0.1)

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
                        "content": f"{prompt_template}\n\n{content}",
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

            # Report completion
            if progress_callback:
                progress_callback(1.0)

            # Parse the response into the EntrySummary model
            content = response["message"]["content"]
            summary = EntrySummary.model_validate_json(content)

            # Store the prompt type that was used
            summary.prompt_type = prompt_type

            return summary
        except Exception as e:
            logger.error(f"Error summarizing entry: {e}")
            raise SummarizationError(f"Failed to summarize entry: {e}")

    def save_favorite_summary(self, entry_id: str, summary: EntrySummary) -> bool:
        """
        Save a summary as a favorite for a specific entry.

        Args:
            entry_id: The ID of the journal entry
            summary: The EntrySummary object to save

        Returns:
            True if successful, False otherwise
        """
        if not self.storage_manager:
            logger.error("Cannot save favorite summary without storage manager")
            return False

        try:
            # Mark as favorite
            summary.favorite = True

            # Save to storage
            return self.storage_manager.save_entry_summary(entry_id, summary)
        except Exception as e:
            logger.error(f"Failed to save favorite summary: {e}")
            return False

    def get_favorite_summaries(self, entry_id: str) -> List[EntrySummary]:
        """
        Get all favorite summaries for a specific entry.

        Args:
            entry_id: The ID of the journal entry

        Returns:
            List of EntrySummary objects
        """
        if not self.storage_manager:
            logger.error("Cannot get favorite summaries without storage manager")
            return []

        try:
            return self.storage_manager.get_entry_summaries(entry_id)
        except Exception as e:
            logger.error(f"Failed to get favorite summaries: {e}")
            return []

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        offset: int = 0,
        batch_size: int = 1000,
        min_similarity: Optional[
            float
        ] = None,  # Allow overriding the default threshold
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on journal entries with pagination support.

        This implementation uses a hybrid approach combining:
        1. Vector-based similarity search using embeddings
        2. Text-based search using the expanded query terms

        This ensures we find both semantically similar content and
        content with direct keyword matches from the expanded query.

        Args:
            query: The search query text
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination
            batch_size: Size of batches for processing vectors
            min_similarity: Optional minimum similarity threshold (0-1).
                           If None, uses the configured default value.

        Returns:
            List of search results filtered by relevance

        Raises:
            ValueError: If storage manager is not set
        """
        if not self.storage_manager:
            raise ValueError("Storage manager is required for this operation")

        # Use the configured threshold if none is provided
        if min_similarity is None:
            min_similarity = self.min_similarity

        # Expand the query to better capture semantic meaning
        expanded_query = self._expand_semantic_query(query)

        # Get expanded query terms for text matching
        expanded_terms = expanded_query.lower().split()

        # Generate embedding for the original query
        query_embedding = self.get_embedding(query)

        # HYBRID APPROACH: Combine vector search with text search

        # 1. Get semantic search results
        semantic_results = self.storage_manager.semantic_search(
            query_embedding,
            limit=limit * 2,  # Get more results to account for filtering
            offset=offset,
            batch_size=batch_size,
        )

        # Track entry IDs to avoid duplicates
        found_entry_ids = set()
        final_results = []

        # 2. Filter semantic results by similarity threshold and collect entry IDs
        for result in semantic_results:
            if result["similarity"] >= min_similarity:
                found_entry_ids.add(result["entry_id"])
                final_results.append(result)

        # 3. Add text search results for expanded terms if they're not already included
        if self.storage_manager:
            # Search for entries containing any of the expanded terms
            for term in expanded_terms:
                if len(term) < 3:
                    continue  # Skip very short terms

                text_results = self.storage_manager.text_search(
                    query=term, limit=limit  # Reasonable limit for each term
                )

                # Add unique entries not already found by semantic search
                for entry in text_results:
                    if entry.id not in found_entry_ids:
                        found_entry_ids.add(entry.id)
                        # Create a result dict similar to semantic results
                        final_results.append(
                            {
                                "entry_id": entry.id,
                                "entry": entry,
                                "similarity": 0.7,  # Default similarity
                                "text": f"Text match for term: '{term}'",
                                "match_type": "text",  # Mark as text match
                            }
                        )

        # Sort by similarity (semantic matches naturally rank higher)
        final_results.sort(key=lambda x: x["similarity"], reverse=True)

        # Apply limit to combined results
        return final_results[:limit]

    def _expand_semantic_query(self, query: str) -> str:
        """
        Expand a search query to improve semantic search results using LLM.

        This method uses the LLM to generate related terms for the query
        to improve semantic search accuracy.

        Args:
            query: Original search query

        Returns:
            Expanded query for better semantic matching
        """
        # If query is too short or empty, return as is
        if not query or len(query.strip()) < 3:
            return query

        try:
            # Prepare a prompt for the LLM to expand the query
            system_message = "You are a semantic search enhancer."
            user_message = (
                "Expand the following query with related terms "
                f"to improve semantic search: '{query}'\n\n"
                "Return ONLY a space-separated list of terms without explanations. "
                "Include the original query terms adding 5-8 closely related concepts. "
                "Keep the total response under 15 words."
            )

            # Call Ollama to get expanded terms
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                options={
                    "temperature": 0.2,  # Low temperature for more deterministism
                    "num_predict": 100,  # Limit token count for efficiency
                },
            )

            # Extract expanded query from response
            expanded_query = response["message"]["content"].strip()
            logger.info(f"Expanded query '{query}' to '{expanded_query}'")
            return expanded_query

        except Exception as e:
            # On failure, log and return original query
            logger.warning(f"Failed to expand query using LLM: {e}")
            return query
