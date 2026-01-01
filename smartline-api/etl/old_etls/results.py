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
GAMES_ENDPOINT = "/games"

HEADERS = {
    "x-apisports-key": API_KEY
}

NFL_LEAGUE_ID = 1
SEASON_YEAR = 2023


# ==========================================================
# MAIN ETL
# ==========================================================
def load_results():
    conn = get_conn()
    cur = conn.cursor()

    # ------------------------------------------------------
    # Build external_game_key → game_id map
    # ------------------------------------------------------
    cur.execute("""
        SELECT game_id, external_game_key
        FROM game
        WHERE season_id = (
            SELECT season_id
            FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = %s
        );
    """, (SEASON_YEAR,))

    game_map = {row[1]: row[0] for row in cur.fetchall()}
    print(f"🔗 Loaded {len(game_map)} games from DB")

    # ------------------------------------------------------
    # Fetch games (again, as source of truth for scores)
    # ------------------------------------------------------
    print("🚀 Fetching NFL 2023 games for results...")
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
    skipped = 0

    for g in games:
        game = g["game"]

        # Only completed regular season games
        if game.get("stage") != "Regular Season":
            continue
        status = game.get("status", {})
        status_long = status.get("long")

        if not status_long.startswith("Final") and not status_long.startswith("Finished"):
            print(
                f"⏭️ Skipping non-final game "
            )
            continue

        external_game_key = str(game["id"])

        if external_game_key not in game_map:
            skipped += 1
            continue

        scores = g.get("scores", {})
        home_score = scores.get("home", {}).get("total")
        away_score = scores.get("away", {}).get("total")

        if home_score is None or away_score is None:
            skipped += 1
            continue

        cur.execute("""
            INSERT INTO game_result (
                game_id,
                home_score,
                away_score
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (game_id) DO NOTHING;
        """, (
            game_map[external_game_key],
            home_score,
            away_score
        ))

        if cur.rowcount == 1:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Results ETL complete — inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    load_results()
