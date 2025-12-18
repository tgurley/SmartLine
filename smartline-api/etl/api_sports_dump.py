import requests
import json
from datetime import datetime

# ======================================
# CONFIG
# ======================================
API_KEY = "c94fa8aca52ceedd3ba87af778c66132"  # <-- your real key here
BASE_URL = "https://v1.american-football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

# Start with leagues endpoint (no filters)
ENDPOINT = "/leagues"

# ======================================
# REQUEST
# ======================================
print("🚀 Sending request to API-Sports...")

response = requests.get(
    BASE_URL + ENDPOINT,
    headers=HEADERS,
    timeout=30
)

response.raise_for_status()
data = response.json()

# ======================================
# WRITE RAW PAYLOAD
# ======================================
timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
outfile = f"api_sports_raw_{timestamp}.txt"

with open(outfile, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"✅ Raw payload written to: {outfile}")
print(f"Top-level keys: {list(data.keys())}")
print(f"Results count: {data.get('results')}")
