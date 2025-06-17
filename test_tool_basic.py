#!/usr/bin/env python3
"""
Basic test script for the tool calling framework.
"""
import tempfile
import logging
from datetime import datetime

from app.tools import ToolRegistry, JournalSearchTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tool_registry_basic():
    """Test the basic tool registry functionality."""
    print("=== Testing Tool Registry Basic Functionality ===")

    # Create a registry
    registry = ToolRegistry()

    # Create and register a journal search tool
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_tool = JournalSearchTool(base_dir=temp_dir)
        registry.register(journal_tool, enabled=True)

        # Test registry functions
        print(f"✓ Total tools: {len(registry.list_tools())}")
        print(f"✓ Enabled tools: {len(registry.list_tools(enabled_only=True))}")
        print(f"✓ Journal search enabled: {registry.is_enabled('journal_search')}")

        # Test tool info
        tool_info = journal_tool.get_info()
        print(f"✓ Tool name: {tool_info['name']}")
        print(f"✓ Tool description: {tool_info['description']}")
        print(f"✓ Tool version: {tool_info['version']}")

        # Test tool schema
        schema = journal_tool.get_schema()
        print(f"✓ Schema has properties: {len(schema.get('properties', {}))}")

        return True


def test_tool_triggering():
    """Test the tool triggering logic."""
    print("\n=== Testing Tool Triggering Logic ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        journal_tool = JournalSearchTool(base_dir=temp_dir)

        test_cases = [
            ("What did I write yesterday?", True),
            ("Tell me about my entries from last week", True),
            ("Hello, how are you?", False),
            ("What's the weather like?", False),
            ("Can you find my notes about the project?", True),
            ("Remember when I mentioned the meeting?", True),
            ("How do I cook pasta?", False),
            ("What did I say about vacation?", True),
        ]

        correct_predictions = 0
        for message, expected in test_cases:
            should_trigger = journal_tool.should_trigger(message)
            status = "✓" if should_trigger == expected else "✗"
            print(
                f"{status} '{message}' -> Trigger: {should_trigger} (expected: {expected})"
            )
            if should_trigger == expected:
                correct_predictions += 1

        accuracy = correct_predictions / len(test_cases)
        print(
            f"\n✓ Trigger accuracy: {accuracy:.1%} ({correct_predictions}/{len(test_cases)})"
        )

        return accuracy > 0.7  # Expect at least 70% accuracy


def test_parameter_validation():
    """Test parameter validation."""
    print("\n=== Testing Parameter Validation ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        journal_tool = JournalSearchTool(base_dir=temp_dir)

        # Test valid parameters
        try:
            valid_params = {"query": "test search", "limit": 5}
            validated = journal_tool.validate_parameters(valid_params)
            print(f"✓ Valid parameters accepted: {validated}")
        except Exception as e:
            print(f"✗ Valid parameters rejected: {e}")
            return False

        # Test missing required parameter
        try:
            invalid_params = {"limit": 5}  # missing query
            journal_tool.validate_parameters(invalid_params)
            print("✗ Missing required parameter not caught")
            return False
        except Exception as e:
            print(f"✓ Missing required parameter caught: {e}")

        return True


def main():
    """Run all basic tests."""
    print("Testing Tool Calling Framework - Basic Functionality")
    print("=" * 60)

    tests_passed = 0
    total_tests = 3

    if test_tool_registry_basic():
        tests_passed += 1
        print("✓ Tool registry basic test passed")
    else:
        print("✗ Tool registry basic test failed")

    if test_tool_triggering():
        tests_passed += 1
        print("✓ Tool triggering test passed")
    else:
        print("✗ Tool triggering test failed")

    if test_parameter_validation():
        tests_passed += 1
        print("✓ Parameter validation test passed")
    else:
        print("✗ Parameter validation test failed")

    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All basic tool calling framework tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
