import json
import requests
import os
import time
from pathlib import Path
from datetime import datetime

# --- Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_JSON_FILE = SCRIPT_DIR.parent / "builds.json"
# The base URL template for fetching round data
BASE_URL = 'https://qkdvetofbsoynkfprlos.supabase.co/rest/v1/rounds?select=*,round_upgrades(id,upgrade_id,action,notes)&build_id=eq.{build_id}&order=round_number.asc'
OUTPUT_DIRECTORY = SCRIPT_DIR / 'build_rounds_data'  # Directory to save the output JSON files
# Headers for the request (Supabase requires an API key)
# IMPORTANT: Replace 'YOUR_SUPABASE_ANON_KEY' with your actual Supabase anonymous API key.
# You can usually find this in your Supabase project settings under API.
# THIS IS A PUBLIC KEY - IT IS USED BY ALL VIEWERS
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8', # Replace with your actual anon key
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8' # Replace with your actual anon key
}
REQUEST_DELAY_SECONDS = 0.1  # Delay between requests to avoid overwhelming the server (adjust as needed)


def load_build_index(filepath):
    """Load build metadata from the index file.

    Returns a list of dictionaries with at least 'id' and 'updated_at' keys.
    """

    try:
        with open(filepath, "r") as f:
            builds_data = json.load(f)
        builds = []
        for item in builds_data:
            if "id" not in item:
                continue
            builds.append({
                "id": item["id"],
                "updated_at": item.get("updated_at"),
            })
        if not builds:
            print(
                f"Warning: No build entries found in '{filepath}'. Ensure the file contains objects with 'id' keys."
            )
        return builds
    except FileNotFoundError:
        print(f"Error: Input file '{filepath}' not found.")
        return []
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from '{filepath}'. Please ensure it's a valid JSON file."
        )
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading build metadata: {e}")
        return []

def fetch_round_data(build_id):
    """Fetches round data for a given build ID from the Supabase endpoint."""
    if not HEADERS['apikey'] or 'YOUR_SUPABASE_ANON_KEY' in HEADERS['apikey']:
        print("Error: Supabase API key is not set or is still the placeholder. Please update the HEADERS.")
        return None

    url = BASE_URL.format(build_id=build_id)
    print(f"Fetching data for build ID: {build_id} from {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for build ID {build_id}: {http_err} - Response: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred for build ID {build_id}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred for build ID {build_id}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during the request for build ID {build_id}: {req_err}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response for build ID {build_id}. Response: {response.text}")
    return None

def save_data_to_json(data, updated_at, filename, directory):
    """Save round data along with its update timestamp to a JSON file."""

    directory = Path(directory)
    if not directory.exists():
        try:
            directory.mkdir(parents=True)
            print(f"Created directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            return

    filepath = directory / filename
    if filepath.exists():
        try:
            filepath.unlink()
        except OSError as e:
            print(f"Error deleting existing file '{filepath}': {e}")

    wrapped_data = {"updated_at": updated_at, "rounds": data}
    try:
        with filepath.open("w") as f:
            json.dump(wrapped_data, f, indent=4)
        print(f"Successfully saved data to '{filepath}'")
    except IOError as e:
        print(f"Error writing to file '{filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving data: {e}")

def main():
    """Main function to orchestrate the data fetching and saving process."""
    print("Starting the data fetching script...")

    # --- IMPORTANT SECURITY NOTE ---
    # Ensure your Supabase API key has the appropriate (minimal) permissions.
    # For read-only operations like this, an 'anon' key is usually sufficient,
    # but double-check your table's Row Level Security (RLS) policies in Supabase.
    if 'YOUR_SUPABASE_ANON_KEY' in HEADERS['apikey']:
        print("\n" + "="*50)
        print("IMPORTANT: Please replace 'YOUR_SUPABASE_ANON_KEY' in the script's")
        print("HEADERS with your actual Supabase anonymous API key.")
        print("You can find this in your Supabase project settings under API > Project API keys.")
        print("The script will not work correctly without a valid API key.")
        print("="*50 + "\n")
        # You might want to exit here if the key is not set, or proceed cautiously.
        # For this example, we'll proceed but print a prominent warning.

    builds = load_build_index(INPUT_JSON_FILE)
    if not builds:
        print("No builds to process. Exiting.")
        return

    print(f"Found {len(builds)} builds in index. Checking for updates...")

    for i, build in enumerate(builds):
        build_id = build["id"]
        index_updated_at = build.get("updated_at")
        filepath = Path(OUTPUT_DIRECTORY) / f"{build_id}.json"

        needs_update = False

        if filepath.exists():
            try:
                with filepath.open("r") as f:
                    existing_data = json.load(f)
                file_updated_at = None
                if isinstance(existing_data, dict):
                    file_updated_at = existing_data.get("updated_at")

                if index_updated_at and file_updated_at:
                    try:
                        needs_update = datetime.fromisoformat(index_updated_at) > datetime.fromisoformat(file_updated_at)
                    except ValueError:
                        needs_update = True
                else:
                    needs_update = True
            except Exception as e:
                print(f"Error reading existing build {build_id}: {e}. Will refetch.")
                needs_update = True
        else:
            needs_update = True

        if not needs_update:
            print(f"Build {build_id} is up to date. Skipping.")
            continue

        print(f"\nProcessing build {i+1}/{len(builds)}: ID {build_id}")
        round_data = fetch_round_data(build_id)
        if round_data is not None:
            output_filename = f"{build_id}.json"
            save_data_to_json(round_data, index_updated_at, output_filename, OUTPUT_DIRECTORY)
        else:
            print(f"Skipping save for build ID {build_id} due to fetch error.")

        if i < len(builds) - 1:
            print(f"Waiting for {REQUEST_DELAY_SECONDS} seconds before next request...")
            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nScript finished.")

if __name__ == "__main__":
    main()

