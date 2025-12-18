import os
import requests
import json
from datetime import datetime

API_KEY = os.getenv("API_SPORTS_KEY")
if not API_KEY:
    raise RuntimeError("API_SPORTS_KEY environment variable is not set")

BASE_URL = "https://v1.american-football.api-sports.io"
GAMES_ENDPOINT = "/games"

HEADERS = {
    "x-apisports-key": API_KEY
}

NFL_LEAGUE_ID = 1
SEASON_YEAR = 2023

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
output_file = f"api_sports_nfl_{SEASON_YEAR}_games_raw_{timestamp}.txt"

print("🚀 Fetching NFL 2023 games payload from API-Sports...")

resp = requests.get(
    BASE_URL + GAMES_ENDPOINT,
    headers=HEADERS,
    params={
        "league": NFL_LEAGUE_ID,
        "season": SEASON_YEAR
    },
    timeout=30
)

resp.raise_for_status()
payload = resp.json()

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print(f"✅ Payload written to {output_file}")
print("Top-level keys:", payload.keys())
print("Results count:", payload.get("results"))
