"""
Journal search tool for intelligent entry retrieval.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseTool, ToolResult, ToolError
from app.storage.vector_search import VectorStorage
from app.storage.entries import EntryStorage

logger = logging.getLogger(__name__)


class JournalSearchTool(BaseTool):
    """Tool for searching journal entries with intelligent triggering."""

    def __init__(self, base_dir: str = "./journal_data", llm_service=None):
        """
        Initialize the journal search tool.

        Args:
            base_dir: Base directory for journal data storage
            llm_service: Optional LLM service for semantic search
        """
        super().__init__(
            name="journal_search",
            description="Search journal entries based on content, dates, and semantic similarity",
            version="1.0.0",
        )
        self.base_dir = base_dir
        self.llm_service = llm_service
        self.vector_storage = VectorStorage(base_dir)
        self.entry_storage = EntryStorage(base_dir)

        # Keywords that strongly suggest journal search is needed
        self.search_keywords = [
            "remember",
            "recall",
            "wrote",
            "entry",
            "journal",
            "diary",
            "yesterday",
            "last week",
            "last month",
            "ago",
            "before",
            "when did",
            "what did",
            "tell me about",
            "find",
            "search",
            "mentioned",
            "discussed",
            "talked about",
            "notes",
            "recorded",
            "previous",
            "earlier",
            "past",
            "history",
            "memories",
        ]

        # Date-related patterns
        self.date_patterns = [
            r"\b\d{1,2}\/\d{1,2}\/\d{2,4}\b",  # MM/DD/YYYY or M/D/YY
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",  # YYYY-MM-DD
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
            r"\b(yesterday|today|tomorrow)\b",
            r"\b\d+\s+(days?|weeks?|months?|years?)\s+ago\b",
            r"\blast\s+(week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        ]

        # Question patterns that suggest looking for past information
        self.question_patterns = [
            r"\bwhat\s+(did|was|were)\b",
            r"\bhow\s+(did|was|were)\b",
            r"\bwhen\s+(did|was|were)\b",
            r"\bwhere\s+(did|was|were)\b",
            r"\bwhy\s+(did|was|were)\b",
            r"\bcan you (tell|remind|find|search|look up)\b",
            r"\bdo you (remember|recall|know about)\b",
        ]

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for journal search parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for finding relevant journal entries",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entries to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "date_filter": {
                    "type": "object",
                    "description": "Optional date range filter",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "description": "End date (YYYY-MM-DD)",
                        },
                    },
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags to filter by",
                },
                "search_type": {
                    "type": "string",
                    "enum": ["semantic", "text", "both"],
                    "default": "both",
                    "description": "Type of search to perform",
                },
            },
            "required": ["query"],
        }

    def should_trigger(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if journal search should be triggered for this message.

        Args:
            message: User message to analyze
            context: Optional context (conversation history, etc.)

        Returns:
            True if journal search should be triggered
        """
        message_lower = message.lower()

        # Strong indicators for journal search
        keyword_score = 0
        for keyword in self.search_keywords:
            if keyword in message_lower:
                keyword_score += 1

        # Check for date patterns
        has_date_pattern = any(
            re.search(pattern, message_lower, re.IGNORECASE)
            for pattern in self.date_patterns
        )

        # Check for question patterns
        has_question_pattern = any(
            re.search(pattern, message_lower, re.IGNORECASE)
            for pattern in self.question_patterns
        )

        # Calculate confidence score
        confidence = 0

        # Strong keyword matches
        if keyword_score > 0:
            confidence += keyword_score * 0.3

        # Date references add significant confidence
        if has_date_pattern:
            confidence += 0.4

        # Questions about past events
        if has_question_pattern:
            confidence += 0.3

        # Length and complexity bonus (longer, more specific queries are more likely to need search)
        if len(message.split()) > 5:
            confidence += 0.1

        # Context analysis (if available)
        if context:
            # If the conversation is already about journal entries, increase confidence
            session_context = context.get("session_context", "")
            if any(
                keyword in session_context.lower()
                for keyword in ["entry", "journal", "wrote", "remember"]
            ):
                confidence += 0.2

        # Threshold for triggering search
        trigger_threshold = 0.5

        self.logger.debug(
            f"Journal search trigger analysis for '{message}': "
            f"keywords={keyword_score}, date={has_date_pattern}, "
            f"question={has_question_pattern}, confidence={confidence:.2f}, "
            f"trigger={confidence >= trigger_threshold}"
        )

        return confidence >= trigger_threshold

    def get_trigger_keywords(self) -> List[str]:
        """Get keywords that might trigger journal search."""
        return self.search_keywords

    async def execute(
        self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute journal search with the given parameters.

        Args:
            parameters: Search parameters (query, limit, filters, etc.)
            context: Optional context (session_id, user preferences, etc.)

        Returns:
            ToolResult with search results
        """
        try:
            query = parameters["query"]
            limit = parameters.get("limit", 5)
            date_filter = parameters.get("date_filter")
            tags = parameters.get("tags")
            search_type = parameters.get("search_type", "both")

            self.logger.info(
                f"Executing journal search: query='{query}', limit={limit}, type={search_type}"
            )

            # Perform the search based on type
            results = []

            if search_type in ["semantic", "both"]:
                # Semantic search using vector embeddings
                try:
                    semantic_results = await self._semantic_search(
                        query, limit, date_filter, tags
                    )
                    results.extend(semantic_results)
                    self.logger.debug(
                        f"Semantic search returned {len(semantic_results)} results"
                    )
                except Exception as e:
                    self.logger.warning(f"Semantic search failed: {e}")
                    if search_type == "semantic":
                        # Fall back to text search if semantic-only search fails
                        search_type = "text"

            if search_type in ["text", "both"] and (
                not results or search_type == "text"
            ):
                # Text-based search
                try:
                    text_results = await self._text_search(
                        query, limit, date_filter, tags
                    )
                    if search_type == "text":
                        results = text_results
                    else:
                        # Merge and deduplicate results
                        results = self._merge_results(results, text_results, limit)
                    self.logger.debug(
                        f"Text search returned {len(text_results)} results"
                    )
                except Exception as e:
                    self.logger.warning(f"Text search failed: {e}")
                    if not results:
                        raise ToolError(f"Both search methods failed: {e}", self.name)

            # Format results for LLM consumption
            formatted_results = self._format_results(results)

            return ToolResult(
                success=True,
                data={
                    "results": formatted_results,
                    "query": query,
                    "total_found": len(results),
                    "search_type": search_type,
                },
                metadata={
                    "tool_name": self.name,
                    "search_parameters": parameters,
                    "result_count": len(results),
                },
            )

        except ToolError:
            raise
        except Exception as e:
            self.logger.error(f"Journal search execution failed: {e}")
            raise ToolError(f"Search execution failed: {e}", self.name)

    async def _semantic_search(
        self,
        query: str,
        limit: int,
        date_filter: Optional[Dict],
        tags: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings."""
        # Use the LLM service's semantic search if available
        if self.llm_service:
            search_results = self.llm_service.semantic_search(
                query=query, limit=limit, date_filter=date_filter
            )
        else:
            # Fallback to direct vector search (requires pre-computed embeddings)
            # This is a simplified fallback - in practice, you'd need to generate embeddings
            search_results = []

        # Convert to standard format
        results = []
        for result in search_results:
            entry_data = {
                "entry_id": result["entry_id"],
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "created_at": result.get("created_at", ""),
                "tags": result.get("tags", []),
                "relevance_score": result.get("similarity_score", 0.0),
                "search_type": "semantic",
            }

            # Apply tag filter if specified
            if tags:
                entry_tags = set(entry_data.get("tags", []))
                if not any(
                    tag.lower() in [t.lower() for t in entry_tags] for tag in tags
                ):
                    continue

            results.append(entry_data)

        return results[:limit]

    async def _text_search(
        self,
        query: str,
        limit: int,
        date_filter: Optional[Dict],
        tags: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Perform text-based search."""
        # Use the entry storage's search functionality
        search_results = self.entry_storage.search_entries(
            query=query, tags=tags, date_filter=date_filter, limit=limit
        )

        # Convert to standard format
        results = []
        for entry in search_results:
            entry_data = {
                "entry_id": entry.id,
                "title": entry.title,
                "content": entry.content[:500] + "..."
                if len(entry.content) > 500
                else entry.content,
                "created_at": entry.created_at.isoformat() if entry.created_at else "",
                "tags": entry.tags or [],
                "relevance_score": 0.8,  # Default score for text search
                "search_type": "text",
            }
            results.append(entry_data)

        return results

    def _merge_results(
        self, semantic_results: List[Dict], text_results: List[Dict], limit: int
    ) -> List[Dict]:
        """Merge and deduplicate search results."""
        seen_ids = set()
        merged = []

        # Add semantic results first (typically higher quality)
        for result in semantic_results:
            entry_id = result["entry_id"]
            if entry_id not in seen_ids:
                seen_ids.add(entry_id)
                merged.append(result)

        # Add text results that weren't already found
        for result in text_results:
            entry_id = result["entry_id"]
            if entry_id not in seen_ids and len(merged) < limit:
                seen_ids.add(entry_id)
                merged.append(result)

        return merged[:limit]

    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results for LLM consumption."""
        formatted = []

        for result in results:
            # Create a concise, LLM-friendly representation
            formatted_result = {
                "id": result["entry_id"],
                "title": result["title"],
                "content_preview": result["content"][:300] + "..."
                if len(result["content"]) > 300
                else result["content"],
                "date": result["created_at"][:10]
                if result["created_at"]
                else "Unknown",
                "tags": result.get("tags", []),
                "relevance": round(result.get("relevance_score", 0.0), 2),
                "source": result.get("search_type", "unknown"),
            }
            formatted.append(formatted_result)

        return formatted

    async def health_check(self) -> bool:
        """Check if the journal search tool is healthy."""
        try:
            # Test basic connectivity to storage systems
            vector_healthy = await self._check_vector_storage()
            entry_healthy = await self._check_entry_storage()

            return vector_healthy and entry_healthy
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def _check_vector_storage(self) -> bool:
        """Check vector storage health."""
        try:
            # Try a simple search to verify the system is working
            test_results = self.vector_storage.search_entries("test", limit=1)
            return True
        except Exception:
            return False

    async def _check_entry_storage(self) -> bool:
        """Check entry storage health."""
        try:
            # Try to access the entry storage
            test_entries = self.entry_storage.search_entries("test", limit=1)
            return True
        except Exception:
            return False
