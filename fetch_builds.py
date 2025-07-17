import requests
import json
import sqlite3
import os
from glob import glob
import brotli

API_URL = "https://qkdvetofbsoynkfprlos.supabase.co/rest/v1/rpc/filter_builds_advanced"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8"

HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/x-www-form-urlencoded",
}

LIMIT = 1000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROUND_DATA_DIR = os.path.join(BASE_DIR, "builds-download", "build_rounds_data")
DB_PATH = os.path.join(BASE_DIR, "builds.db")
# Brotli compression level (1=lowest, 11=highest)
COMPRESSION_LEVEL = 6

def fetch_all_builds():
    all_builds = []
    offset = 0

    while True:
        data = {
            "p_limit": LIMIT,
            "p_offset": offset,
        }
        resp = requests.post(API_URL, headers=HEADERS, data=data)
        resp.raise_for_status()
        page = resp.json()
        if not isinstance(page, list):
            raise Exception(f"API response not a list! Got: {page}")
        all_builds.extend(page)
        if len(page) < LIMIT:
            break
        offset += LIMIT

    return all_builds


def create_sqlite_database(builds, compression_level: int = COMPRESSION_LEVEL):
    """Create the SQLite database and save it compressed with Brotli."""
    temp_db = DB_PATH + ".tmp"
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()

    # Tables: one for the index, one for per-build round data
    cur.execute(
        "CREATE TABLE IF NOT EXISTS builds_index (id TEXT PRIMARY KEY, data TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS build_rounds (build_id TEXT PRIMARY KEY, data TEXT)"
    )
    conn.commit()

    # Insert index data
    rows = [(b.get("id"), json.dumps(b, ensure_ascii=False)) for b in builds]
    cur.executemany(
        "INSERT OR REPLACE INTO builds_index (id, data) VALUES (?, ?)", rows
    )

    # Insert round data from json files if available
    if os.path.isdir(ROUND_DATA_DIR):
        for path in glob(os.path.join(ROUND_DATA_DIR, "*.json")):
            build_id = os.path.splitext(os.path.basename(path))[0]
            with open(path, "r", encoding="utf-8") as f:
                round_data = json.load(f)
            cur.execute(
                "INSERT OR REPLACE INTO build_rounds (build_id, data) VALUES (?, ?)",
                (build_id, json.dumps(round_data, ensure_ascii=False)),
            )

    conn.commit()
    conn.close()

    # Compress the database using Brotli
    with open(temp_db, "rb") as f:
        db_bytes = f.read()
    compressed = brotli.compress(db_bytes, quality=compression_level)
    with open(DB_PATH, "wb") as f:
        f.write(compressed)
    os.remove(temp_db)

if __name__ == "__main__":
    builds = fetch_all_builds()
    with open("builds.json", "w", encoding="utf-8") as f:
        json.dump(builds, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(builds)} builds to builds.json")
    create_sqlite_database(builds)
    print(f"SQLite database updated at {DB_PATH}")
