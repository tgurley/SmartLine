import os
import requests
from etl.db import get_conn

API_KEY = os.getenv("API_SPORTS_KEY")
if not API_KEY:
    raise RuntimeError("API_SPORTS_KEY not set")

BASE_URL = "https://v1.american-football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# --------------------------------------------------
# Metric extraction map: metric_name -> JSON path
# --------------------------------------------------
STAT_PATHS = {
    "total_yards": ("yards", "total"),
    "passing_yards": ("passing", "total"),
    "rushing_yards": ("rushings", "total"),
    "turnovers": ("turnovers", "total"),
    "penalties": ("penalties", "total"),
    "plays": ("plays", "total"),
    "points_against": ("points_against", "total"),
    "time_of_possession": ("posession", "total"),
}


def parse_possession(value: str) -> float:
    """Convert mm:ss → minutes"""
    mins, secs = value.split(":")
    return float(mins) + float(secs) / 60


def load_team_game_stats():
    conn = get_conn()
    cur = conn.cursor()

    # --------------------------------------------------
    # Load games
    # --------------------------------------------------
    cur.execute("""
        SELECT game_id, external_game_key
        FROM game
        ORDER BY game_id;
    """)
    games = cur.fetchall()
    print(f"📦 Loaded {len(games)} games")

    # --------------------------------------------------
    # Load team map
    # --------------------------------------------------
    cur.execute("""
        SELECT team_id, external_team_key
        FROM team;
    """)
    team_map = {str(api_id): team_id for team_id, api_id in cur.fetchall()}

    inserted = 0
    skipped_games = 0

    for game_id, api_game_id in games:
        resp = requests.get(
            f"{BASE_URL}/games/statistics/teams",
            headers=HEADERS,
            params={"id": api_game_id},
            timeout=30,
        )

        print(f"\n🎯 GAME {api_game_id}")
        print(f"Status code: {resp.status_code}")
        print(f"Raw response: {resp.text[:500]}")
        
        if resp.status_code != 200:
            skipped_games += 1
            continue

        response = resp.json().get("response", [])

        if not response:
            skipped_games += 1
            continue

        for team_block in response:
            team_api_id = str(team_block["team"]["id"])

            if team_api_id not in team_map:
                continue

            team_id = team_map[team_api_id]
            stats = team_block.get("statistics", {})

            for metric, path in STAT_PATHS.items():
                group = path[0]
                field = path[1]

                if group not in stats:
                    continue

                value = stats[group].get(field)

                if value in (None, ""):
                    continue

                try:
                    if metric == "time_of_possession":
                        value = parse_possession(value)
                    else:
                        value = float(value)
                except Exception:
                    continue
                

                cur.execute(
                    """
                    INSERT INTO team_game_stat (
                        game_id, team_id, metric, value
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (game_id, team_id, metric, value),
                )

                inserted += 1

        conn.commit()

    cur.close()
    conn.close()

    print(
        f"✅ Team game stats ETL complete — "
        f"inserted={inserted}, games_skipped={skipped_games}"
    )


if __name__ == "__main__":
    load_team_game_stats()

