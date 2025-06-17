"""
Web search tool for accessing external information.
"""

import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseTool, ToolResult, ToolError

try:
    from duckduckgo_search import DDGS

    ddgs_available = True
except ImportError:
    ddgs_available = False

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo with intelligent triggering."""

    def __init__(self, config_storage=None):
        """
        Initialize the web search tool.

        Args:
            config_storage: ConfigStorage instance for retrieving web search settings
        """
        super().__init__(
            name="web_search",
            description="Search the web for current information, facts, and external knowledge",
            version="1.0.0",
        )
        self.config_storage = config_storage

        # Rate limiting storage
        self._search_timestamps = []
        self._search_cache = {}  # Simple cache for duplicate queries
        self._cache_duration = 3600  # 1 hour cache

        # Keywords that suggest web search is needed
        self.web_search_keywords = [
            "what is",
            "who is",
            "when did",
            "when was",
            "how does",
            "how did",
            "current",
            "latest",
            "recent",
            "news",
            "today",
            "now",
            "current events",
            "definition",
            "explain",
            "meaning",
            "wikipedia",
            "google",
            "search",
            "weather",
            "price",
            "cost",
            "stock",
            "quote",
            "exchange rate",
            "population",
            "capital",
            "president",
            "ceo",
            "founded",
            "born",
            "facts about",
            "information about",
            "details about",
            "tell me about",
            "lookup",
            "find out",
            "research",
            "investigate",
            "verify",
        ]

        # Question patterns that often need external information
        self.external_info_patterns = [
            r"\bwhat\s+(is|are|was|were)\s+(?:the\s+)?(?:current|latest|recent)\b",
            r"\bhow\s+(?:much|many)\s+(?:is|are|does|did)\b",
            r"\bwhen\s+(?:did|was|is)\s+.+(?:born|founded|created|invented)\b",
            r"\bwho\s+(?:is|was)\s+(?:the\s+)?(?:current|latest)\b",
            r"\bwhere\s+(?:is|was)\s+.+(?:located|situated|based)\b",
            r"\b(?:price|cost|value)\s+of\b",
            r"\b(?:population|area|size)\s+of\b",
            r"\bcapital\s+of\b",
            r"\b(?:currency|exchange\s+rate)\b",
            r"\bweather\s+(?:in|at|for)\b",
            r"\bnews\s+(?:about|on)\b",
            r"\b(?:latest|recent)\s+(?:news|updates|developments)\b",
        ]

        # Patterns that suggest internal journal search instead
        self.internal_search_indicators = [
            r"\b(?:my|mine|i)\s+(?:wrote|said|mentioned|noted|recorded)\b",
            r"\b(?:yesterday|last\s+week|last\s+month|ago)\b",
            r"\b(?:entry|journal|diary|notes)\b",
            r"\b(?:remember|recall|mentioned\s+(?:before|earlier))\b",
            r"\bwhen\s+did\s+i\b",
            r"\bwhat\s+did\s+i\b",
        ]

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for web search parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for finding information on the web",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
                "search_type": {
                    "type": "string",
                    "enum": ["general", "news", "images"],
                    "default": "general",
                    "description": "Type of search to perform",
                },
                "region": {
                    "type": "string",
                    "description": "Region for localized results (e.g., 'us-en', 'uk-en')",
                    "default": "wt-wt",
                },
                "max_snippet_length": {
                    "type": "integer",
                    "description": "Maximum length of result snippets",
                    "default": 200,
                    "minimum": 50,
                    "maximum": 500,
                },
            },
            "required": ["query"],
        }

    def should_trigger(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if web search should be triggered for this message.

        Args:
            message: User message to analyze
            context: Optional context (conversation history, etc.)

        Returns:
            True if web search should be triggered
        """
        if not ddgs_available:
            self.logger.warning("DuckDuckGo search not available - skipping web search")
            return False

        # Check if web search is enabled
        if self.config_storage:
            try:
                config = self.config_storage.get_web_search_config()
                if not config or not config.enabled:
                    return False
            except Exception as e:
                self.logger.debug(f"Could not retrieve web search config: {e}")
                return False

        message_lower = message.lower()

        # Strong indicators against web search (favor journal search)
        internal_score = sum(
            1
            for pattern in self.internal_search_indicators
            if re.search(pattern, message_lower, re.IGNORECASE)
        )

        if internal_score >= 2:
            self.logger.debug(
                f"High internal search score ({internal_score}) - skipping web search"
            )
            return False

        # Calculate web search confidence
        confidence = 0

        # Keyword matches
        keyword_score = sum(
            1 for keyword in self.web_search_keywords if keyword in message_lower
        )
        confidence += keyword_score * 0.2

        # External info patterns
        pattern_matches = sum(
            1
            for pattern in self.external_info_patterns
            if re.search(pattern, message_lower, re.IGNORECASE)
        )
        confidence += pattern_matches * 0.4

        # Questions starting with interrogatives often need external info
        if re.match(r"^\s*(?:what|who|when|where|how|why)\s+", message_lower):
            confidence += 0.3

        # Requests for definitions or explanations
        if any(
            term in message_lower
            for term in ["define", "explain", "meaning of", "what is"]
        ):
            confidence += 0.3

        # Current events indicators
        if any(
            term in message_lower
            for term in ["current", "latest", "recent", "today", "now"]
        ):
            confidence += 0.25

        # Reduce confidence if it seems like a personal/journal question
        if internal_score > 0:
            confidence -= internal_score * 0.3

        # Context analysis
        if context:
            session_context = context.get("session_context", "").lower()
            # If conversation is heavily journal-focused, reduce web search confidence
            if any(
                term in session_context
                for term in ["journal", "entry", "wrote", "yesterday"]
            ):
                confidence -= 0.2

        # Threshold for triggering web search
        trigger_threshold = 0.5

        self.logger.debug(
            f"Web search trigger analysis for '{message}': "
            f"keywords={keyword_score}, patterns={pattern_matches}, "
            f"internal={internal_score}, confidence={confidence:.2f}, "
            f"trigger={confidence >= trigger_threshold}"
        )

        return confidence >= trigger_threshold

    def get_trigger_keywords(self) -> List[str]:
        """Get keywords that might trigger web search."""
        return self.web_search_keywords

    async def execute(
        self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute web search with the given parameters.

        Args:
            parameters: Search parameters (query, num_results, etc.)
            context: Optional context (session_id, user preferences, etc.)

        Returns:
            ToolResult with search results
        """
        if not ddgs_available:
            raise ToolError("DuckDuckGo search library not available", self.name)

        try:
            query = parameters["query"]
            num_results = parameters.get("num_results", 5)
            search_type = parameters.get("search_type", "general")
            region = parameters.get("region", "wt-wt")
            max_snippet_length = parameters.get("max_snippet_length", 200)

            # Check rate limits
            if not self._check_rate_limit():
                raise ToolError(
                    "Rate limit exceeded. Please try again later.", self.name
                )

            # Check cache first
            cache_key = f"{query}:{num_results}:{search_type}:{region}"
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(f"Returning cached result for query: {query}")
                return ToolResult(
                    success=True,
                    data=cached_result,
                    metadata={"tool_name": self.name, "cached": True, "query": query},
                )

            self.logger.info(
                f"Executing web search: query='{query}', results={num_results}, type={search_type}"
            )

            # Record search timestamp for rate limiting
            self._search_timestamps.append(time.time())

            # Perform the search
            results = []

            try:
                with DDGS() as ddgs:
                    if search_type == "news":
                        search_results = list(
                            ddgs.news(
                                keywords=query, region=region, max_results=num_results
                            )
                        )
                    else:  # general search
                        search_results = list(
                            ddgs.text(
                                keywords=query, region=region, max_results=num_results
                            )
                        )

                # Format results
                for result in search_results:
                    formatted_result = {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": self._truncate_snippet(
                            result.get("body", ""), max_snippet_length
                        ),
                        "published": result.get("date", ""),
                        "source": self._extract_domain(result.get("href", "")),
                    }
                    results.append(formatted_result)

                # Cache the results
                result_data = {
                    "results": results,
                    "query": query,
                    "total_found": len(results),
                    "search_type": search_type,
                    "timestamp": datetime.now().isoformat(),
                }
                self._cache_result(cache_key, result_data)

                return ToolResult(
                    success=True,
                    data=result_data,
                    metadata={
                        "tool_name": self.name,
                        "search_parameters": parameters,
                        "result_count": len(results),
                        "cached": False,
                    },
                )

            except Exception as search_error:
                self.logger.error(f"Search execution failed: {search_error}")
                raise ToolError(f"Web search failed: {search_error}", self.name)

        except ToolError:
            raise
        except Exception as e:
            self.logger.error(f"Web search execution failed: {e}")
            raise ToolError(f"Search execution failed: {e}", self.name)

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        if not self.config_storage:
            # Default rate limit: 10 searches per minute
            max_searches_per_minute = 10
        else:
            try:
                config = self.config_storage.get_web_search_config()
                max_searches_per_minute = (
                    config.max_searches_per_minute if config else 10
                )
            except:
                max_searches_per_minute = 10

        # Clean old timestamps (older than 1 minute)
        current_time = time.time()
        self._search_timestamps = [
            ts for ts in self._search_timestamps if current_time - ts < 60
        ]

        return len(self._search_timestamps) < max_searches_per_minute

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result if still valid."""
        if cache_key in self._search_cache:
            cached_data, timestamp = self._search_cache[cache_key]
            if time.time() - timestamp < self._cache_duration:
                return cached_data
            else:
                # Remove expired cache entry
                del self._search_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache search result."""
        self._search_cache[cache_key] = (data, time.time())

        # Clean old cache entries periodically
        if len(self._search_cache) > 100:  # Limit cache size
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, timestamp) in self._search_cache.items()
                if current_time - timestamp > self._cache_duration
            ]
            for key in expired_keys:
                del self._search_cache[key]

    def _truncate_snippet(self, text: str, max_length: int) -> str:
        """Truncate snippet to specified length."""
        if len(text) <= max_length:
            return text

        # Try to break at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.8:  # Only break at word if it's not too short
            truncated = truncated[:last_space]

        return truncated + "..."

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for display."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return url

    async def health_check(self) -> bool:
        """Check if the web search tool is healthy."""
        if not ddgs_available:
            return False

        try:
            # Try a simple test search
            with DDGS() as ddgs:
                test_results = list(ddgs.text("test", max_results=1))
                return len(test_results) > 0
        except Exception as e:
            self.logger.error(f"Web search health check failed: {e}")
            return False
