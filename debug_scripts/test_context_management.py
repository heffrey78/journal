#!/usr/bin/env python3
"""
Manual test script for the chat context management feature.

This script:
1. Sets up a test chat session
2. Adds a series of messages to simulate a long conversation
3. Tests the summarization and context windowing
4. Shows the resulting conversation context that would be sent to the LLM

Usage:
    python debug_scripts/test_context_management.py
"""

import os
import sys
from datetime import datetime
from app.models import ChatSession, ChatMessage, ChatConfig
from app.storage.chat import ChatStorage
from app.chat_service import ChatService
from app.llm_service import LLMService

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_mock_llm_service():
    """Create a simple mock LLM service for testing."""

    class MockLLMService(LLMService):
        def __init__(self):
            # Skip actual initialization that would connect to Ollama
            pass

        def chat_completion(self, messages, temperature=0.7, stream=False):
            """Mock chat completion that returns a summary."""
            if stream:
                return [
                    "This",
                    " is",
                    " a",
                    " test",
                    " summary",
                    " of",
                    " the",
                    " conversation",
                ]

            # If the last message is a summary request, generate a summary
            if messages[-1]["content"].startswith("Summarize"):
                # Extract user and assistant messages to include in summary
                topics = []
                for msg in messages:
                    if msg["role"] == "user" and "topic" in msg["content"].lower():
                        topic = (
                            msg["content"].split("topic:")[1].strip()
                            if "topic:" in msg["content"]
                            else "unknown"
                        )
                        topics.append(topic)

                topics_str = ", ".join(topics) if topics else "general conversation"
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "This conversation discussed these "
                                f"topics: {topics_str}. The user asked several "
                                "questions and the assistant provided responses."
                            }
                        }
                    ]
                }

            return {
                "choices": [
                    {
                        "message": {
                            "content": "This is a test response from the mock "
                            "LLM service."
                        }
                    }
                ]
            }

    return MockLLMService()


