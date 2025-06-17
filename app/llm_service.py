"""
LLM Service for the journal application.

This module provides integration with Ollama for
embedding generation and structured outputs.
"""

import ollama
import logging
import json
import time
import random
from typing import List, Dict, Any, Optional, Callable, Iterator, Union
from pydantic import BaseModel
from app.storage import StorageManager
from app.models import LLMConfig, BatchAnalysis, JournalEntry, EntrySummary

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


class BatchAnalysisError(LLMServiceError):
    """Exception raised when batch analysis fails."""

    pass


class CUDAError(LLMServiceError):
    """Exception raised when CUDA-related errors occur."""

    pass


class CircuitBreakerOpen(LLMServiceError):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for GPU operations."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def is_available(self) -> bool:
        """Check if the circuit breaker allows operations."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


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
        self.search_model = self.config.search_model
        self.chat_model = self.config.chat_model
        self.analysis_model = self.config.analysis_model
        self.max_retries = self.config.max_retries
        self.retry_delay = self.config.retry_delay
        self.temperature = self.config.temperature
        self.max_tokens = self.config.max_tokens
        self.system_prompt = self.config.system_prompt
        self.min_similarity = self.config.min_similarity

        # Initialize circuit breaker for GPU operations
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

        # Verify Ollama connection on initialization
        self._verify_ollama_connection()

    def _is_cuda_error(self, error_message: str) -> bool:
        """Check if an error message indicates a CUDA-related failure."""
        cuda_indicators = [
            "cuda error",
            "illegal memory access",
            "ggml_backend_cuda",
            "cudastreamsynchro",
            "cuda device",
            "gpu memory",
            "out of memory",
        ]
        error_lower = str(error_message).lower()
        return any(indicator in error_lower for indicator in cuda_indicators)

    def _execute_with_resilience(
        self, operation_func, operation_name: str, *args, **kwargs
    ):
        """
        Execute an Ollama operation with CUDA error resilience.

        Args:
            operation_func: Function to execute
            operation_name: Name of the operation for logging
            *args, **kwargs: Arguments to pass to the operation function

        Returns:
            Result of the operation

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            CUDAError: If CUDA errors persist after retries
            LLMServiceError: For other types of failures
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_available():
            error_msg = (
                f"Circuit breaker is open for {operation_name} - GPU may be unstable"
            )
            logger.error(error_msg)
            raise CircuitBreakerOpen(error_msg)

        last_error = None
        retry_count = 0
        max_retries = self.max_retries or 3

        while retry_count <= max_retries:
            try:
                # Execute the operation
                result = operation_func(*args, **kwargs)

                # Record success and reset circuit breaker
                self.circuit_breaker.record_success()
                logger.debug(f"Successfully executed {operation_name}")
                return result

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Check if this is a CUDA error
                if self._is_cuda_error(error_str):
                    retry_count += 1
                    self.circuit_breaker.record_failure()

                    logger.warning(
                        f"CUDA error in {operation_name} (attempt {retry_count}/{max_retries + 1}): {error_str}"
                    )

                    if retry_count <= max_retries:
                        # Exponential backoff with jitter
                        delay = (self.retry_delay or 1) * (2 ** (retry_count - 1))
                        jitter = random.uniform(0.1, 0.3) * delay
                        total_delay = delay + jitter

                        logger.info(
                            f"Retrying {operation_name} in {total_delay:.2f} seconds..."
                        )
                        time.sleep(total_delay)
                        continue
                    else:
                        # Max retries exceeded for CUDA error
                        logger.error(
                            f"Max retries exceeded for {operation_name} due to CUDA errors"
                        )
                        raise CUDAError(
                            f"CUDA error persists in {operation_name}: {error_str}"
                        )
                else:
                    # Non-CUDA error, don't retry
                    logger.error(f"Non-CUDA error in {operation_name}: {error_str}")
                    raise LLMServiceError(
                        f"Failed to execute {operation_name}: {error_str}"
                    )

        # Should not reach here, but just in case
        raise LLMServiceError(f"Unexpected error in {operation_name}: {last_error}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current LLM configuration.

        Returns:
            Dictionary with LLM configuration settings
        """
        return self.config.dict()

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
                self.search_model = self.config.search_model
                self.chat_model = self.config.chat_model
                self.analysis_model = self.config.analysis_model
                self.max_retries = self.config.max_retries
                self.retry_delay = self.config.retry_delay
                self.temperature = self.config.temperature
                self.max_tokens = self.config.max_tokens
                self.system_prompt = self.config.system_prompt
                self.min_similarity = self.config.min_similarity

                # Clear cached models to force re-validation with new config
                if hasattr(self, "_cached_models"):
                    delattr(self, "_cached_models")

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

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text using Ollama.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as a list of floats

        Raises:
            LLMServiceError: If generating the embedding fails
        """

        def _embedding_operation():
            response = ollama.embeddings(model=self.embedding_model, prompt=text)
            if "embedding" in response:
                return response["embedding"]
            else:
                raise LLMServiceError("Invalid response from Ollama embeddings API")

        try:
            return self._execute_with_resilience(
                _embedding_operation, "embedding generation"
            )
        except (CUDAError, CircuitBreakerOpen) as e:
            logger.error(f"Embedding generation failed due to GPU issues: {e}")
            raise EmbeddingGenerationError(f"GPU-related embedding failure: {e}")
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {e}")

    def _get_model_for_operation(self, operation_type: str) -> str:
        """
        Get the appropriate model for a specific operation type with fallback strategy.

        Args:
            operation_type: Type of operation ('search', 'chat', 'analysis')

        Returns:
            Model name to use for the operation

        Raises:
            ValueError: If operation_type is not recognized
        """
        # Define operation-specific model preferences with fallback chain
        model_preferences = {
            "search": [self.search_model, self.model_name],
            "chat": [self.chat_model, self.model_name],
            "analysis": [self.analysis_model, self.model_name],
            "embedding": [self.embedding_model],  # Embeddings use dedicated model
        }

        if operation_type not in model_preferences:
            raise ValueError(f"Unknown operation type: {operation_type}")

        # Try each model in preference order, skip None values
        for model in model_preferences[operation_type]:
            if model:
                if self._validate_model_availability(model):
                    return model
                else:
                    logger.warning(
                        f"Model {model} not available for {operation_type}, trying fallback"
                    )

        # If no valid model found, raise exception
        raise ValueError(
            f"No valid model available for operation type: {operation_type}"
        )

    def _validate_model_availability(self, model_name: str) -> bool:
        """
        Validate that a model is available in Ollama.

        Args:
            model_name: Name of the model to validate

        Returns:
            True if model is available, False otherwise
        """
        try:
            # Cache available models to avoid repeated API calls
            if not hasattr(self, "_cached_models"):
                self._cached_models = self.get_available_models()

            return model_name in self._cached_models
        except Exception as e:
            logger.error(f"Failed to validate model availability for {model_name}: {e}")
            return False  # Assume unavailable on error

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

            def _summarization_operation():
                # Get the appropriate model for analysis operations
                model_to_use = self._get_model_for_operation("analysis")

                return ollama.chat(
                    model=model_to_use,
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

            response = self._execute_with_resilience(
                _summarization_operation, "entry summarization"
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
        except (CUDAError, CircuitBreakerOpen) as e:
            logger.error(f"Entry summarization failed due to GPU issues: {e}")
            raise SummarizationError(f"GPU-related summarization failure: {e}")
        except Exception as e:
            logger.error(f"Error summarizing entry: {e}")
            raise SummarizationError(f"Failed to summarize entry: {e}")

    def analyze_entries_batch(
        self,
        entries: List[JournalEntry],
        title: str = "",
        prompt_type: str = "weekly",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> BatchAnalysis:
        """
        Generate an analysis for a batch of journal entries.

        This method processes multiple entries together to identify patterns,
        common themes, and insights across the entries.

        Args:
            entries: List of journal entries to analyze
            title: Title for the batch analysis
                   (if not provided, one will be generated)
            prompt_type: Type of batch analysis to perform
                        (weekly, monthly, topic, etc.)
            progress_callback: Optional function to report progress (0.0-1.0)

        Returns:
            BatchAnalysis object with the analysis results

        Raises:
            BatchAnalysisError: If batch analysis fails
            ValueError: If entries list is empty
        """
        if not entries:
            raise ValueError("Cannot analyze an empty list of entries")

        try:
            # Report initial progress
            if progress_callback:
                progress_callback(0.1)

            # Generate a default title if none provided
            if not title:
                # Get date range
                dates = sorted([entry.created_at for entry in entries])
                if len(dates) > 1:
                    date_range = f"{dates[0].strftime('%Y-%m-%d')} to "
                    f"{dates[-1].strftime('%Y-%m-%d')}"
                    title = f"{prompt_type.capitalize()} Analysis: {date_range}"
                else:
                    date_range = dates[0].strftime("%Y-%m-%d")
                    title = f"Analysis for {date_range}"
            else:
                # Extract date range from entries
                dates = sorted([entry.created_at for entry in entries])
                if len(dates) > 1:
                    date_range = f"{dates[0].strftime('%Y-%m-%d')} to "
                    f"{dates[-1].strftime('%Y-%m-%d')}"
                else:
                    date_range = dates[0].strftime("%Y-%m-%d")

            # Collect entry IDs for the batch analysis
            entry_ids = [entry.id for entry in entries]

            # Check if we have too many entries for a single batch
            # If so, we'll need to implement a chunking strategy
            if len(entries) > 10:
                logger.info(
                    f"Large batch of {len(entries)} entries - using chunking strategy"
                )
                return self._analyze_large_batch(
                    entries,
                    title,
                    prompt_type,
                    date_range,
                    entry_ids,
                    progress_callback,
                )

            # Report progress after preprocessing
            if progress_callback:
                progress_callback(0.2)

            # Prepare the entries for analysis
            combined_content = ""
            for i, entry in enumerate(entries):
                combined_content += (
                    f"Entry {i + 1} - {entry.created_at.strftime('%Y-%m-%d')}:\n"
                )
                combined_content += f"Title: {entry.title}\n"
                combined_content += f"Content: {entry.content}\n\n"

            # Get the prompt template based on analysis type
            prompt_template = self._get_batch_prompt_template(prompt_type)

            # Report progress before LLM call
            if progress_callback:
                progress_callback(0.4)

            # Make the LLM call
            # Get the appropriate model for analysis operations
            model_to_use = self._get_model_for_operation("analysis")

            response = ollama.chat(
                model=model_to_use,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                        or "You are a helpful journaling assistant that analyzes multiple journal entries.",  # noqa: E501
                    },
                    {
                        "role": "user",
                        "content": f"{prompt_template}\n\n{combined_content}",
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
                            "description": "A comprehensive summary analyzing all the journal entries together",  # noqa: E501
                        },
                        "key_themes": {
                            "type": "array",
                            "description": "List of key themes identified across all entries",  # noqa: E501
                            "items": {"type": "string"},
                        },
                        "mood_trends": {
                            "type": "object",
                            "description": "Dictionary mapping mood categories to their frequency across entries",  # noqa: E501
                            "additionalProperties": {"type": "integer"},
                        },
                        "notable_insights": {
                            "type": "array",
                            "description": "List of notable insights or patterns found in the entries",  # noqa: E501
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "summary",
                        "key_themes",
                        "mood_trends",
                        "notable_insights",
                    ],
                },
            )

            # Report progress after LLM call
            if progress_callback:
                progress_callback(0.8)

            # Parse the response
            content = response["message"]["content"]
            result = json.loads(content)

            # Create the BatchAnalysis object
            batch_analysis = BatchAnalysis(
                title=title,
                entry_ids=entry_ids,
                date_range=date_range,
                summary=result["summary"],
                key_themes=result["key_themes"],
                mood_trends=result["mood_trends"],
                notable_insights=result["notable_insights"],
                prompt_type=prompt_type,
            )

            # Report completion
            if progress_callback:
                progress_callback(1.0)

            return batch_analysis

        except Exception as e:
            logger.error(f"Error analyzing entries batch: {e}")
            raise BatchAnalysisError(f"Failed to analyze entries batch: {e}")

    def _analyze_large_batch(
        self,
        entries: List[JournalEntry],
        title: str,
        prompt_type: str,
        date_range: str,
        entry_ids: List[str],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> BatchAnalysis:
        """
        Handle large batch analysis using a hierarchical approach.

        This method:
        1. Splits entries into smaller chunks
        2. Summarizes each chunk
        3. Combines the summaries for final analysis

        Args:
            entries: All entries to analyze
            title: Title for the batch analysis
            prompt_type: Type of analysis to perform
            date_range: Date range string for the entries
            entry_ids: List of entry IDs to include in the result
            progress_callback: Optional progress reporting function

        Returns:
            BatchAnalysis object with the combined analysis
        """
        # Split entries into batches of 5-10
        batch_size = 5
        # fmt: off
        batches = [
            entries[i : i + batch_size]  # noqa: E203
            for i in range(0, len(entries), batch_size)
        ]
        # fmt: on

        # Track progress per batch
        batch_progress_total = 0.6  # 60% of total progress for batch processing
        batch_progress_per_item = batch_progress_total / len(batches)

        # Process each batch to get summaries
        batch_summaries = []

        for i, batch in enumerate(batches):
            # Calculate progress for this batch
            batch_start_progress = 0.2 + (i * batch_progress_per_item)

            # Define a progress callback for this batch
            def batch_progress_callback(progress_fraction):
                if progress_callback:
                    # Scale the progress to the overall batch progress
                    overall_progress = batch_start_progress + (
                        progress_fraction * batch_progress_per_item
                    )
                    progress_callback(overall_progress)

            # Generate a quick summary for this batch
            try:
                batch_content = ""
                for j, entry in enumerate(batch):
                    batch_content += (
                        f"Entry {j + 1} - {entry.created_at.strftime('%Y-%m-%d')}:\n"
                    )
                    batch_content += f"Title: {entry.title}\n"
                    batch_content += f"Content: {entry.content}\n\n"

                # Use a simplified prompt for the batch summary
                prompt = (
                    "Create a brief summary of these journal entries, "
                    "extract key themes, moods, and notable points. "
                    "Keep it concise as this will be used for further analysis."
                )

                response = ollama.chat(
                    model=self._get_model_for_operation("analysis"),
                    messages=[
                        {
                            "role": "system",
                            "content": "You create concise summaries of journal entries.",  # noqa: E501
                        },
                        {"role": "user", "content": f"{prompt}\n\n{batch_content}"},
                    ],
                    options={"temperature": 0.3},
                )

                batch_summaries.append(response["message"]["content"])

                # Report progress
                batch_progress_callback(1.0)

            except Exception as e:
                logger.warning(f"Error processing batch {i + 1}: {e}")
                # Add a placeholder if batch processing fails
                batch_summaries.append(f"[Batch {i + 1}: Processing error - {str(e)}]")
                batch_progress_callback(1.0)

        # Now combine all batch summaries for final analysis
        if progress_callback:
            progress_callback(0.8)  # 80% complete after processing all batches

        combined_summaries = "\n\n".join(
            [
                f"Batch {i + 1} Summary:\n{summary}"
                for i, summary in enumerate(batch_summaries)
            ]
        )

        # Get the prompt template based on analysis type
        prompt_template = self._get_batch_prompt_template(prompt_type)

        # Add context about the hierarchical analysis
        hierarchical_prompt = (
            f"{prompt_template}\n\n"
            f"The following text contains summaries of {len(entries)} journal entries "
            f"that were processed in batches. Please analyze these summaries together "
            f"to provide a comprehensive analysis of all entries in the date range."
        )

        # Make the final LLM call
        try:
            response = ollama.chat(
                model=self._get_model_for_operation("analysis"),
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                        or "You are a helpful journaling assistant that analyzes multiple journal entries.",  # noqa: E501
                    },
                    {
                        "role": "user",
                        "content": f"{hierarchical_prompt}\n\n{combined_summaries}",
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
                            "description": "A comprehensive summary analyzing all the journal entries together",  # noqa: E501
                        },
                        "key_themes": {
                            "type": "array",
                            "description": "List of key themes identified across all entries",  # noqa: E501
                            "items": {"type": "string"},
                        },
                        "mood_trends": {
                            "type": "object",
                            "description": "Dictionary mapping mood categories to their frequency across entries",  # noqa: E501
                            "additionalProperties": {"type": "integer"},
                        },
                        "notable_insights": {
                            "type": "array",
                            "description": "List of notable insights or patterns found in the entries",  # noqa: E501
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "summary",
                        "key_themes",
                        "mood_trends",
                        "notable_insights",
                    ],
                },
            )

            # Parse the response
            content = response["message"]["content"]
            result = json.loads(content)

            # Create the BatchAnalysis object
            batch_analysis = BatchAnalysis(
                title=title,
                entry_ids=entry_ids,
                date_range=date_range,
                summary=result["summary"],
                key_themes=result["key_themes"],
                mood_trends=result["mood_trends"],
                notable_insights=result["notable_insights"],
                prompt_type=prompt_type,
            )

            # Report completion
            if progress_callback:
                progress_callback(1.0)

            return batch_analysis

        except Exception as e:
            logger.error(f"Error in hierarchical batch analysis: {e}")
            raise BatchAnalysisError(
                f"Failed to complete hierarchical batch analysis: {e}"
            )

    def _get_batch_prompt_template(self, prompt_type: str) -> str:
        """
        Get the appropriate prompt template for batch analysis.

        Args:
            prompt_type: Type of batch analysis (weekly, monthly, topic, etc.)

        Returns:
            Prompt template string
        """
        # Check if we have a specific batch prompt in the config
        batch_prompt_id = f"batch_{prompt_type}"
        for pt in self.config.prompt_types:
            if pt.id == batch_prompt_id:
                return pt.prompt

        # If not found, use default templates based on type
        if prompt_type == "weekly":
            return (
                "Analyze the following journal entries from the past week. "
                "Identify recurring themes, patterns in mood, and notable insights. "
                "Create a comprehensive weekly reflection that summarizes key events, "
                "thoughts, and emotions from the week. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )
        elif prompt_type == "monthly":
            return (
                "Analyze the following journal entries from the past month. "
                "Identify long-term themes, changes in perspective, and significant developments. "  # noqa: E501
                "Create a comprehensive monthly review that captures overall progress, "
                "challenges, and growth from the month. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )
        elif prompt_type == "topic":
            return (
                "Analyze the following journal entries related to a specific topic. "
                "Identify insights, patterns, and developments related to this topic. "
                "Create a comprehensive topic analysis that explores how the topic "
                "has evolved across these entries. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )
        elif prompt_type == "quarterly":
            return (
                "Analyze the following journal entries from the past quarter. "
                "Identify major themes, significant changes, and overall progress across this time period. "  # noqa: E501
                "Create a comprehensive quarterly review that captures growth, challenges overcome, "  # noqa: E501
                "and patterns in your personal and professional life. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )
        elif prompt_type == "project":
            return (
                "Analyze the following journal entries related to a specific project. "
                "Track the evolution of the project, challenges encountered, solutions developed, "  # noqa: E501
                "and insights gained throughout the project timeline. "
                "Create a comprehensive project retrospective that captures lessons learned "  # noqa: E501
                "and overall progress. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )
        else:
            # Default prompt for any other type
            return (
                "Analyze the following journal entries. "
                "Identify common themes, patterns, and insights across all entries. "
                "Create a comprehensive analysis that summarizes key points. "
                "Return the analysis in JSON format with the following fields: "
                "summary, key_themes, mood_trends (as an object mapping moods to frequencies), "  # noqa: E501
                "and notable_insights."
            )

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
        date_filter: Optional[Dict[str, Any]] = None,
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
            date_filter: Optional date filter with date_from and date_to fields

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
        try:
            semantic_results = self.storage_manager.semantic_search(
                query_embedding,
                limit=limit * 2,  # Get more results to account for filtering
                offset=offset,
                batch_size=batch_size,
                date_filter=date_filter,
            )
        except TypeError:
            logger.info("Date filter not supported, falling back to basic search")
            semantic_results = self.storage_manager.semantic_search(
                query_embedding,
                limit=limit * 2,
                offset=offset,
                batch_size=batch_size,
            )

            # Apply date filter manually if needed
            if date_filter:
                filtered_results = []
                date_from = date_filter.get("date_from")
                date_to = date_filter.get("date_to")

                for result in semantic_results:
                    if "entry" in result:
                        entry = result["entry"]
                        # Skip if the entry doesn't have a created_at date
                        if not hasattr(entry, "created_at"):
                            continue

                        # Apply date filter
                        entry_date = entry.created_at
                        passes_filter = True

                        if date_from and entry_date < date_from:
                            passes_filter = False

                        if date_to and entry_date > date_to:
                            passes_filter = False

                        if passes_filter:
                            filtered_results.append(result)

                semantic_results = filtered_results

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

                # Add date filter to text search if available
                date_args = {}
                if date_filter:
                    date_args["date_from"] = date_filter.get("date_from")
                    date_args["date_to"] = date_filter.get("date_to")

                text_results = self.storage_manager.text_search(
                    query=term,
                    limit=limit,  # Reasonable limit for each term
                    **date_args,  # Include date filter in text search
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
                model=self._get_model_for_operation("search"),
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        model: Optional[str] = None,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Generate a chat completion response using Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Optional temperature parameter (0-1) to control randomness
            max_tokens: Optional maximum tokens to generate
            stream: Whether to stream the response token by token

        Returns:
            If stream=False: Dictionary containing the response
            If stream=True: Iterator yielding response chunks

        Raises:
            LLMServiceError: If the chat completion fails
        """
        try:
            # Use provided parameters or fall back to class defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            # Call Ollama for chat completion - use specified model or get appropriate chat model
            model_to_use = model or self._get_model_for_operation("chat")

            if stream:
                return self._stream_chat_completion(
                    messages, temp, tokens, model_to_use
                )
            else:

                def _chat_operation():
                    return ollama.chat(
                        model=model_to_use,
                        messages=messages,
                        options={"temperature": temp, "num_predict": tokens},
                    )

                return self._execute_with_resilience(_chat_operation, "chat completion")
        except (CUDAError, CircuitBreakerOpen) as e:
            logger.error(f"Chat completion failed due to GPU issues: {e}")
            raise LLMServiceError(f"GPU-related chat failure: {e}")
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise LLMServiceError(f"Failed to generate chat completion: {e}")

    def _stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream a chat completion response from Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Temperature parameter (0-1) to control randomness
            max_tokens: Maximum tokens to generate

        Yields:
            Text content chunks as they are generated

        Raises:
            LLMServiceError: If the streaming chat completion fails
        """
        import requests
        import json

        try:
            # Prepare the request payload - use specified model or get appropriate chat model
            model_to_use = model or self._get_model_for_operation("chat")

            data = {
                "model": model_to_use,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }

            # Make the request directly to the Ollama API
            url = "http://localhost:11434/api/chat"
            response = requests.post(url, json=data, stream=True)

            if not response.ok:
                raise LLMServiceError(
                    f"Ollama API error: {response.status_code} {response.reason}"
                )

            # Process each line in the streaming response
            for line in response.iter_lines():
                if not line:
                    continue

                # Parse the JSON chunk
                try:
                    chunk = json.loads(line.decode("utf-8"))

                    # Skip the final completion chunk with done=True
                    if chunk.get("done") is True:
                        continue

                    # Extract just the message content
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        if content:  # Skip empty content
                            yield content
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Ollama response: {e}")
                    continue

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}")
            raise LLMServiceError(f"Failed to stream chat completion: {e}")

    def get_available_models(self):
        """
        Get a list of available models from Ollama.

        Returns:
            List of model names that can be used for text generation

        Raises:
            OllamaConnectionError: If connection to Ollama fails
        """
        try:
            # Try to get the list of models from Ollama
            response = ollama.list()

            # Log successful connection for debugging
            logger.debug(f"ollama.list() returned: {type(response)}")

            # Extract just the model names from the response
            # Handle both old dict format and new typed object format
            models = []

            # Check if response has models attribute (new format)
            if hasattr(response, "models"):
                model_list = response.models
            elif isinstance(response, dict) and "models" in response:
                # Fallback for dict format
                model_list = response["models"]
            else:
                logger.error(
                    f"Unexpected response format from ollama.list(): {type(response)}, {response}"
                )
                raise ValueError(f"Unexpected response format: {type(response)}")

            for model in model_list:
                if hasattr(model, "model"):
                    # New typed object format
                    models.append(model.model)
                elif isinstance(model, dict) and "name" in model:
                    # Old dict format (for backward compatibility)
                    models.append(model["name"])
                elif isinstance(model, dict) and "model" in model:
                    # Alternative dict format
                    models.append(model["model"])

            # Sort the model names for consistent presentation
            models.sort()

            return models
        except Exception as e:
            logger.error(f"Failed to retrieve available models: {e}")
            raise OllamaConnectionError(f"Failed to get available models: {e}")

    def generate_session_title(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a title for a chat session based on the conversation content.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            Generated title string (2-6 words)

        Raises:
            LLMServiceError: If title generation fails
        """
        try:
            # Only use the first few messages to avoid token limit issues
            relevant_messages = messages[:6]

            # Create a condensed conversation summary for title generation
            conversation_text = ""
            for msg in relevant_messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role in ["user", "assistant"] and content:
                    conversation_text += f"{role}: {content[:200]}...\n"

            # Prepare the title generation prompt
            system_message = "You are a chat session title generator. Generate concise, descriptive titles."
            user_message = (
                "Based on this conversation, generate a short title (2-6 words) that captures "
                "the main topic or purpose. Return ONLY the title, no explanations.\n\n"
                f"Conversation:\n{conversation_text}"
            )

            response = ollama.chat(
                model=self._get_model_for_operation("chat"),
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                options={
                    "temperature": 0.3,  # Low temperature for consistent titles
                    "num_predict": 20,  # Short response for just the title
                },
            )

            title = response["message"]["content"].strip()

            # Clean up the title - remove quotes and extra formatting
            title = title.strip("\"'")

            # Fallback if title is too long or empty
            if not title or len(title.split()) > 8:
                # Extract topic from first user message as fallback
                first_user_msg = next(
                    (
                        msg["content"]
                        for msg in relevant_messages
                        if msg.get("role") == "user"
                    ),
                    "Chat Session",
                )
                words = first_user_msg.split()[:4]
                title = " ".join(words) if words else "Chat Session"

            logger.info(f"Generated session title: '{title}'")
            return title

        except Exception as e:
            logger.error(f"Failed to generate session title: {e}")
            # Return a fallback title instead of raising an exception
            return "Chat Session"

    def generate_response_with_model(self, messages, model_name=None):
        """
        Generate a response using a specific model.

        Args:
            messages: List of message objects with 'role' and 'content'
            model_name: Name of the model to use (defaults to configured model_name)

        Returns:
            Text of the generated response

        Raises:
            OllamaConnectionError: If connection to Ollama fails
        """
        try:
            # Use the provided model_name or fall back to chat model
            model = model_name or self._get_model_for_operation("chat")

            response = ollama.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            )

            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Failed to generate response with model {model_name}: {e}")
            raise OllamaConnectionError(f"Failed to generate response: {e}")

    def analyze_message_for_tools(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a message to determine what tools should be called.

        This method uses the LLM to intelligently decide which tools are relevant
        for the given message and context.

        Args:
            message: User message to analyze
            context: Optional context (conversation history, session info, etc.)

        Returns:
            Dictionary with tool recommendations and confidence scores
        """
        try:
            # Create a prompt for tool selection
            system_prompt = """You are an intelligent tool selector for a journaling application. Your job is to analyze user messages and determine which tools should be called to provide the best response.

Available tools:
- journal_search: Search through journal entries for relevant information. Use when user asks about past entries, memories, or specific events they recorded.
- web_search: Search the web for current information, facts, and external knowledge. Use when user asks about general knowledge, current events, definitions, or anything that requires external information beyond their personal journal.

Analyze the user's message and determine:
1. Whether any tools should be called (true/false)
2. Which tools are relevant and why
3. Confidence score (0.0 to 1.0) for each tool recommendation

Important guidelines:
- Use journal_search for personal/journal-related queries
- Use web_search for factual questions, current events, definitions, or external information
- Some queries may require both tools
- If unsure whether information is in the journal or requires web search, recommend both with appropriate confidence scores

Respond with JSON only."""

            # Include conversation context if available
            context_str = ""
            if context:
                if context.get("recent_messages"):
                    context_str += (
                        f"Recent conversation: {context['recent_messages'][-3:]} "
                    )
                if context.get("session_summary"):
                    context_str += f"Session context: {context['session_summary']} "

            user_prompt = f"""User message: "{message}"
{context_str}

Analyze this message and respond with JSON in this format:
{{
    "should_use_tools": boolean,
    "recommended_tools": [
        {{
            "tool_name": "tool_name",
            "confidence": 0.0-1.0,
            "reason": "why this tool is relevant",
            "suggested_query": "query to use with the tool"
        }}
    ],
    "analysis": "brief explanation of your decision"
}}"""

            response = ollama.chat(
                model=self._get_model_for_operation("chat"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "num_predict": 500,
                },
                format={
                    "type": "object",
                    "properties": {
                        "should_use_tools": {"type": "boolean"},
                        "recommended_tools": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool_name": {"type": "string"},
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "reason": {"type": "string"},
                                    "suggested_query": {"type": "string"},
                                },
                                "required": [
                                    "tool_name",
                                    "confidence",
                                    "reason",
                                    "suggested_query",
                                ],
                            },
                        },
                        "analysis": {"type": "string"},
                    },
                    "required": ["should_use_tools", "recommended_tools", "analysis"],
                },
            )

            return json.loads(response["message"]["content"])

        except Exception as e:
            logger.error(f"Failed to analyze message for tools: {e}")
            # Return a fallback response
            return {
                "should_use_tools": False,
                "recommended_tools": [],
                "analysis": f"Error analyzing message: {e}",
            }

    def synthesize_response_with_tools(
        self,
        user_message: str,
        tool_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response that incorporates tool results.

        Args:
            user_message: Original user message
            tool_results: Results from tool executions
            context: Optional context information

        Returns:
            Generated response incorporating tool results
        """
        try:
            # Prepare context from tool results
            tool_context = ""
            for result in tool_results:
                if result.get("success") and result.get("data"):
                    tool_name = result.get("tool_name", "unknown")
                    data = result["data"]

                    if tool_name == "journal_search" and data.get("results"):
                        tool_context += "\n\nRelevant journal entries found:\n"
                        for entry in data["results"]:
                            tool_context += f"- {entry['date']}: {entry['title']}\n"
                            tool_context += f"  {entry['content_preview']}\n"
                            if entry.get("tags"):
                                tool_context += f"  Tags: {', '.join(entry['tags'])}\n"
                    elif tool_name == "web_search" and data.get("results"):
                        tool_context += f"\n\nWeb search results for '{data.get('query', 'your query')}':\n"
                        tool_context += "=" * 50 + "\n"
                        for idx, result in enumerate(data["results"], 1):
                            tool_context += f"\nResult {idx}:\n"
                            tool_context += f"Title: {result['title']}\n"
                            tool_context += f"Source: {result['source']}\n"
                            tool_context += f"Content: {result['snippet']}\n"
                            if result.get("url"):
                                tool_context += f"URL: {result['url']}\n"
                            tool_context += "-" * 30 + "\n"
                        tool_context += "=" * 50
                    else:
                        tool_context += f"\n\nTool {tool_name} results: {data}\n"

            # Get current date for context
            from datetime import datetime

            current_date = datetime.now().strftime("%B %d, %Y")

            # Create system prompt that emphasizes using the tool results
            # Don't duplicate instructions if persona already has tool awareness
            base_instructions = f"""Today's date is {current_date}. Use this as the reference point for "current" or "today" when responding.

When tool results are provided, you MUST use them as the primary source for your response:

For journal search results:
- Reference specific entries by date and title
- Quote relevant content from the user's journal
- Mention the dates of entries when referencing them

For web search results:
- YOU MUST base your answer ENTIRELY on the provided search results
- Cite specific sources by mentioning the result number and source name
- Quote or paraphrase information from the search results
- DO NOT add information that isn't in the search results
- If the search results don't fully answer the question, acknowledge what information is missing

CRITICAL: When web search results are provided, your response MUST be based on those results. Do not use general knowledge or make up information. Always cite which search result you're referencing."""

            # Use existing system prompt (which may be persona-specific) with tool context
            existing_prompt = (
                self.system_prompt or "You are a helpful journaling assistant."
            )

            # Only add tool context if not already present
            if "search tools" in existing_prompt:
                system_prompt = f"{existing_prompt}\n\n{base_instructions}"
            else:
                system_prompt = f"{existing_prompt} You have access to search tools to help provide better responses.\n\n{base_instructions}"

            # Prepare the conversation context
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available
            if context and context.get("conversation_history"):
                for msg in context["conversation_history"][
                    -5:
                ]:  # Last 5 messages for context
                    messages.append(
                        {
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                        }
                    )

            # Add the current user message
            messages.append({"role": "user", "content": user_message})

            # Add tool context as a separate system message to make it clearer to the LLM
            if tool_context:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Here are the search results to answer the user's question:{tool_context}\n\nPlease use these search results to provide an accurate, detailed response to the user's question.",
                    }
                )

            response = ollama.chat(
                model=self._get_model_for_operation("chat"),
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Failed to synthesize response with tools: {e}")
            # Fallback to basic response
            return self.generate_response_with_model(
                [
                    {
                        "role": "system",
                        "content": self.system_prompt or "You are a helpful assistant.",
                    },
                    {"role": "user", "content": user_message},
                ]
            )
