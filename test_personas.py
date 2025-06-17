#!/usr/bin/env python3
"""
Test script for the personas functionality.
This tests the data model, storage layer, and API endpoints.
"""

import pytest
import tempfile
import shutil
import os
from datetime import datetime

from app.models import Persona, PersonaCreate, PersonaUpdate, ChatSession
from app.storage.personas import PersonaStorage
from app.storage.chat import ChatStorage


def test_persona_models():
    """Test Persona model validation."""
    print("Testing Persona models...")

    # Test PersonaCreate
    create_data = PersonaCreate(
        name="Test Persona",
        description="A test persona for validation",
        system_prompt="You are a test assistant.",
        icon="🧪",
    )
    assert create_data.name == "Test Persona"
    assert create_data.icon == "🧪"

    # Test Persona model
    persona = Persona(
        name="Test Persona",
        description="A test persona",
        system_prompt="You are a test assistant.",
        icon="🧪",
    )
    assert persona.is_default == False
    assert persona.icon == "🧪"
    assert persona.id.startswith("persona-")

    print("✓ Persona models validation passed")


def test_persona_storage():
    """Test PersonaStorage functionality."""
    print("Testing PersonaStorage...")

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize storage
        storage = PersonaStorage(base_dir=temp_dir)

        # Test default personas seeded
        personas = storage.list_personas()
        assert len(personas) == 5  # Should have 5 default personas

        default_persona = storage.get_default_persona()
        assert default_persona is not None
        assert default_persona.name == "Journaling Assistant"
        assert default_persona.is_default == True

        # Test creating custom persona
        create_data = PersonaCreate(
            name="Custom Test Persona",
            description="A custom test persona",
            system_prompt="You are a custom test assistant.",
            icon="🚀",
        )

        created_persona = storage.create_persona(create_data)
        assert created_persona.name == "Custom Test Persona"
        assert created_persona.is_default == False
        assert created_persona.icon == "🚀"

        # Test retrieving persona
        retrieved = storage.get_persona(created_persona.id)
        assert retrieved is not None
        assert retrieved.name == "Custom Test Persona"

        # Test listing personas (should now be 6)
        all_personas = storage.list_personas()
        assert len(all_personas) == 6

        # Test updating persona
        update_data = PersonaUpdate(
            name="Updated Test Persona", description="An updated test persona"
        )

        updated = storage.update_persona(created_persona.id, update_data)
        assert updated is not None
        assert updated.name == "Updated Test Persona"
        assert updated.system_prompt == "You are a custom test assistant."  # Unchanged

        # Test deleting persona
        success = storage.delete_persona(created_persona.id)
        assert success == True

        # Verify deletion
        deleted = storage.get_persona(created_persona.id)
        assert deleted is None

        # Should be back to 5 personas
        final_personas = storage.list_personas()
        assert len(final_personas) == 5

        print("✓ PersonaStorage functionality passed")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_chat_session_with_persona():
    """Test ChatSession with persona_id functionality."""
    print("Testing ChatSession with persona integration...")

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize storage
        persona_storage = PersonaStorage(base_dir=temp_dir)
        chat_storage = ChatStorage(base_dir=temp_dir)

        # Get default persona
        default_persona = persona_storage.get_default_persona()
        assert default_persona is not None

        # Create chat session with persona
        session = ChatSession(
            title="Test Chat with Persona", persona_id=default_persona.id
        )

        # Save session
        saved_session = chat_storage.create_session(session)
        assert saved_session.persona_id == default_persona.id

        # Retrieve session
        retrieved_session = chat_storage.get_session(saved_session.id)
        assert retrieved_session is not None
        assert retrieved_session.persona_id == default_persona.id

        print("✓ ChatSession persona integration passed")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_api_endpoints():
    """Test API endpoints with a mock FastAPI test client."""
    print("Testing API endpoints...")

    from fastapi.testclient import TestClient
    from app.api import app

    # Create test client
    client = TestClient(app)

    # Test list personas
    response = client.get("/api/personas")
    assert response.status_code == 200
    personas = response.json()
    assert isinstance(personas, list)
    assert len(personas) >= 5  # Should have default personas

    # Test get default persona
    response = client.get("/api/personas/default")
    assert response.status_code == 200
    default_persona = response.json()
    assert default_persona["name"] == "Journaling Assistant"

    # Test create persona
    create_data = {
        "name": "API Test Persona",
        "description": "A test persona via API",
        "system_prompt": "You are an API test assistant.",
        "icon": "🔧",
    }

    response = client.post("/api/personas", json=create_data)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "API Test Persona"
    persona_id = created["id"]

    # Test get specific persona
    response = client.get(f"/api/personas/{persona_id}")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["name"] == "API Test Persona"

    # Test update persona
    update_data = {"name": "Updated API Test Persona"}

    response = client.put(f"/api/personas/{persona_id}", json=update_data)
    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Updated API Test Persona"

    # Test delete persona
    response = client.delete(f"/api/personas/{persona_id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/personas/{persona_id}")
    assert response.status_code == 404

    print("✓ API endpoints testing passed")


if __name__ == "__main__":
    print("Running Personas functionality tests...")
    print("=" * 50)

    try:
        test_persona_models()
        test_persona_storage()
        test_chat_session_with_persona()
        test_api_endpoints()

        print("=" * 50)
        print("🎉 All tests passed! Personas functionality is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
