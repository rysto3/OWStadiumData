import os
import json
import requests

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICTURES_DIR = os.path.join(BASE_DIR, 'images')
JSON_FILE = os.path.join(BASE_DIR, 'SBItems.json')

# Create the pictures/images directory if it doesn't exist
os.makedirs(PICTURES_DIR, exist_ok=True)

# Load the JSON file
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    items = json.load(f)

def get_filename_from_url(url):
    return url.split('/')[-1].split('?')[0]

downloaded, skipped = 0, 0

for item in items:
    url = item.get('portrait_url')
    if not url:
        skipped += 1
        continue
    filename = get_filename_from_url(url)
    filename = filename.lower()
    dest_path = os.path.join(PICTURES_DIR, filename)

    # Skip if file already exists
    if os.path.exists(dest_path):
        print(f"Already exists: {filename}")
        continue

    try:
        print(f"Downloading: {url}")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        with open(dest_path, 'wb') as img_file:
            img_file.write(resp.content)
        downloaded += 1
    except Exception as e:
        print(f"Failed to download {url}: {e}")

print(f"\nDone! Downloaded {downloaded} images. Skipped {skipped} items with no portrait_url.")
