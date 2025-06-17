#!/usr/bin/env python3
"""
Test script for the tool calling framework.
"""
import tempfile
import logging
from datetime import datetime

from app.tools import ToolRegistry, JournalSearchTool
from app.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tool_registry():
    """Test the tool registry functionality."""
    print("=== Testing Tool Registry ===")

    # Create a registry
    registry = ToolRegistry()

    # Create and register a journal search tool
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_tool = JournalSearchTool(base_dir=temp_dir)
        registry.register(journal_tool, enabled=True)

        # Test registry functions
        print(f"Total tools: {len(registry.list_tools())}")
        print(f"Enabled tools: {len(registry.list_tools(enabled_only=True))}")
        print(f"Journal search enabled: {registry.is_enabled('journal_search')}")

        # Test tool info
        tool_info = registry.get_info()
        print(f"Registry info: {tool_info}")

        # Test tool trigger logic
        test_messages = [
            "What did I write yesterday?",
            "Tell me about my entries from last week",
            "Hello, how are you?",
            "What's the weather like?",
            "Can you find my notes about the project?",
            "Remember when I mentioned the meeting?",
        ]

        print("\n--- Testing Tool Triggering ---")
        for message in test_messages:
            tool = registry.get_tool("journal_search")
            should_trigger = tool.should_trigger(message)
            print(f"'{message}' -> Trigger: {should_trigger}")


def test_llm_tool_analysis():
    """Test LLM-based tool analysis (requires Ollama)."""
    print("\n=== Testing LLM Tool Analysis ===")

    try:
        # Initialize LLM service
        llm_service = LLMService()

        test_messages = [
            "What did I write about my vacation last month?",
            "Hello, how are you today?",
            "Can you help me remember what I said about the project?",
            "Tell me about my mood patterns",
            "What's the capital of France?",
        ]

        print("\n--- Testing LLM Analysis ---")
        for message in test_messages:
            try:
                analysis = llm_service.analyze_message_for_tools(message)
                print(f"\nMessage: '{message}'")
                print(f"Should use tools: {analysis.get('should_use_tools', False)}")
                print(
                    f"Recommended tools: {len(analysis.get('recommended_tools', []))}"
                )

                for tool_rec in analysis.get("recommended_tools", []):
                    print(
                        f"  - {tool_rec.get('tool_name')} (confidence: {tool_rec.get('confidence'):.2f})"
                    )
                    print(f"    Reason: {tool_rec.get('reason')}")

            except Exception as e:
                print(f"Error analyzing message '{message}': {e}")

    except Exception as e:
        print(f"Could not test LLM analysis (Ollama may not be running): {e}")


def test_tool_execution():
    """Test tool execution."""
    print("\n=== Testing Tool Execution ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create registry and tool
            registry = ToolRegistry()
            journal_tool = JournalSearchTool(base_dir=temp_dir)
            registry.register(journal_tool, enabled=True)

            # Test parameters
            test_params = {"query": "test search query", "limit": 3}

            print(f"Testing tool execution with params: {test_params}")

            # Test validation
            tool = registry.get_tool("journal_search")
            validated_params = tool.validate_parameters(test_params)
            print(f"Validated parameters: {validated_params}")

            print(
                "Tool execution test completed (no actual search performed due to empty database)"
            )

        except Exception as e:
            print(f"Error in tool execution test: {e}")


def main():
    """Run all tests."""
    print("Testing Tool Calling Framework")
    print("=" * 50)

    test_tool_registry()
    test_llm_tool_analysis()
    test_tool_execution()

    print("\n" + "=" * 50)
    print("Tool calling framework test completed!")


if __name__ == "__main__":
    main()
