import os
import requests
from etl.db import get_conn

API_KEY = os.getenv("API_SPORTS_KEY")
if not API_KEY:
    raise RuntimeError("API_SPORTS_KEY not set")

BASE_URL = "https://v1.american-football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

NFL_LEAGUE_ID = 1
SEASON_YEAR = 2023

DOME_STADIUMS = {
    "Allegiant Stadium",
    "AT&T Stadium",
    "Caesars Superdome",
    "Ford Field",
    "Lucas Oil Stadium",
    "Mercedes-Benz Stadium",
    "NRG Stadium",
    "State Farm Stadium",
    "SoFi Stadium",
    "U.S. Bank Stadium"
}


def load_venues():
    conn = get_conn()
    cur = conn.cursor()

    print("🚀 Fetching NFL teams for venue extraction...")

    resp = requests.get(
        f"{BASE_URL}/teams",
        headers=HEADERS,
        params={"league": NFL_LEAGUE_ID, "season": SEASON_YEAR},
        timeout=30
    )
    resp.raise_for_status()

    payload = resp.json()
    teams = payload.get("response", [])

    print(f"📦 API returned {len(teams)} teams")

    venues_seen = set()
    inserted = 0

    for t in teams:
        stadium = t.get("stadium")
        city = t.get("city")

        # Skip AFC / NFC pseudo-teams
        if not stadium or stadium in venues_seen:
            continue

        venues_seen.add(stadium)

        is_dome = stadium in DOME_STADIUMS

        cur.execute("""
            INSERT INTO venue (name, city, is_dome)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING;
        """, (stadium, city, is_dome))

        if cur.rowcount == 1:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Venues ETL complete — inserted={inserted}")
    print(f"🏟️ Unique venues detected={len(venues_seen)}")


if __name__ == "__main__":
    load_venues()

