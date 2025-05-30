import requests
import json

API_URL = "https://qkdvetofbsoynkfprlos.supabase.co/rest/v1/rpc/filter_builds_advanced"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZHZldG9mYnNveW5rZnBybG9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3Mjc0NDEsImV4cCI6MjA2MTMwMzQ0MX0.Moy2MzlEQ0w1cqvnMs3qAV6Mzdm8R1v_YSo7Zw93mG8"

HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/x-www-form-urlencoded",
}

LIMIT = 1000

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

if __name__ == "__main__":
    builds = fetch_all_builds()
    with open("builds.json", "w", encoding="utf-8") as f:
        json.dump(builds, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(builds)} builds to builds.json")
