import os
import requests
from etl.db import get_conn

# ==========================================================
# CONFIG
# ==========================================================
API_KEY = os.getenv("API_SPORTS_KEY")
if not API_KEY:
    raise RuntimeError("API_SPORTS_KEY environment variable is not set")

BASE_URL = "https://v1.american-football.api-sports.io"
TEAMS_ENDPOINT = "/teams"

HEADERS = {
    "x-apisports-key": API_KEY
}

NFL_LEAGUE_ID = 1
SEASON_YEAR = 2023


# ==========================================================
# MAIN ETL
# ==========================================================
def load_teams():
    conn = get_conn()
    cur = conn.cursor()

    # ------------------------------------------------------
    # Resolve NFL league_id from DB
    # ------------------------------------------------------
    cur.execute("SELECT league_id FROM league WHERE name = 'NFL';")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("NFL league not found in database")

    league_id = row[0]

    print("🚀 Fetching NFL teams from API-Sports (2023)...")

    resp = requests.get(
        BASE_URL + TEAMS_ENDPOINT,
        headers=HEADERS,
        params={
            "league": NFL_LEAGUE_ID,
            "season": SEASON_YEAR
        },
        timeout=30
    )
    resp.raise_for_status()
    payload = resp.json()

    teams = payload.get("response", [])
    print(f"📦 API returned {len(teams)} teams")

    inserted = 0
    updated = 0

    for t in teams:
        team = t

        api_team_id = team.get("id")
        name = team.get("name")
        city = team.get("city")
        abbrev = team.get("code")  # API-Sports DOES provide code here

        if abbrev is None:
            continue

        # Try update first (preferred)
        cur.execute("""
            UPDATE team
            SET
                name = %s,
                city = %s,
                external_team_key = %s
            WHERE league_id = %s
              AND external_team_key = %s;
        """, (
            name,
            city,
            api_team_id,
            league_id,
            api_team_id
        ))

        if cur.rowcount == 1:
            updated += 1
            continue

        # Otherwise insert
        cur.execute("""
            INSERT INTO team (
                league_id,
                name,
                abbrev,
                city,
                external_team_key
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (league_id, abbrev) DO NOTHING;
        """, (
            league_id,
            name,
            abbrev,
            city,
            api_team_id
        ))

        if cur.rowcount == 1:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Teams ETL complete — inserted={inserted}, updated={updated}")


if __name__ == "__main__":
    load_teams()
