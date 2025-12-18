import os
import requests
from datetime import datetime
from etl.db import get_conn

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

STATUS_MAP = {
    "FT": "final",
    "NS": "scheduled",
    "LIVE": "in_progress"
}


def load_games():
    conn = get_conn()
    cur = conn.cursor()

    # Resolve season_id
    cur.execute("""
        SELECT s.season_id
        FROM season s
        JOIN league l ON l.league_id = s.league_id
        WHERE l.name = 'NFL' AND s.year = %s;
    """, (SEASON_YEAR,))
    season_id = cur.fetchone()[0]

    # Build team lookup by API-Sports ID
    cur.execute("""
        SELECT team_id, external_team_key
        FROM team
        WHERE league_id = (
            SELECT league_id FROM league WHERE name = 'NFL'
        );
    """)
    team_map = {row[1]: row[0] for row in cur.fetchall()}

    print("🚀 Fetching NFL 2023 games from API-Sports...")

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
    games = resp.json().get("response", [])

    print(f"📦 API returned {len(games)} games")

    inserted = 0

    for g in games:
        game = g["game"]
        teams = g["teams"]
        status_raw = game["status"]["short"]

        # Skip non-regular season games if needed
        if game.get("stage") != "Regular Season":
            continue

        week = int(game["week"].replace("Week ", ""))
        kickoff = datetime.utcfromtimestamp(game["date"]["timestamp"])

        home_api_id = teams["home"]["id"]
        away_api_id = teams["away"]["id"]

        if home_api_id not in team_map or away_api_id not in team_map:
            continue

        cur.execute("""
            INSERT INTO game (
                season_id,
                week,
                game_datetime_utc,
                home_team_id,
                away_team_id,
                status,
                external_game_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_game_key) DO NOTHING;
        """, (
            season_id,
            week,
            kickoff,
            team_map[home_api_id],
            team_map[away_api_id],
            STATUS_MAP.get(status_raw, "scheduled"),
            game["id"]
        ))

        if cur.rowcount == 1:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Games ETL complete — inserted={inserted}")
if __name__ == "__main__": 
    load_games()
