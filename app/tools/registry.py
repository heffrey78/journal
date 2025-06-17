"""
Tool registry for managing available tools in the framework.
"""

from typing import Dict, List, Optional, Any, Set
import logging
from .base import BaseTool, ToolResult, ToolError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and accessing available tools."""

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._enabled_tools: Set[str] = set()

    def register(self, tool: BaseTool, enabled: bool = True) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register
            enabled: Whether the tool should be enabled by default

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool
        if enabled:
            self._enabled_tools.add(tool.name)

        logger.info(f"Registered tool: {tool.name} (enabled: {enabled})")

    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool from the registry.

        Args:
            tool_name: Name of the tool to unregister

        Raises:
            KeyError: If the tool is not registered
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered")

        del self._tools[tool_name]
        self._enabled_tools.discard(tool_name)

        logger.info(f"Unregistered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(tool_name)

    def list_tools(self, enabled_only: bool = False) -> List[BaseTool]:
        """
        List all registered tools.

        Args:
            enabled_only: If True, only return enabled tools

        Returns:
            List of tool instances
        """
        if enabled_only:
            return [
                tool
                for name, tool in self._tools.items()
                if name in self._enabled_tools
            ]
        return list(self._tools.values())

    def is_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is enabled, False otherwise
        """
        return tool_name in self._enabled_tools

    def enable_tool(self, tool_name: str) -> None:
        """
        Enable a tool.

        Args:
            tool_name: Name of the tool to enable

        Raises:
            KeyError: If the tool is not registered
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered")

        self._enabled_tools.add(tool_name)
        logger.info(f"Enabled tool: {tool_name}")

    def disable_tool(self, tool_name: str) -> None:
        """
        Disable a tool.

        Args:
            tool_name: Name of the tool to disable
        """
        self._enabled_tools.discard(tool_name)
        logger.info(f"Disabled tool: {tool_name}")

    async def find_relevant_tools(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> List[BaseTool]:
        """
        Find tools that are relevant for the given message.

        Args:
            message: User message to analyze
            context: Optional context information

        Returns:
            List of relevant tools, ordered by relevance
        """
        relevant_tools = []

        for tool in self.list_tools(enabled_only=True):
            try:
                if tool.should_trigger(message, context):
                    relevant_tools.append(tool)
            except Exception as e:
                logger.warning(
                    f"Error checking if tool {tool.name} should trigger: {e}"
                )

        # Sort by relevance (can be enhanced with scoring in the future)
        return relevant_tools

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Execute a specific tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            context: Optional context information

        Returns:
            ToolResult from the tool execution

        Raises:
            ToolError: If the tool is not found, disabled, or execution fails
        """
        # Check if tool exists
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ToolError(f"Tool '{tool_name}' not found", tool_name=tool_name)

        # Check if tool is enabled
        if not self.is_enabled(tool_name):
            raise ToolError(f"Tool '{tool_name}' is disabled", tool_name=tool_name)

        # Validate parameters
        try:
            validated_params = tool.validate_parameters(parameters)
        except Exception as e:
            raise ToolError(
                f"Parameter validation failed: {e}",
                tool_name=tool_name,
                details={"parameters": parameters},
            )

        # Execute the tool
        try:
            start_time = None
            import time

            start_time = time.time()

            result = await tool.execute(validated_params, context)

            if start_time is not None:
                execution_time = (
                    time.time() - start_time
                ) * 1000  # Convert to milliseconds
                if result.metadata is None:
                    result.metadata = {}
                result.execution_time_ms = execution_time

            logger.info(
                f"Tool {tool_name} executed successfully in {result.execution_time_ms:.2f}ms"
            )
            return result

        except ToolError:
            # Re-raise tool errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in ToolError
            raise ToolError(
                f"Tool execution failed: {e}",
                tool_name=tool_name,
                details={"parameters": validated_params},
            )

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health checks on all registered tools.

        Returns:
            Dictionary mapping tool names to their health status
        """
        health_status = {}

        for tool_name, tool in self._tools.items():
            try:
                health_status[tool_name] = await tool.health_check()
            except Exception as e:
                logger.warning(f"Health check failed for tool {tool_name}: {e}")
                health_status[tool_name] = False

        return health_status

    def get_tool_schemas(self, enabled_only: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Get schemas for all tools.

        Args:
            enabled_only: If True, only return schemas for enabled tools

        Returns:
            Dictionary mapping tool names to their schemas
        """
        schemas = {}

        for tool in self.list_tools(enabled_only=enabled_only):
            try:
                schemas[tool.name] = tool.get_schema()
            except Exception as e:
                logger.warning(f"Failed to get schema for tool {tool.name}: {e}")

        return schemas

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the registry and all tools.

        Returns:
            Dictionary with registry and tool information
        """
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len(self._enabled_tools),
            "tools": {name: tool.get_info() for name, tool in self._tools.items()},
            "health_status": None,  # Can be populated with async health check
        }
