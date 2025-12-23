#!/usr/bin/env python3
"""
Test script to fetch actual API responses for player 1349
Saves pretty-printed JSON responses to .txt files
"""

import requests
import json
from datetime import datetime
import os

BASE_URL = "https://smartline-production.up.railway.app"
PLAYER_ID = 1349
SEASON = 2023

OUTPUT_DIR = "api_test_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_filename(name: str) -> str:
    """Convert endpoint name to filesystem-safe filename"""
    return (
        name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )


def test_endpoint(name, url):
    """Test an endpoint and save the response to a txt file"""
    print(f"Testing: {name}")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{safe_filename(name)}_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        response = requests.get(url, timeout=30)
        status_code = response.status_code

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"ENDPOINT: {name}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Status Code: {status_code}\n")
            f.write(f"Timestamp (UTC): {timestamp}\n")
            f.write("\n" + "=" * 80 + "\n\n")

            if status_code == 200:
                data = response.json()
                f.write("JSON Response:\n")
                f.write(json.dumps(data, indent=2, default=str))
            else:
                f.write("Error Response:\n")
                f.write(response.text)

        print(f"  → Saved to {filepath}")

    except Exception as e:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"ENDPOINT: {name}\n")
            f.write(f"URL: {url}\n")
            f.write("Exception occurred:\n")
            f.write(str(e))

        print(f"  → Exception saved to {filepath}")


# =========================================================
# Test all relevant endpoints
# =========================================================

print("TESTING API ENDPOINTS FOR PLAYER 1349")
print("=" * 80)

# 1. Player Details
test_endpoint(
    "Player Details",
    f"{BASE_URL}/players/{PLAYER_ID}"
)

# 2. Player Game Log (Passing only)
test_endpoint(
    "Player Game Log (Passing)",
    f"{BASE_URL}/statistics/players/{PLAYER_ID}/games"
    f"?season={SEASON}&stat_group=Passing&limit=10"
)

# 3. Player Game Log (All stat groups)
test_endpoint(
    "Player Game Log (All Groups)",
    f"{BASE_URL}/statistics/players/{PLAYER_ID}/games"
    f"?season={SEASON}&limit=10"
)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
