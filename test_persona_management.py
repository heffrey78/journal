#!/usr/bin/env python3
"""
Test script for persona management functionality.
This tests the full CRUD operations for personas via API.
"""

from fastapi.testclient import TestClient
from app.api import app
import tempfile
import shutil


def test_persona_management_api():
    """Test persona management API endpoints."""
    print("Testing persona management API...")

    # Create test client
    client = TestClient(app)

    # Test list personas (should have 5 defaults)
    response = client.get("/api/personas")
    assert response.status_code == 200
    personas = response.json()
    assert isinstance(personas, list)
    assert len(personas) >= 5  # Should have default personas

    default_personas = [p for p in personas if p["is_default"]]
    custom_personas = [p for p in personas if not p["is_default"]]
    assert len(default_personas) == 5

    print(
        f"✓ Found {len(default_personas)} default personas and {len(custom_personas)} custom personas"
    )

    # Test get default persona
    response = client.get("/api/personas/default")
    assert response.status_code == 200
    default_persona = response.json()
    assert default_persona["name"] == "Journaling Assistant"
    assert default_persona["is_default"] == True

    print("✓ Default persona retrieval working")

    # Test create custom persona
    new_persona_data = {
        "name": "Test Persona",
        "description": "A test persona for validation",
        "system_prompt": "You are a test assistant designed to validate the persona management system.",
        "icon": "🧪",
    }

    response = client.post("/api/personas", json=new_persona_data)
    assert response.status_code == 201
    created_persona = response.json()
    assert created_persona["name"] == "Test Persona"
    assert created_persona["is_default"] == False
    assert created_persona["icon"] == "🧪"

    persona_id = created_persona["id"]
    print(f"✓ Created custom persona with ID: {persona_id}")

    # Test get specific persona
    response = client.get(f"/api/personas/{persona_id}")
    assert response.status_code == 200
    retrieved_persona = response.json()
    assert retrieved_persona["name"] == "Test Persona"
    assert retrieved_persona["id"] == persona_id

    print("✓ Persona retrieval by ID working")

    # Test update persona
    update_data = {
        "name": "Updated Test Persona",
        "description": "An updated test persona",
    }

    response = client.put(f"/api/personas/{persona_id}", json=update_data)
    assert response.status_code == 200
    updated_persona = response.json()
    assert updated_persona["name"] == "Updated Test Persona"
    assert updated_persona["description"] == "An updated test persona"
    assert (
        updated_persona["system_prompt"] == new_persona_data["system_prompt"]
    )  # Should remain unchanged

    print("✓ Persona update working")

    # Test that we can't update default personas
    default_persona_id = default_persona["id"]
    response = client.put(
        f"/api/personas/{default_persona_id}", json={"name": "Modified Default"}
    )
    assert response.status_code == 403  # Forbidden

    print("✓ Default persona protection working")

    # Test delete persona
    response = client.delete(f"/api/personas/{persona_id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/personas/{persona_id}")
    assert response.status_code == 404

    print("✓ Persona deletion working")

    # Test that we can't delete default personas
    response = client.delete(f"/api/personas/{default_persona_id}")
    assert response.status_code == 403  # Forbidden

    print("✓ Default persona deletion protection working")

    # Test validation - missing required fields
    invalid_persona_data = {
        "name": "",  # Empty name should fail validation
        "description": "Test",
        "system_prompt": "Test",
    }

    response = client.post("/api/personas", json=invalid_persona_data)
    assert response.status_code == 422  # Validation error

    print("✓ Input validation working")


def test_persona_default_content():
    """Test that default personas have good content."""
    print("Testing default persona content...")

    client = TestClient(app)

    # Get all personas
    response = client.get("/api/personas")
    assert response.status_code == 200
    personas = response.json()

    default_personas = [p for p in personas if p["is_default"]]

    # Expected default personas
    expected_personas = {
        "Journaling Assistant": "📖",
        "Coach": "🎯",
        "Story Teller": "📚",
        "Therapist": "💙",
        "Productivity Partner": "⚡",
    }

    found_personas = {}
    for persona in default_personas:
        found_personas[persona["name"]] = persona["icon"]

        # Verify each persona has substantial content
        assert len(persona["name"]) > 0
        assert len(persona["description"]) > 10
        assert len(persona["system_prompt"]) > 50
        assert len(persona["icon"]) > 0

        print(
            f"✓ {persona['name']} - {persona['icon']} - {len(persona['system_prompt'])} chars"
        )

    # Verify all expected personas exist
    for name, icon in expected_personas.items():
        assert name in found_personas, f"Missing expected persona: {name}"
        assert (
            found_personas[name] == icon
        ), f"Wrong icon for {name}: expected {icon}, got {found_personas[name]}"

    print("✓ All default personas have appropriate content")


if __name__ == "__main__":
    print("Running Persona Management tests...")
    print("=" * 50)

    try:
        test_persona_management_api()
        test_persona_default_content()

        print("=" * 50)
        print("🎉 All persona management tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
