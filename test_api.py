import requests

BASE_URL = "http://localhost:8000"


def test_api():
    print("Testing Journal API...")

    # Test 1: Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"API Status: {response.status_code}")
        print(f"API Info: {response.json()}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return

    # Test 2: Create a new entry
    print("\n--- Creating a new entry ---")
    new_entry = {
        "title": "Test Entry from Client",
        "content": "# Test Entry\n\nThis entry was created by the test client script.",
        "tags": ["test", "api"],
    }

    try:
        response = requests.post(f"{BASE_URL}/entries/", json=new_entry)
        if response.status_code == 200:
            created_entry = response.json()
            print(f"Created entry with ID: {created_entry['id']}")
            entry_id = created_entry["id"]
        else:
            print(f"Failed to create entry: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Error creating entry: {e}")
        return

    # Test 3: Get the newly created entry
    print("\n--- Getting entry by ID ---")
    try:
        response = requests.get(f"{BASE_URL}/entries/{entry_id}")
        if response.status_code == 200:
            entry = response.json()
            print(f"Retrieved entry: {entry['title']}")
            print(f"Content: {entry['content'][:50]}...")
        else:
            print(f"Failed to get entry: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting entry: {e}")

    # Test 4: List all entries
    print("\n--- Listing entries ---")
    try:
        response = requests.get(f"{BASE_URL}/entries/")
        if response.status_code == 200:
            entries = response.json()
            print(f"Found {len(entries)} entries")
            for idx, entry in enumerate(entries[:3], 1):  # Show top 3
                print(f"{idx}. {entry['title']} ({entry['id']})")
            if len(entries) > 3:
                print(f"...and {len(entries) - 3} more")
        else:
            print(f"Failed to list entries: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error listing entries: {e}")

    # Test 5: Search for entries
    print("\n--- Searching entries ---")
    search_term = "test"
    try:
        response = requests.get(f"{BASE_URL}/entries/search/?query={search_term}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results for '{search_term}'")
            for idx, entry in enumerate(results[:3], 1):  # Show top 3
                print(f"{idx}. {entry['title']} ({entry['id']})")
            if len(results) > 3:
                print(f"...and {len(results) - 3} more")
        else:
            print(f"Failed to search: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error searching: {e}")

    print("\nAPI testing complete!")


if __name__ == "__main__":
    test_api()
