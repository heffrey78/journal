import requests
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:8000"


def test_enhanced_api():
    print("Testing Enhanced Journal API Features...")

    # Test 1: Check API status
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"API Status: {response.status_code}")
        print(f"API Info: {response.json()}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return

    # Test 2: Create a new entry for testing
    print("\n--- Creating a new test entry ---")
    new_entry = {
        "title": "Enhanced API Test Entry",
        "content": "# Test Entry\n\nThis entry tests the enhanced API functionality.",
        "tags": ["test", "enhanced", "api"],
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

    # Test 3: Update the entry
    print("\n--- Updating entry ---")
    update_data = {
        "title": "Updated Test Entry",
        "tags": ["test", "enhanced", "api", "updated"],
    }

    try:
        response = requests.patch(f"{BASE_URL}/entries/{entry_id}", json=update_data)
        if response.status_code == 200:
            updated_entry = response.json()
            print(f"Updated entry: {updated_entry['title']}")
            print(f"New tags: {updated_entry['tags']}")
        else:
            print(f"Failed to update entry: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error updating entry: {e}")

    # Test 4: Get all tags
    print("\n--- Getting all tags ---")
    try:
        response = requests.get(f"{BASE_URL}/tags/")
        if response.status_code == 200:
            tags = response.json()
            print(f"Found {len(tags)} unique tags:")
            print(", ".join(tags[:10]) + ("..." if len(tags) > 10 else ""))
        else:
            print(f"Failed to get tags: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting tags: {e}")

    # Test 5: Filter entries by tag
    print("\n--- Getting entries by tag ---")
    tag = "updated"
    try:
        response = requests.get(f"{BASE_URL}/tags/{tag}/entries")
        if response.status_code == 200:
            tag_entries = response.json()
            print(f"Found {len(tag_entries)} entries with tag '{tag}'")
            for idx, entry in enumerate(tag_entries[:3], 1):
                print(f"{idx}. {entry['title']} ({entry['id']})")
        else:
            print(
                f"Failed to get entries by tag: "
                f"{response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"Error getting entries by tag: {e}")

    # Test 6: Advanced search with parameters
    print("\n--- Testing advanced search ---")
    search_params = {
        "query": "test",
        "date_from": (datetime.now() - timedelta(days=7)).isoformat(),
        "date_to": datetime.now().isoformat(),
        "tags": ["api"],
    }

    try:
        response = requests.post(f"{BASE_URL}/entries/search/", json=search_params)
        if response.status_code == 200:
            search_results = response.json()
            print(f"Found {len(search_results)} entries matching advanced search")
            for idx, entry in enumerate(search_results[:3], 1):
                print(f"{idx}. {entry['title']} ({entry['id']})")
        else:
            print(f"Failed to search: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error performing advanced search: {e}")

    # Test 7: Get statistics
    print("\n--- Getting journal statistics ---")
    try:
        response = requests.get(f"{BASE_URL}/stats/")
        if response.status_code == 200:
            stats = response.json()
            print("Journal Statistics:")
            print(f"- Total entries: {stats['total_entries']}")
            print(f"- Total unique tags: {stats['total_tags']}")
            print("- Most used tags:")
            for tag, count in stats["most_used_tags"]:
                print(f"  * {tag}: {count} entries")
        else:
            print(f"Failed to get stats: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting statistics: {e}")

    print("\nEnhanced API testing complete!")


def test_summarize_entry(entry_id: str):
    """Test the entry summarization endpoint"""
    print(f"Testing entry summarization for entry ID: {entry_id}")

    url = f"{BASE_URL}/entries/{entry_id}/summarize"
    response = requests.post(url)

    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        summary = response.json()
        print("\n=== ENTRY SUMMARY ===")
        print(f"Summary: {summary['summary']}")
        print("\nKey Topics:")
        for topic in summary["key_topics"]:
            print(f"- {topic}")
        print(f"\nMood: {summary['mood']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_custom_prompt_summary(entry_id: str):
    """Test the custom prompt summarization endpoint with different prompt types"""
    print(f"\nTesting custom prompt summaries for entry ID: {entry_id}")

    prompt_types = ["default", "detailed", "creative", "concise"]
    summaries = {}

    for prompt_type in prompt_types:
        print(f"\nGenerating {prompt_type} summary...")
        url = f"{BASE_URL}/entries/{entry_id}/summarize/custom"
        payload = {"prompt_type": prompt_type}

        try:
            response = requests.post(url, json=payload)
            print(f"Status code: {response.status_code}")

            if response.status_code == 200:
                summary = response.json()
                summaries[prompt_type] = summary

                print(f"=== {prompt_type.upper()} SUMMARY ===")
                print(f"Summary: {summary['summary'][:150]}...")
                print("\nKey Topics:")
                for topic in summary["key_topics"][:3]:
                    print(f"- {topic}")
                print(f"\nMood: {summary['mood']}")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Error testing {prompt_type} summary: {e}")

    return summaries


def test_favorite_summaries(entry_id: str, summaries: dict):
    """Test saving and retrieving favorite summaries"""
    print(f"\nTesting favorite summary functionality for entry ID: {entry_id}")

    if not summaries:
        print("No summaries available to test with")
        return False

    # Test saving favorite summaries
    print("\nSaving summaries as favorites...")
    saved_count = 0

    for prompt_type, summary in summaries.items():
        # Add prompt_type to summary
        summary["prompt_type"] = prompt_type

        url = f"{BASE_URL}/entries/{entry_id}/summaries/favorite"
        try:
            response = requests.post(url, json=summary)
            if response.status_code == 200:
                saved_count += 1
                print(f"✓ Saved {prompt_type} summary as favorite")
            else:
                print(
                    f"✗ Failed to save {prompt_type} summary: "
                    f"{response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"Error saving {prompt_type} summary: {e}")

    # Test retrieving favorite summaries
    print("\nRetrieving favorite summaries...")
    url = f"{BASE_URL}/entries/{entry_id}/summaries/favorite"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            favorites = response.json()
            print(f"Retrieved {len(favorites)} favorite summaries")

            # Display a sample of the favorites
            for i, fav in enumerate(favorites[:2], 1):
                print(f"\nFavorite #{i}:")
                print(f"Type: {fav.get('prompt_type', 'default')}")
                print(f"Summary: {fav['summary'][:100]}...")
                print(f"Topics: {', '.join(fav['key_topics'][:3])}")

            return len(favorites) > 0
        else:
            print(
                "Failed to retrieve favorites: "
                f"{response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"Error retrieving favorites: {e}")
        return False


def get_latest_entry() -> str:
    """Get the ID of the latest entry for testing"""
    url = f"{BASE_URL}/entries/"
    response = requests.get(url, params={"limit": 1})

    if response.status_code == 200:
        entries = response.json()
        if entries:
            return entries[0]["id"]
    return None


if __name__ == "__main__":
    print("=== Testing Journal API Enhanced Features ===\n")

    # Use entry ID from command line argument or get latest entry
    if len(sys.argv) > 1:
        entry_id = sys.argv[1]
        print(f"Using provided entry ID: {entry_id}")
    else:
        print("Getting latest entry ID...")
        entry_id = get_latest_entry()
        if not entry_id:
            print("No entries found to test with. Please create an entry first.")
            sys.exit(1)
        print(f"Using latest entry ID: {entry_id}")

    # Run tests for all enhanced features
    print("\n--- Testing Basic Summarization ---")
    test_summarize_entry(entry_id)

    print("\n--- Testing Custom Prompt Summarization ---")
    summaries = test_custom_prompt_summary(entry_id)

    print("\n--- Testing Favorite Summaries ---")
    test_favorite_summaries(entry_id, summaries)

    print("\nAll enhanced API tests completed!")
