from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.models import StrategyRequest
from app.crud import backtest_strategy
from app.database import get_connection

app = FastAPI(title="SmartLine NFL Betting Intelligence")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # local dev
        "http://127.0.0.1:5173",
        "https://smart-line-three.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/backtest")
def backtest(strategy: StrategyRequest):
    rows = backtest_strategy(strategy)

    bets = len(rows)
    wins = sum(1 for r in rows if r["profit"] > 0)
    total_profit = sum(r["profit"] for r in rows)

    roi = (total_profit / (bets * strategy.stake) * 100) if bets > 0 else 0

    return {
        "strategy": strategy.name,
        "bets": bets,
        "wins": wins,
        "win_pct": round((wins / bets) * 100, 2) if bets else 0,
        "total_profit": round(total_profit, 2),
        "roi_pct": round(roi, 2),
        "results": rows
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    conn = get_connection()
    conn.close()
    return {"db": "ok"}

@app.get("/db/verify")
def db_verify():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.get("/games")
def get_games(
    season: int = Query(...),
    week: int = Query(...)
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.game_id,
            g.game_datetime_utc AS kickoff_utc,
            g.status,

            ht.team_id AS home_team_id,
            ht.name AS home_team_name,
            ht.abbrev AS home_team_abbrev,

            at.team_id AS away_team_id,
            at.name AS away_team_name,
            at.abbrev AS away_team_abbrev,

            v.name AS venue_name,
            v.city AS venue_city,
            v.state AS venue_state,
            v.is_dome,

            r.home_score,
            r.away_score,
            r.home_win,

            w.temp_f,
            w.wind_mph,
            w.precip_prob,
            w.precip_mm,
            w.weather_severity_score,
            w.is_cold,
            w.is_windy,
            w.is_heavy_wind,
            w.is_rain_risk,
            w.is_storm_risk,
            w.source AS weather_source

        FROM game g
        JOIN season s ON g.season_id = s.season_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        LEFT JOIN venue v ON g.venue_id = v.venue_id
        LEFT JOIN game_result r ON r.game_id = g.game_id
        LEFT JOIN weather_observation w ON w.game_id = g.game_id

        WHERE s.year = %s
          AND g.week = %s

        ORDER BY g.game_datetime_utc;
    """, (season, week))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    games = []

    for r in rows:
        games.append({
            "game_id": r["game_id"],
            "kickoff_utc": r["kickoff_utc"],
            "status": r["status"],

            "home_team": {
                "team_id": r["home_team_id"],
                "name": r["home_team_name"],
                "abbrev": r["home_team_abbrev"],
            },
            "away_team": {
                "team_id": r["away_team_id"],
                "name": r["away_team_name"],
                "abbrev": r["away_team_abbrev"],
            },

            "venue": {
                "name": r["venue_name"],
                "city": r["venue_city"],
                "state": r["venue_state"],
                "is_dome": r["is_dome"],
            },

            "result": (
                {
                    "home_score": r["home_score"],
                    "away_score": r["away_score"],
                    "winner": "home" if r["home_win"] else "away"
                } if r["home_score"] is not None else None
            ),

            "weather": {
                "source": r["weather_source"] or "dome",
                "temp_f": r["temp_f"],
                "wind_mph": r["wind_mph"],
                "precip_prob": r["precip_prob"],
                "precip_mm": r["precip_mm"],
                "severity_score": r["weather_severity_score"] or 0,
                "flags": {
                    "cold": r["is_cold"] or False,
                    "windy": r["is_windy"] or False,
                    "heavy_wind": r["is_heavy_wind"] or False,
                    "rain_risk": r["is_rain_risk"] or False,
                    "storm_risk": r["is_storm_risk"] or False,
                }
            }
        })

    return {
        "season": season,
        "week": week,
        "games": games
    }
    
@app.get("/games/{game_id}")
def get_game_detail(game_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.game_id,
            g.game_datetime_utc AS kickoff_utc,
            g.status,

            ht.team_id AS home_team_id,
            ht.name AS home_team_name,
            ht.abbrev AS home_team_abbrev,

            at.team_id AS away_team_id,
            at.name AS away_team_name,
            at.abbrev AS away_team_abbrev,

            r.home_score,
            r.away_score,

            w.temp_f,
            w.wind_mph,
            w.precip_prob,
            w.precip_mm,
            w.weather_severity_score,
            w.is_cold,
            w.is_windy,
            w.is_heavy_wind,
            w.is_rain_risk,
            w.is_storm_risk,
            w.source AS weather_source

        FROM game g
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        LEFT JOIN game_result r ON r.game_id = g.game_id
        LEFT JOIN weather_observation w ON w.game_id = g.game_id
        WHERE g.game_id = %s;
    """, (game_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"error": "Game not found"}

    return {
        "game_id": row["game_id"],
        "kickoff_utc": row["kickoff_utc"],
        "status": row["status"],
        "home_team": {
            "name": row["home_team_name"],
            "abbrev": row["home_team_abbrev"]
        },
        "away_team": {
            "name": row["away_team_name"],
            "abbrev": row["away_team_abbrev"]
        },
        "result": (
            {
                "home_score": row["home_score"],
                "away_score": row["away_score"]
            } if row["home_score"] is not None else None
        ),
        "weather": {
            "source": row["weather_source"],
            "temp_f": row["temp_f"],
            "wind_mph": row["wind_mph"],
            "precip_prob": row["precip_prob"],
            "precip_mm": row["precip_mm"],
            "severity_score": row["weather_severity_score"],
            "flags": {
                "cold": row["is_cold"],
                "windy": row["is_windy"],
                "heavy_wind": row["is_heavy_wind"],
                "rain_risk": row["is_rain_risk"],
                "storm_risk": row["is_storm_risk"],
            }
        }
    }
