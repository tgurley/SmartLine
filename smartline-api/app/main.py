from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.player_endpoints import router as player_router
from app.team_endpoints import router as team_router
from app.player_statistics_endpoints import router as player_statistics_router
from app.game_team_statistics_endpoints import router as game_team_statistic_router
from app.game_player_statistics_endpoints import router as game_player_statistics_router
from app.player_odds_endpoints import router as player_odds_router
from app.bankroll_endpoints import router as bankroll_router
from app.settings_endpoints import router as settings_router
from app.export_endpoints import router as export_router
from app.models import StrategyRequest
from app.crud import backtest_strategy
from app.database import get_connection
from typing import Optional

app = FastAPI(title="SmartLine NFL Betting Intelligence")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[                                 # ← List format
    "http://localhost:5173",
    "https://smart-line-three.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_router)
app.include_router(team_router)
app.include_router(player_statistics_router)
app.include_router(player_odds_router)
app.include_router(game_team_statistic_router)
app.include_router(game_player_statistics_router)

app.include_router(bankroll_router)
app.include_router(settings_router)
app.include_router(export_router)

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
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        LEFT JOIN venue v ON g.venue_id = v.venue_id
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
            "team_id": row["home_team_id"],
            "name": row["home_team_name"],
            "abbrev": row["home_team_abbrev"]
        },
        "away_team": {
            "team_id": row["away_team_id"],
            "name": row["away_team_name"],
            "abbrev": row["away_team_abbrev"]
        },
        "venue": {
            "name": row["venue_name"],
            "city": row["venue_city"],
            "state": row["venue_state"],
            "is_dome": row["is_dome"]
        },
        "result": (
            {
                "home_score": row["home_score"],
                "away_score": row["away_score"],
                "winner": "home" if row["home_win"] else "away"
            } if row["home_score"] is not None else None
        ),
        "weather": {
            "source": row["weather_source"] or "dome",
            "temp_f": row["temp_f"],
            "wind_mph": row["wind_mph"],
            "precip_prob": row["precip_prob"],
            "precip_mm": row["precip_mm"],
            "severity_score": row["weather_severity_score"] or 0,
            "flags": {
                "cold": row["is_cold"] or False,
                "windy": row["is_windy"] or False,
                "heavy_wind": row["is_heavy_wind"] or False,
                "rain_risk": row["is_rain_risk"] or False,
                "storm_risk": row["is_storm_risk"] or False,
            }
        }
    }
    
