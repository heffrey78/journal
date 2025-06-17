"""
Base classes for the tool calling framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolError(Exception):
    """Exception raised when a tool execution fails."""

    def __init__(
        self, message: str, tool_name: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.tool_name = tool_name
        self.details = details or {}


@dataclass
class ToolCall:
    """Represents a tool call request."""

    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseTool(ABC):
    """Base class for all tools in the framework."""

    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """
        Initialize the tool.

        Args:
            name: Unique name for the tool
            description: Human-readable description of what the tool does
            version: Version of the tool implementation
        """
        self.name = name
        self.description = description
        self.version = version
        self.logger = logging.getLogger(f"tools.{name}")

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for the tool's parameters.

        This schema is used by the LLM to understand how to call the tool
        and what parameters it expects.

        Returns:
            JSON schema dictionary defining the tool's parameters
        """
        pass

    @abstractmethod
    async def execute(
        self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            parameters: Tool parameters as validated by the schema
            context: Optional context information (session_id, user_id, etc.)

        Returns:
            ToolResult containing the execution result

        Raises:
            ToolError: If the tool execution fails
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize tool parameters against the schema.

        Args:
            parameters: Raw parameters to validate

        Returns:
            Validated and normalized parameters

        Raises:
            ToolError: If parameters are invalid
        """
        # Basic validation - subclasses can override for more sophisticated validation
        schema = self.get_schema()
        required_params = schema.get("required", [])

        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise ToolError(
                    f"Missing required parameter: {param}",
                    tool_name=self.name,
                    details={
                        "required_params": required_params,
                        "provided_params": list(parameters.keys()),
                    },
                )

        return parameters

    def should_trigger(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if this tool should be triggered for the given message.

        This method implements the intelligence for when to use this tool.
        It should return True if the tool is relevant for the current message.

        Args:
            message: User message to analyze
            context: Optional context (conversation history, session info, etc.)

        Returns:
            True if the tool should be triggered, False otherwise
        """
        # Default implementation - subclasses should override with intelligent logic
        return False

    def get_trigger_keywords(self) -> List[str]:
        """
        Get a list of keywords that might trigger this tool.

        This is used as a fallback when more sophisticated triggering logic
        isn't available or as an optimization.

        Returns:
            List of keywords that might indicate this tool should be used
        """
        return []

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this tool.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema": self.get_schema(),
            "trigger_keywords": self.get_trigger_keywords(),
        }

    async def health_check(self) -> bool:
        """
        Check if the tool is healthy and ready to use.

        Returns:
            True if the tool is healthy, False otherwise
        """
        # Default implementation - tools can override for specific health checks
        return True

    def __str__(self) -> str:
        return f"{self.name} v{self.version}: {self.description}"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"
        )
