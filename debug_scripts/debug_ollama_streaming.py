#!/usr/bin/env python3
"""
Debug script to test the raw Ollama streaming response format.
This helps understand the exact structure of the chunks
so we can properly handle them in our streaming implementation.
"""

import json
import requests


def print_chunk(prefix, chunk, include_content=False):
    """Pretty print chunk information without overwhelming the console."""
    try:
        if isinstance(chunk, dict):
            keys = list(chunk.keys())
            print(f"{prefix} keys: {keys}")

            # Check for specific important fields
            if "model" in chunk:
                print(f"{prefix} model: {chunk['model']}")
            if "done" in chunk:
                print(f"{prefix} done: {chunk['done']}")
            if "message" in chunk:
                msg_keys = list(chunk["message"].keys())
                print(f"{prefix} message keys: {msg_keys}")
                if "content" in chunk["message"] and include_content:
                    print(f"{prefix} content: {chunk['message']['content']}")
                elif "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    print(f"{prefix} content: {content[:20]}...")
        else:
            print(f"{prefix} (not a dict): {chunk}")
    except Exception as e:
        print(f"Error printing chunk: {e}")
        print(f"Raw chunk: {chunk}")


def test_direct_streaming():
    """Test streaming by directly calling the Ollama API."""
    print("\n=== Testing direct Ollama API streaming ===\n")

    url = "http://localhost:11434/api/chat"
    data = {
        "model": "qwen2.5:3b",  # Use the same model as in the logs
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about the sky in 3-5 words."},
        ],
        "stream": True,
    }

    try:
        print("Starting direct API streaming request...")
        response = requests.post(url, json=data, stream=True)

        print("\nProcessing direct stream chunks:")
        for i, line in enumerate(response.iter_lines()):
            if line:
                # Decode the line to utf-8 string
                line_str = line.decode("utf-8")
                print(f"\n--- Line {i+1} ---")
                print(f"Raw line: {line_str}")

                # Parse as JSON
                chunk = json.loads(line_str)
                print_chunk("API", chunk, include_content=True)

                # Extract just the content to show how it should be done
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    print(f"API extracted content: '{content}'")

        print("\nDone processing direct stream")

    except Exception as e:
        print(f"Error in direct streaming: {e}")


if __name__ == "__main__":
    test_direct_streaming()
