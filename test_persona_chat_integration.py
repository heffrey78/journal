#!/usr/bin/env python3
"""
Test script for persona chat integration.
This tests that chat sessions use persona system prompts correctly.
"""

import tempfile
import shutil
from app.models import ChatSession, ChatMessage, ChatConfig
from app.storage.chat import ChatStorage
from app.storage.personas import PersonaStorage
from app.chat_service import ChatService
from app.llm_service import LLMService


def test_persona_system_prompt_integration():
    """Test that chat service uses persona system prompts."""
    print("Testing persona system prompt integration...")

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize storage
        persona_storage = PersonaStorage(base_dir=temp_dir)
        chat_storage = ChatStorage(base_dir=temp_dir)

        # Get default persona
        default_persona = persona_storage.get_default_persona()
        assert default_persona is not None
        assert default_persona.name == "Journaling Assistant"

        # Create chat session with persona
        session = ChatSession(
            title="Test Chat with Persona", persona_id=default_persona.id
        )

        # Save session
        saved_session = chat_storage.create_session(session)

        # Create a mock LLM service (we don't need actual LLM calls for this test)
        class MockLLMService:
            def __init__(self):
                pass

            def get_config(self):
                return ChatConfig()  # Default config

        # Initialize chat service
        llm_service = MockLLMService()
        chat_service = ChatService(chat_storage, llm_service)

        # Get chat config
        config = chat_storage.get_chat_config()

        # Test conversation history preparation
        conversation = chat_service._prepare_conversation_history(
            saved_session.id, config
        )

        # Verify that the conversation starts with the persona's system prompt
        assert len(conversation) > 0
        assert conversation[0]["role"] == "system"
        assert conversation[0]["content"] == default_persona.system_prompt
        assert "journaling assistant" in conversation[0]["content"].lower()

        # Test with session without persona
        session_no_persona = ChatSession(title="Test Chat without Persona")
        saved_session_no_persona = chat_storage.create_session(session_no_persona)

        conversation_no_persona = chat_service._prepare_conversation_history(
            saved_session_no_persona.id, config
        )

        # Should use default system prompt
        assert len(conversation_no_persona) > 0
        assert conversation_no_persona[0]["role"] == "system"
        assert conversation_no_persona[0]["content"] == config.system_prompt

        print("✓ Persona system prompt integration working correctly")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_persona_fallback_behavior():
    """Test fallback behavior when persona is not found."""
    print("Testing persona fallback behavior...")

    temp_dir = tempfile.mkdtemp()

    try:
        chat_storage = ChatStorage(base_dir=temp_dir)
        persona_storage = PersonaStorage(base_dir=temp_dir)

        # Create session with non-existent persona ID
        session = ChatSession(
            title="Test Chat with Invalid Persona", persona_id="invalid-persona-id"
        )
        saved_session = chat_storage.create_session(session)

        class MockLLMService:
            def get_config(self):
                return ChatConfig()

        llm_service = MockLLMService()
        chat_service = ChatService(chat_storage, llm_service)
        config = chat_storage.get_chat_config()

        # Should fallback to default system prompt
        conversation = chat_service._prepare_conversation_history(
            saved_session.id, config
        )

        assert len(conversation) > 0
        assert conversation[0]["role"] == "system"
        assert conversation[0]["content"] == config.system_prompt

        print("✓ Persona fallback behavior working correctly")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Running Persona Chat Integration tests...")
    print("=" * 50)

    try:
        test_persona_system_prompt_integration()
        test_persona_fallback_behavior()

        print("=" * 50)
        print("🎉 All persona chat integration tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
