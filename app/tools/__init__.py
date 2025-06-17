"""
Tool calling framework for intelligent chat interactions.

This module provides a framework for implementing and managing tools that can be
called by the chat system to perform specific tasks like searching journal entries,
analyzing patterns, or processing user requests.
"""

from .base import BaseTool, ToolResult, ToolError
from .registry import ToolRegistry
from .journal_search import JournalSearchTool
from .web_search import WebSearchTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolError",
    "ToolRegistry",
    "JournalSearchTool",
    "WebSearchTool",
]
