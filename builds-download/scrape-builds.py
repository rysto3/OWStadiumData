import json
import requests
import os
import time

# --- Configuration ---
INPUT_JSON_FILE = 'builds.json'
# The base URL template for fetching round data
BASE_URL = 'https://qkdvetofbsoynkfprlos.supabase.co/rest/v1/rounds?select=*,round_upgrades(id,upgrade_id,action,notes)&build_id=eq.{build_id}&order=round_number.asc'
OUTPUT_DIRECTORY = 'build_rounds_data'  # Directory to save the output JSON files
# Headers for the request (Supabase requires an API key)
# IMPORTANT: Replace 'YOUR_SUPABASE_ANON_KEY' with your actual Supabase anonymous API key.
# You can usually find this in your Supabase project settings under API.
# THIS IS A PUBLIC KEY - IT IS USED BY ALL VIEWERS
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8', # Replace with your actual anon key
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8' # Replace with your actual anon key
}
REQUEST_DELAY_SECONDS = 0.1 # Delay between requests to avoid overwhelming the server (adjust as needed)

def load_build_ids(filepath):
    """Loads build IDs from the specified JSON file."""
    try:
        with open(filepath, 'r') as f:
            builds_data = json.load(f)
        # Assuming the JSON file is a list of dictionaries, each with an 'id' key
        build_ids = [item['id'] for item in builds_data if 'id' in item]
        if not build_ids:
            print(f"Warning: No build IDs found in '{filepath}'. Ensure the file has a list of objects with 'id' keys.")
        return build_ids
    except FileNotFoundError:
        print(f"Error: Input file '{filepath}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Please ensure it's a valid JSON file.")
        return []
    except KeyError:
        print(f"Error: One or more items in '{filepath}' are missing the 'id' key.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading build IDs: {e}")
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

def save_data_to_json(data, filename, directory):
    """Saves the given data to a JSON file in the specified directory."""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            return

    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
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

    build_ids = load_build_ids(INPUT_JSON_FILE)

    if not build_ids:
        print("No build IDs to process. Exiting.")
        return

    print(f"Found {len(build_ids)} build IDs to process.")

    for i, build_id in enumerate(build_ids):
        print(f"\nProcessing build {i+1}/{len(build_ids)}: ID {build_id}")
        round_data = fetch_round_data(build_id)
        if round_data is not None: # Check if data was successfully fetched
            output_filename = f"{build_id}.json"
            save_data_to_json(round_data, output_filename, OUTPUT_DIRECTORY)
        else:
            print(f"Skipping save for build ID {build_id} due to fetch error.")

        # Add a delay to be respectful to the API
        if i < len(build_ids) - 1: # Don't delay after the last item
            print(f"Waiting for {REQUEST_DELAY_SECONDS} seconds before next request...")
            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nScript finished.")

if __name__ == "__main__":
    main()

