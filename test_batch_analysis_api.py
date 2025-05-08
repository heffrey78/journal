#!/usr/bin/env python3
"""
Test script for the batch analysis API endpoints.

This script tests the functionality of the batch analysis API routes:
- POST /batch/analyze
- GET /batch/analyses
- GET /batch/analyses/{batch_id}
- DELETE /batch/analyses/{batch_id}
- GET /entries/{entry_id}/batch-analyses

Run this script after starting the API server to verify that the batch analysis
endpoints are working correctly.
"""
import requests

BASE_URL = "http://localhost:8000"


def test_batch_analysis_api():
    """Test the batch analysis API endpoints."""
    print("Testing Batch Analysis API Endpoints...")

    # Test 1: Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/info")
        if response.status_code == 200:
            print(f"API Status: {response.status_code} - {response.json()['name']}")
        else:
            print(f"API Status: {response.status_code} - Unable to connect")
            print("Make sure the API server is running.")
            return
    except Exception as e:
        print(f"Error connecting to API: {e}")
        print("Make sure the API server is running.")
        return

    # Test 2: Get available entries for batch analysis
    print("\n--- Getting entries for batch analysis ---")
    entry_ids = []
    try:
        response = requests.get(f"{BASE_URL}/entries/?limit=3")
        if response.status_code == 200:
            entries = response.json()
            if len(entries) < 2:
                print(
                    "Error: Need at least 2 entries in the database for batch analysis."
                )
                return

            print(f"Found {len(entries)} entries to use for testing:")
            for idx, entry in enumerate(entries, 1):
                print(f"{idx}. {entry['title']} ({entry['id']})")
                entry_ids.append(entry["id"])
        else:
            print(f"Failed to get entries: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Error getting entries: {e}")
        return

    # Test 3: Create batch analysis
    print("\n--- Creating batch analysis ---")
    batch_request = {
        "entry_ids": entry_ids,
        "title": "Test Batch Analysis",
        "prompt_type": "weekly",
    }

    batch_id = None
    try:
        print("Sending request to analyze entries...")
        print(f"Number of entries: {len(entry_ids)}")
        print(f"Prompt type: {batch_request['prompt_type']}")

        response = requests.post(f"{BASE_URL}/batch/analyze", json=batch_request)

        if response.status_code == 200:
            batch_analysis = response.json()
            batch_id = batch_analysis["id"]
            print(f"Created batch analysis with ID: {batch_id}")
            print(f"Title: {batch_analysis['title']}")
            print(f"Date range: {batch_analysis['date_range']}")
            print(f"Summary (excerpt): {batch_analysis['summary'][:80]}...")
            print(f"Key themes: {', '.join(batch_analysis['key_themes'])}")
            print(f"Number of insights: {len(batch_analysis['notable_insights'])}")
        else:
            print(
                f"Failed to create batch analysis: "
                f"{response.status_code} - {response.text}"
            )
            # Continue with other tests even if this fails
    except Exception as e:
        print(f"Error creating batch analysis: {e}")
        # Continue with other tests even if this fails

    # Test 4: List all batch analyses
    print("\n--- Listing batch analyses ---")
    try:
        response = requests.get(f"{BASE_URL}/batch/analyses")
        if response.status_code == 200:
            analyses = response.json()
            print(f"Found {len(analyses)} batch analyses")
            for idx, analysis in enumerate(analyses[:3], 1):  # Show top 3
                print(
                    f"{idx}. {analysis['title']} (ID: {analysis['id']}, "
                    f"Prompt: {analysis['prompt_type']})"
                )
            if len(analyses) > 3:
                print(f"...and {len(analyses) - 3} more")

            # If we didn't create a batch analysis earlier, use the first one
            if not batch_id and analyses:
                batch_id = analyses[0]["id"]
                print(
                    f"Using existing batch analysis with ID: "
                    f"{batch_id} for further tests"
                )
        else:
            print(
                f"Failed to list batch analyses: "
                f"{response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"Error listing batch analyses: {e}")

    # Test 5: Get specific batch analysis by ID
    if batch_id:
        print("\n--- Getting batch analysis by ID ---")
        try:
            response = requests.get(f"{BASE_URL}/batch/analyses/{batch_id}")
            if response.status_code == 200:
                analysis = response.json()
                print(f"Retrieved batch analysis: {analysis['title']}")
                print(f"Number of entries: {len(analysis['entry_ids'])}")
                print(f"Date range: {analysis['date_range']}")
                print(f"Summary (excerpt): {analysis['summary'][:80]}...")
            else:
                print(
                    f"Failed to get batch analysis: "
                    f"{response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"Error getting batch analysis: {e}")

        # Test 6: Get batch analyses for a specific entry
        if entry_ids:
            print("\n--- Getting batch analyses for specific entry ---")
            test_entry_id = entry_ids[0]
            try:
                response = requests.get(
                    f"{BASE_URL}/entries/{test_entry_id}/batch-analyses"
                )
                if response.status_code == 200:
                    entry_analyses = response.json()
                    print(
                        f"Found {len(entry_analyses)} batch analyses for entry "
                        f"{test_entry_id}"
                    )
                    for idx, analysis in enumerate(entry_analyses[:3], 1):
                        print(f"{idx}. {analysis['title']} (ID: {analysis['id']})")
                else:
                    print(
                        f"Failed to get entry batch analyses: "
                        f"{response.status_code} - {response.text}"
                    )
            except Exception as e:
                print(f"Error getting entry batch analyses: {e}")

        # Test 7: Delete batch analysis
        print("\n--- Deleting batch analysis ---")
        try:
            response = requests.delete(f"{BASE_URL}/batch/analyses/{batch_id}")
            if response.status_code == 200:
                print(f"Successfully deleted batch analysis {batch_id}")

                # Verify deletion by trying to get it again
                verify_response = requests.get(f"{BASE_URL}/batch/analyses/{batch_id}")
                if verify_response.status_code == 404:
                    print(
                        "Verified: Batch analysis was properly deleted (404 Not Found)"
                    )
                else:
                    print(
                        f"Warning: Unexpected response after deletion: "
                        f"{verify_response.status_code}"
                    )
            else:
                print(
                    f"Failed to delete batch analysis: "
                    f"{response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"Error deleting batch analysis: {e}")

    print("\nBatch Analysis API testing complete!")


if __name__ == "__main__":
    test_batch_analysis_api()
