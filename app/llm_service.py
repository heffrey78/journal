"""
LLM Service for the journal application.

This module provides integration with Ollama for
embedding generation and structured outputs.
"""
import ollama
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.storage import StorageManager


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
        model_name: str = "qwen3:latest",
        storage_manager: Optional[StorageManager] = None,
    ):
        """
        Initialize the LLM service.

        Args:
            model_name: Ollama model to use
            storage_manager: Optional reference to the storage manager
        """
        self.model_name = model_name
        self.storage_manager = storage_manager

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text using Ollama.

        Args:
            text: The text to generate an embedding for

        Returns:
            Numpy array containing the embedding vector
        """
        try:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            return np.array(response["embedding"], dtype=np.float32)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return empty embedding as fallback
            return np.zeros(4096, dtype=np.float32)

    def process_entries_without_embeddings(self, limit: int = 10) -> int:
        """
        Process entries that don't have embeddings yet.

        Args:
            limit: Maximum number of chunks to process

        Returns:
            Number of chunks processed
        """
        if not self.storage_manager:
            raise ValueError("Storage manager is required for this operation")

        chunks = self.storage_manager.get_chunks_without_embeddings(limit)
        if not chunks:
            return 0

        for chunk in chunks:
            entry_id = chunk["entry_id"]
            chunk_id = chunk["chunk_id"]
            text = chunk["text"]

            # Generate embedding
            embedding = self.get_embedding(text)

            # Update storage with embedding
            self.storage_manager.update_vectors_with_embeddings(
                entry_id, {chunk_id: embedding}
            )

        return len(chunks)

    def summarize_entry(self, content: str) -> EntrySummary:
        """
        Generate a summary of a journal entry using structured output.

        Args:
            content: The journal entry content to summarize

        Returns:
            EntrySummary object with summary, key topics and mood
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this journal entry. "
                        f"Extract key topics and mood. Return as JSON:\n\n{content}",
                    }
                ],
                format={
                    "schema": {
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
                    }
                },
            )

            # Parse the response into the EntrySummary model
            content = response["message"]["content"]
            return EntrySummary.model_validate_json(content)
        except Exception as e:
            print(f"Error summarizing entry: {e}")
            # Return fallback summary
            return EntrySummary(
                summary="Failed to generate summary.",
                key_topics=["error"],
                mood="unknown",
            )

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on journal entries.

        Args:
            query: The search query text
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        if not self.storage_manager:
            raise ValueError("Storage manager is required for this operation")

        # Generate embedding for the query
        query_embedding = self.get_embedding(query)

        # Search using the storage manager
        results = self.storage_manager.semantic_search(query_embedding, limit)

        return results
