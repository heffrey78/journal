"""
LLM Service for the journal application.

This module provides integration with Ollama for
embedding generation and structured outputs.
"""

import ollama
import logging
import json
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel
from app.storage import StorageManager
from app.models import LLMConfig, BatchAnalysis, JournalEntry

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
        try:
            # Call Ollama's embeddings endpoint
            response = ollama.embeddings(model=self.model_name, prompt=text)

            if "embedding" in response:
                return response["embedding"]
            else:
                raise LLMServiceError("Invalid response from Ollama embeddings API")

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise LLMServiceError(f"Failed to generate embedding: {e}")

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
            response = ollama.chat(
                model=self.model_name,
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
                    model=self.model_name,
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
                model=self.model_name,
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

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion response using Ollama.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Optional temperature parameter (0-1) to control randomness
            max_tokens: Optional maximum tokens to generate

        Returns:
            Dictionary containing the response

        Raises:
            LLMServiceError: If the chat completion fails
        """
        try:
            # Use provided parameters or fall back to class defaults
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            # Call Ollama for chat completion
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"temperature": temp, "num_predict": tokens},
            )

            return response
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise LLMServiceError(f"Failed to generate chat completion: {e}")