def create_test_messages(session_id, count=15):
    """Create a series of test messages to simulate a conversation."""
    messages = []
    topics = [
        "journal features",
        "chat capabilities",
        "search functionality",
        "data storage",
        "user interface",
        "performance optimization",
        "machine learning",
        "natural language processing",
    ]

    for i in range(count):
        # Alternate between user and assistant
        role = "user" if i % 2 == 0 else "assistant"

        if role == "user":
            # Create more detailed user messages with topics
            topic = topics[i // 2 % len(topics)]
            content = (
                f"Question about topic: {topic}. How does the journal app handle this?"
            )
        else:
            # Create assistant responses
            content = f"The journal app handles {topics[(i-1) // 2 % len(topics)]} "
            "through specialized algorithms and data structures."

        # Create the message
        message = ChatMessage(
            id=f"msg-test-{i+1}",
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.now(),
        )
        messages.append(message)

    return messages


def print_formatted_conversation(conversation, title="Conversation Context"):
    """Print a formatted representation of the conversation context."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

    for i, msg in enumerate(conversation):
        role = msg["role"].upper()
        if role == "SYSTEM" and "Summary of earlier conversation" in msg["content"]:
            print(f"\n[SUMMARY] {msg['content']}\n")
        else:
            print(f"\n[{role}]")
            # Truncate very long messages for display
            content = msg["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"{content}")

    print("\n" + "=" * 80 + "\n")


def init_test_database(storage_dir):
    """Initialize test database with necessary tables."""
    import sqlite3

    # Connect to the database
    db_path = os.path.join(storage_dir, "journal.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create chat_sessions table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            context_summary TEXT,
            temporal_filter TEXT,
            entry_count INTEGER DEFAULT 0
        )
        """
        )

        # Create chat_messages table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT,
            token_count INTEGER,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        )
        """
        )

        # Create chat_message_entries table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chat_message_entries (
            message_id TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            similarity_score REAL NOT NULL,
            chunk_index INTEGER,
            PRIMARY KEY (message_id, entry_id, chunk_index)
        )
        """
        )

        # Create chat_config table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chat_config (
            id TEXT PRIMARY KEY,
            system_prompt TEXT,
            temperature REAL,
            max_tokens INTEGER,
            retrieval_limit INTEGER,
            chunk_size INTEGER,
            chunk_overlap INTEGER,
            max_history INTEGER,
            use_enhanced_retrieval BOOLEAN,
            conversation_summary_threshold INTEGER,
            context_window_size INTEGER,
            use_context_windowing BOOLEAN,
            min_messages_for_summary INTEGER,
            summary_prompt TEXT
        )
        """
        )

        # Commit changes
        conn.commit()
        print("Test database tables created successfully")

    except Exception as e:
        print(f"Error creating test database tables: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    """Run the manual test for context management."""
    # Use a temporary directory for testing
    temp_dir = "/tmp/journal_chat_test"
    os.makedirs(temp_dir, exist_ok=True)

    # Initialize the test database
    init_test_database(temp_dir)

    # Create storage and services
    chat_storage = ChatStorage(temp_dir)
    llm_service = create_mock_llm_service()
    chat_service = ChatService(chat_storage, llm_service)

    # Create a test chat configuration with low thresholds for testing
    config = ChatConfig(
        id="default",
        system_prompt="You are an AI assistant for the journal app.",
        temperature=0.7,
        max_history=10,
        retrieval_limit=5,
        chunk_size=500,
        chunk_overlap=100,
        use_enhanced_retrieval=True,
        max_tokens=2048,
        max_context_tokens=1000,
        conversation_summary_threshold=20,  # Set low to trigger summarization easily
        context_window_size=4,  # Keep only 4 recent messages in full
        use_context_windowing=True,
        min_messages_for_summary=3,
        summary_prompt="Summarize the key points of this conversation so far "
        "in 3-4 sentences:",
    )

    # Save the config
    chat_storage.update_chat_config(config)

    # Create a test session
    session = ChatSession(
        id="test-context-session",
        title="Test Context Management Session",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_accessed=datetime.now(),
    )

    # Save the session
    chat_storage.create_session(session)
    session_id = session.id

    print(f"Created test session: {session_id}")

    # Create and save test messages
    messages = create_test_messages(session_id, count=10)
    for msg in messages:
        chat_storage.add_message(msg)

    print(f"Added {len(messages)} test messages to the session")

    # Get the conversation history without windowing
    # Temporarily disable windowing in config
    original_use_windowing = config.use_context_windowing
    config.use_context_windowing = False

    conversation_without_windowing = chat_service._prepare_conversation_history(
        session_id, config
    )

    # Restore windowing setting
    config.use_context_windowing = original_use_windowing

    # Get the conversation history with windowing
    conversation_with_windowing = chat_service._prepare_conversation_history(
        session_id, config
    )

    # Print both for comparison
    print_formatted_conversation(
        conversation_without_windowing, "WITHOUT CONTEXT WINDOWING"
    )
    print_formatted_conversation(conversation_with_windowing, "WITH CONTEXT WINDOWING")

    # Test updating the session summary
    print("\nTesting update_session_summary()...")
    result = chat_service.update_session_summary(session_id)
    print(f"Summary update successful: {result}")

    # Get the updated session
    updated_session = chat_storage.get_session(session_id)
    if updated_session.context_summary:
        print(f"Generated summary: {updated_session.context_summary}")
    else:
        print("No summary was generated")

    # Get conversation after explicit summarization
    conversation_after_summary = chat_service._prepare_conversation_history(
        session_id, config
    )
    print_formatted_conversation(
        conversation_after_summary, "AFTER EXPLICIT SUMMARIZATION"
    )

    # Test clearing the session summary
    print("\nTesting clear_session_summary()...")
    result = chat_service.clear_session_summary(session_id)
    print(f"Summary clearing successful: {result}")

    # Get conversation after clearing the summary
    conversation_after_clearing = chat_service._prepare_conversation_history(
        session_id, config
    )
    print_formatted_conversation(conversation_after_clearing, "AFTER CLEARING SUMMARY")

    # Clean up
    print("\nCleaning up...")
    chat_storage.delete_session(session_id)
    print("Test completed")


if __name__ == "__main__":
    main()
