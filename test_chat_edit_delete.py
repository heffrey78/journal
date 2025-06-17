#!/usr/bin/env python3
"""
Quick test script for chat message edit and delete functionality.
"""
import os
import tempfile
import shutil
from datetime import datetime
import uuid

from app.storage.chat import ChatStorage
from app.models import ChatSession, ChatMessage


def test_chat_edit_delete():
    """Test the edit and delete functionality for chat messages."""
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # Initialize storage
        storage = ChatStorage(base_dir=temp_dir)

        # Create a test session
        session = ChatSession(
            id=str(uuid.uuid4()),
            title="Test Chat Session",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        print(f"Creating session: {session.id}")
        created_session = storage.create_session(session)

        # Add some test messages
        messages = []
        for i in range(3):
            msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i+1}",
                created_at=datetime.now(),
            )
            storage.add_message(msg)
            messages.append(msg)
            print(f"Added message {i+1}: {msg.id}")

        # Test 1: Update a message
        print("\n--- Testing message update ---")
        message_to_update = messages[1]
        new_content = "This is the updated content!"

        print(f"Updating message {message_to_update.id}")
        print(f"Original content: '{message_to_update.content}'")
        print(f"New content: '{new_content}'")

        success = storage.update_message(message_to_update.id, new_content)
        print(f"Update success: {success}")

        # Verify the update
        updated_msg = storage.get_message(message_to_update.id)
        if updated_msg:
            print(f"Updated message content: '{updated_msg.content}'")
            print(f"Message metadata: {updated_msg.metadata}")
            assert updated_msg.content == new_content
            assert updated_msg.metadata.get("edited") == True
            print("✓ Message update successful!")
        else:
            print("✗ Failed to retrieve updated message")

        # Test 2: Delete a message
        print("\n--- Testing message delete ---")
        message_to_delete = messages[2]

        print(f"Deleting message {message_to_delete.id}")
        success = storage.delete_message(message_to_delete.id)
        print(f"Delete success: {success}")

        # Verify the deletion
        deleted_msg = storage.get_message(message_to_delete.id)
        if deleted_msg is None:
            print("✓ Message deleted successfully!")
        else:
            print("✗ Message still exists after deletion")

        # Test 3: Delete message range
        print("\n--- Testing message range delete ---")

        # Add more messages for range deletion test
        for i in range(3, 6):
            msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i+1}",
                created_at=datetime.now(),
            )
            storage.add_message(msg)
            print(f"Added message {i+1} for range test")

        # Get all messages to see current state
        all_messages = storage.get_messages(session.id)
        print(f"\nTotal messages before range delete: {len(all_messages)}")

        # Delete messages at index 1-2 (0-based)
        print("Deleting messages at index 1-2")
        success = storage.delete_messages_range(session.id, 1, 2)
        print(f"Range delete success: {success}")

        # Verify range deletion
        remaining_messages = storage.get_messages(session.id)
        print(f"Total messages after range delete: {len(remaining_messages)}")
        print(
            "✓ Message range delete successful!" if success else "✗ Range delete failed"
        )

        # Print final state
        print("\n--- Final message list ---")
        for idx, msg in enumerate(remaining_messages):
            print(f"{idx}: {msg.role}: {msg.content}")

        print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_chat_edit_delete()
