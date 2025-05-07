#!/usr/bin/env python3
"""
Debug script to test Ollama API directly
"""
import ollama


def test_ollama_list():
    """Test the ollama.list() function directly"""
    try:
        print("Calling ollama.list()...")
        response = ollama.list()

        print("\nResponse type:", type(response))
        print("\nResponse structure:")

        # Check if the object has the expected attribute
        if hasattr(response, "models"):
            print(f"Found 'models' attribute with {len(response.models)} models")

            # Extract model names directly
            model_names = []
            for model in response.models:
                model_name = getattr(model, "name", None)
                if model_name:
                    model_names.append(model_name)
                print(f"- {model_name}")

            print(f"\nExtracted {len(model_names)} model names")

        # Try accessing as dictionary
        try:
            if isinstance(response, dict) and "models" in response:
                print("\nAccessing as dictionary:")
                for model in response["models"]:
                    print(f"- {model.get('name', 'N/A')}")
        except (TypeError, KeyError) as e:
            print(f"Error accessing as dictionary: {e}")

    except Exception as e:
        print(f"Error during ollama.list(): {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("== Ollama List Debug ==")
    test_ollama_list()