@app.get("/odds")
def get_odds(
    season: int = Query(2023),
    week: Optional[int] = Query(None),
    game_id: Optional[int] = Query(None)
):
    """
    Get odds data for games
    Can filter by season, week, or specific game
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Build WHERE clause based on filters
    where_clauses = ["s.year = %s"]
    params = [season]
    
    if week:
        where_clauses.append("g.week = %s")
        params.append(week)
    
    if game_id:
        where_clauses.append("g.game_id = %s")
        params.append(game_id)
    
    where_sql = " AND ".join(where_clauses)
    
    cur.execute(f"""
        SELECT
            g.game_id,
            g.week,
            g.game_datetime_utc,
            
            ht.abbrev AS home_team,
            at.abbrev AS away_team,
            
            b.name AS book,
            ol.market,
            ol.side,
            ol.line_value,
            ol.price_american,
            ol.pulled_at_utc,
            
            -- Determine if this is opening or closing
            CASE 
                WHEN ol.pulled_at_utc = MIN(ol.pulled_at_utc) OVER (PARTITION BY ol.game_id, ol.book_id, ol.market)
                THEN 'opening'
                ELSE 'closing'
            END as line_type
            
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        JOIN season s ON s.season_id = g.season_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        JOIN book b ON b.book_id = ol.book_id
        
        WHERE {where_sql}
        
        ORDER BY g.game_datetime_utc, b.name, ol.market, ol.pulled_at_utc;
    """, params)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Organize by game
    games_odds = {}
    
    for row in rows:
        game_id = row["game_id"]
        
        if game_id not in games_odds:
            games_odds[game_id] = {
                "game_id": game_id,
                "week": row["week"],
                "kickoff_utc": row["game_datetime_utc"],
                "matchup": f"{row['away_team']} @ {row['home_team']}",
                "books": {}
            }
        
        book = row["book"]
        if book not in games_odds[game_id]["books"]:
            games_odds[game_id]["books"][book] = {
                "spread": {"opening": None, "closing": None},
                "total": {"opening": None, "closing": None},
                "moneyline": {"opening": None, "closing": None}
            }
        
        market = row["market"]
        line_type = row["line_type"]
        
        games_odds[game_id]["books"][book][market][line_type] = {
            "side": row["side"],
            "line": row["line_value"],
            "price": row["price_american"],
            "pulled_at": row["pulled_at_utc"]
        }
    
    return {
        "season": season,
        "week": week,
        "game_id": game_id,
        "games": list(games_odds.values())
    }


@app.get("/odds/game/{game_id}")
def get_game_odds(game_id: int):
    """
    Get all odds for a specific game with line movement
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT
            g.game_id,
            g.week,
            g.game_datetime_utc,
            
            ht.abbrev AS home_team,
            at.abbrev AS away_team,
            
            b.name AS book,
            ol.market,
            ol.side,
            ol.line_value,
            ol.price_american,
            ol.pulled_at_utc
            
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        JOIN book b ON b.book_id = ol.book_id
        
        WHERE g.game_id = %s
        
        ORDER BY b.name, ol.market, ol.pulled_at_utc;
    """, (game_id,))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        return {"error": "No odds found for this game"}
    
    # Organize by book and market
    game_info = {
        "game_id": rows[0]["game_id"],
        "week": rows[0]["week"],
        "kickoff_utc": rows[0]["game_datetime_utc"],
        "matchup": f"{rows[0]['away_team']} @ {rows[0]['home_team']}",
        "books": {}
    }
    
    for row in rows:
        book = row["book"]
        market = row["market"]
        
        if book not in game_info["books"]:
            game_info["books"][book] = {}
        
        if market not in game_info["books"][book]:
            game_info["books"][book][market] = []
        
        game_info["books"][book][market].append({
            "side": row["side"],
            "line": row["line_value"],
            "price": row["price_american"],
            "pulled_at": row["pulled_at_utc"]
        })
    
    return game_info


@app.get("/odds/movement")
def get_line_movement(
    season: int = Query(2023),
    week: Optional[int] = Query(None),
    market: str = Query("spread", description="spread, total, or moneyline")
):
    """
    Get line movement data for spread/total analysis
    Shows opening vs closing and movement magnitude
    """
    conn = get_connection()
    cur = conn.cursor()
    
    where_clauses = ["s.year = %s", "ol.market = %s"]
    params = [season, market]
    
    if week:
        where_clauses.append("g.week = %s")
        params.append(week)
    
    where_sql = " AND ".join(where_clauses)
    
    cur.execute(f"""
        WITH game_odds AS (
            SELECT
                g.game_id,
                g.week,
                g.game_datetime_utc,
                ht.abbrev AS home_team,
                at.abbrev AS away_team,
                b.name AS book,
                ol.market,
                ol.side,
                ol.line_value,
                ol.pulled_at_utc,
                ROW_NUMBER() OVER (
                    PARTITION BY ol.game_id, ol.book_id, ol.market, ol.side 
                    ORDER BY ol.pulled_at_utc ASC
                ) as rn_asc,
                ROW_NUMBER() OVER (
                    PARTITION BY ol.game_id, ol.book_id, ol.market, ol.side 
                    ORDER BY ol.pulled_at_utc DESC
                ) as rn_desc
            FROM odds_line ol
            JOIN game g ON g.game_id = ol.game_id
            JOIN season s ON s.season_id = g.season_id
            JOIN team ht ON g.home_team_id = ht.team_id
            JOIN team at ON g.away_team_id = at.team_id
            JOIN book b ON b.book_id = ol.book_id
            WHERE {where_sql}
        )
        SELECT
            opening.game_id,
            opening.week,
            opening.game_datetime_utc,
            opening.home_team,
            opening.away_team,
            opening.book,
            opening.market,
            opening.side,
            opening.line_value as opening_line,
            closing.line_value as closing_line,
            closing.line_value - opening.line_value as movement,
            opening.pulled_at_utc as opening_time,
            closing.pulled_at_utc as closing_time
        FROM game_odds opening
        JOIN game_odds closing ON 
            closing.game_id = opening.game_id 
            AND closing.book = opening.book
            AND closing.market = opening.market
            AND closing.side = opening.side
            AND closing.rn_desc = 1
        WHERE opening.rn_asc = 1
        ORDER BY ABS(closing.line_value - opening.line_value) DESC;
    """, params)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    movements = []
    for row in rows:
        movements.append({
            "game_id": row["game_id"],
            "week": row["week"],
            "matchup": f"{row['away_team']} @ {row['home_team']}",
            "book": row["book"],
            "market": row["market"],
            "side": row["side"],
            "opening_line": row["opening_line"],
            "closing_line": row["closing_line"],
            "movement": row["movement"],
            "opening_time": row["opening_time"],
            "closing_time": row["closing_time"]
        })
    
    return {
        "season": season,
        "week": week,
        "market": market,
        "movements": movements
    }


@app.get("/odds/compare")
def compare_odds(game_id: int, market: str = Query("spread")):
    """
    Compare current odds across all books for a specific game
    Shows best available lines
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        WITH latest_odds AS (
            SELECT
                ol.*,
                b.name as book_name,
                ROW_NUMBER() OVER (
                    PARTITION BY ol.book_id, ol.market, ol.side 
                    ORDER BY ol.pulled_at_utc DESC
                ) as rn
            FROM odds_line ol
            JOIN book b ON b.book_id = ol.book_id
            WHERE ol.game_id = %s AND ol.market = %s
        )
        SELECT
            book_name,
            side,
            line_value,
            price_american,
            pulled_at_utc
        FROM latest_odds
        WHERE rn = 1
        ORDER BY book_name, side;
    """, (game_id, market))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Find best lines
    comparison = {
        "game_id": game_id,
        "market": market,
        "books": [],
        "best_lines": {}
    }
    
    for row in rows:
        comparison["books"].append({
            "book": row["book_name"],
            "side": row["side"],
            "line": row["line_value"],
            "price": row["price_american"],
            "updated": row["pulled_at_utc"]
        })
    
    return comparison
