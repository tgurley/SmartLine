"""
SmartLine Player Odds API Endpoints
====================================
Comprehensive REST API for player prop betting data.

All endpoints use the analytical views for optimized performance.

Endpoints:
1. GET /player-odds/game/{game_id} - All props for a game
2. GET /player-odds/player/{player_id}/history - Player's prop history
3. GET /player-odds/player/{player_id}/record - Over/under hit rates
4. GET /player-odds/best-odds - Line shopping tool
5. GET /player-odds/consensus - Market consensus
6. GET /player-odds/sharp-movement - Line movement detection
7. GET /player-odds/bookmakers - Bookmaker comparison
8. GET /player-odds/streaks - Hot/cold streaks
9. GET /player-odds/home-away-splits - Situational analysis
10. GET /player-odds/games - Games with prop availability
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize router
router = APIRouter(prefix="/player-odds", tags=["Player Odds"])

# =========================================================
# RESPONSE MODELS
# =========================================================

class BetType(str, Enum):
    over = "over"
    under = "under"

class MarketKey(str, Enum):
    player_pass_yds = "player_pass_yds"
    player_pass_tds = "player_pass_tds"
    player_rush_yds = "player_rush_yds"
    player_reception_yds = "player_reception_yds"
    player_anytime_td = "player_anytime_td"

class PlayerOddsDetailed(BaseModel):
    odds_id: int
    game_id: int
    player_id: int
    player_name: str
    position: str
    player_team_abbrev: Optional[str]
    market_key: str
    bet_type: BetType
    line_value: float
    odds_american: int
    odds_decimal: float
    implied_probability_pct: float
    bookmaker_name: str
    opponent_name: Optional[str]
    player_home_away: str
    week: int
    season_year: int
    game_datetime_utc: datetime
    pulled_at_utc: datetime

class ConsensusOdds(BaseModel):
    game_id: int
    player_id: int
    player_name: str
    position: str
    player_team: Optional[str]
    market_key: str
    bet_type: BetType
    consensus_line: float
    consensus_odds_american: int
    num_bookmakers: int
    best_odds_american: int
    best_odds_bookmaker: str
    min_line: float
    max_line: float
    line_spread: float
    week: int
    season_year: int

class BestOdds(BaseModel):
    game_id: int
    player_id: int
    player_name: str
    position: str
    market_key: str
    bet_type: BetType
    line_value: float
    best_odds_american: int
    best_odds_bookmaker: str
    week: int
    season_year: int

class PlayerPropHistory(BaseModel):
    game_id: int
    week: int
    season_year: int
    opponent: str
    home_away: str
    market_key: str
    avg_line: float
    min_line: float
    max_line: float
    num_books: int
    actual_result: Optional[float]
    result_vs_line: Optional[Literal["over", "under", "push"]]
    game_datetime_utc: datetime

class OverUnderRecord(BaseModel):
    player_id: int
    player_name: str
    position: str
    market_key: str
    season_year: int
    games_with_result: int
    times_hit_over: int
    times_hit_under: int
    over_percentage: Optional[float]
    avg_diff_from_line: Optional[float]
    avg_line: float
    avg_actual: float

class SharpMovement(BaseModel):
    game_id: int
    player_id: int
    player_name: str
    market_key: str
    bet_type: BetType
    opening_line: float
    current_line: float
    line_movement: float
    movement_magnitude: Literal["major", "significant", "moderate", "minor"]
    num_books: int
    game_datetime_utc: datetime

class BookmakerComparison(BaseModel):
    book_id: int
    bookmaker_name: str
    season_year: int
    market_key: str
    games_covered: int
    players_covered: int
    total_props_offered: int
    avg_odds_american: int
    times_had_best_odds: int
    best_odds_pct: float

class PlayerStreak(BaseModel):
    player_id: int
    player_name: str
    position: str
    market_key: str
    season_year: int
    current_streak_type: Literal["over", "under", "push"]
    current_streak_length: int
    most_recent_week: int
    longest_over_streak: Optional[int]
    longest_under_streak: Optional[int]

class HomeAwaySplit(BaseModel):
    player_id: int
    player_name: str
    position: str
    market_key: str
    season_year: int
    home_games: int
    home_avg: float
    away_games: int
    away_avg: float
    home_away_diff: float

class GamePropsAvailability(BaseModel):
    game_id: int
    week: int
    season_year: int
    home_team: str
    away_team: str
    players_with_props: int
    markets_offered: int
    bookmakers: int
    total_prop_count: int
    qbs_with_props: Optional[str]
    rbs_with_props: Optional[str]
    game_datetime_utc: datetime

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    """Database connection dependency."""
    import os
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432),
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()

# =========================================================
# ENDPOINT 1: GET PROPS FOR A GAME
# =========================================================

@router.get("/game/{game_id}", response_model=List[PlayerOddsDetailed])
async def get_game_player_odds(
    game_id: int,
    market_key: Optional[MarketKey] = None,
    player_id: Optional[int] = None,
    bet_type: Optional[BetType] = None,
    book_id: Optional[int] = None,
    conn = Depends(get_db)
):
    """
    Get all player props for a specific game.
    
    **Use Case:** Game detail page, props card
    **View Used:** v_player_odds_detailed
    
    **Filters:**
    - market_key: Filter by prop type (e.g., player_pass_yds)
    - player_id: Filter by specific player
    - bet_type: Filter by over/under
    - book_id: Filter by bookmaker
    
    **Returns:** Fully denormalized prop data with odds, teams, opponents
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            odds_id, game_id, player_id, player_name, position, player_team_abbrev,
            market_key, bet_type, line_value, odds_american, odds_decimal,
            implied_probability_pct, bookmaker_name, opponent_name, player_home_away,
            week, season_year, game_datetime_utc, pulled_at_utc
        FROM v_player_odds_detailed
        WHERE game_id = %s
    """
    params = [game_id]
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    if player_id:
        query += " AND player_id = %s"
        params.append(player_id)
    
    if bet_type:
        query += " AND bet_type = %s"
        params.append(bet_type.value)
    
    if book_id:
        query += " AND book_id = %s"
        params.append(book_id)
    
    query += " ORDER BY player_name, market_key, bet_type, bookmaker_name"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No props found for game {game_id}")
    
    return results

# =========================================================
# ENDPOINT 2: PLAYER PROP HISTORY
# =========================================================

@router.get("/player/{player_id}/history", response_model=List[PlayerPropHistory])
async def get_player_prop_history(
    player_id: int,
    season_year: int,
    market_key: Optional[MarketKey] = None,
    limit: int = Query(default=50, le=100),
    conn = Depends(get_db)
):
    """
    Get historical prop lines and results for a player.
    
    **Use Case:** Player detail page, trend analysis
    **View Used:** v_player_props_history
    
    **Returns:** Game-by-game prop lines with actual results
    - Shows if player went over/under/push
    - Tracks line movement over season
    - Includes opponent and home/away context
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            game_id, week, season_year, opponent, home_away, market_key,
            avg_line, min_line, max_line, num_books, actual_result,
            result_vs_line, game_datetime_utc
        FROM v_player_props_history
        WHERE player_id = %s AND season_year = %s
    """
    params = [player_id, season_year]
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    query += " ORDER BY week DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No history found for player {player_id}")
    
    return results

# =========================================================
# ENDPOINT 3: OVER/UNDER RECORD
# =========================================================

@router.get("/player/{player_id}/record", response_model=List[OverUnderRecord])
async def get_player_over_under_record(
    player_id: int,
    season_year: Optional[int] = None,
    market_key: Optional[MarketKey] = None,
    conn = Depends(get_db)
):
    """
    Get player's over/under hit rates.
    
    **Use Case:** Betting trends, player analysis, "fade or follow" decisions
    **View Used:** v_player_over_under_record
    
    **Returns:** Hit rate statistics
    - Over percentage (e.g., hits over 68% of the time)
    - Average difference from line
    - Actual vs expected performance
    
    **Example:** "Patrick Mahomes hits OVER on pass_yds 68% of the time"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            player_id, player_name, position, market_key, season_year,
            games_with_result, times_hit_over, times_hit_under,
            over_percentage, avg_diff_from_line, avg_line, avg_actual
        FROM v_player_over_under_record
        WHERE player_id = %s
    """
    params = [player_id]
    
    if season_year:
        query += " AND season_year = %s"
        params.append(season_year)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    query += " ORDER BY season_year DESC, market_key"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No record found for player {player_id}")
    
    return results

# =========================================================
# ENDPOINT 4: BEST ODDS (LINE SHOPPING)
# =========================================================

@router.get("/best-odds", response_model=List[BestOdds])
async def get_best_odds(
    game_id: Optional[int] = None,
    player_id: Optional[int] = None,
    market_key: Optional[MarketKey] = None,
    bet_type: Optional[BetType] = None,
    season_year: Optional[int] = None,
    week: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    conn = Depends(get_db)
):
    """
    Find best available odds across all bookmakers.
    
    **Use Case:** Line shopping tool, odds aggregator
    **View Used:** v_best_odds_finder
    
    **Returns:** Best odds for each prop
    - Which bookmaker has the best odds
    - Line value and odds
    - Can filter by game, player, market
    
    **Example:** "FanDuel has -105 on Mahomes over 275.5, best available"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            game_id, player_id, player_name, position, market_key, bet_type,
            line_value, best_odds_american, best_odds_bookmaker,
            week, season_year
        FROM v_best_odds_finder
        WHERE 1=1
    """
    params = []
    
    if game_id:
        query += " AND game_id = %s"
        params.append(game_id)
    
    if player_id:
        query += " AND player_id = %s"
        params.append(player_id)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    if bet_type:
        query += " AND bet_type = %s"
        params.append(bet_type.value)
    
    if season_year:
        query += " AND season_year = %s"
        params.append(season_year)
    
    if week:
        query += " AND week = %s"
        params.append(week)
    
    query += " ORDER BY week DESC, player_name LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail="No odds found matching criteria")
    
    return results

# =========================================================
# ENDPOINT 5: CONSENSUS ODDS
# =========================================================

@router.get("/consensus", response_model=List[ConsensusOdds])
async def get_consensus_odds(
    game_id: Optional[int] = None,
    player_id: Optional[int] = None,
    market_key: Optional[MarketKey] = None,
    season_year: Optional[int] = None,
    week: Optional[int] = None,
    min_bookmakers: int = Query(default=3, ge=1),
    limit: int = Query(default=100, le=500),
    conn = Depends(get_db)
):
    """
    Get market consensus odds across bookmakers.
    
    **Use Case:** Fair value estimation, market efficiency analysis
    **View Used:** v_player_odds_consensus
    
    **Returns:** Aggregated market data
    - Consensus line (average across books)
    - Line spread (disagreement between books)
    - Best available odds
    - Number of bookmakers offering prop
    
    **Example:** "Consensus line is 276.5, ranging from 275.5 to 278.5"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            game_id, player_id, player_name, position, player_team,
            market_key, bet_type, consensus_line, consensus_odds_american,
            num_bookmakers, best_odds_american, best_odds_bookmaker,
            min_line, max_line, line_spread, week, season_year
        FROM v_player_odds_consensus
        WHERE num_bookmakers >= %s
    """
    params = [min_bookmakers]
    
    if game_id:
        query += " AND game_id = %s"
        params.append(game_id)
    
    if player_id:
        query += " AND player_id = %s"
        params.append(player_id)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    if season_year:
        query += " AND season_year = %s"
        params.append(season_year)
    
    if week:
        query += " AND week = %s"
        params.append(week)
    
    query += " ORDER BY week DESC, player_name LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail="No consensus data found")
    
    return results

# =========================================================
# ENDPOINT 6: SHARP LINE MOVEMENT
# =========================================================

@router.get("/sharp-movement", response_model=List[SharpMovement])
async def get_sharp_line_movement(
    game_id: Optional[int] = None,
    movement_magnitude: Optional[Literal["major", "significant", "moderate", "minor"]] = None,
    season_year: Optional[int] = None,
    week: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    conn = Depends(get_db)
):
    """
    Detect significant line movements (sharp money indicator).
    
    **Use Case:** Sharp money tracking, injury news detection
    **View Used:** v_sharp_line_movement
    
    **Returns:** Lines that have moved significantly
    - Opening line vs current line
    - Movement magnitude (major/significant/moderate/minor)
    - Potential sharp action or news
    
    **Thresholds:**
    - Major: 10+ unit movement
    - Significant: 5-10 units
    - Moderate: 2-5 units
    - Minor: <2 units
    
    **Example:** "Josh Allen pass_yds moved from 265.5 to 275.5 (major movement)"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            game_id, player_id, player_name, market_key, bet_type,
            opening_line, current_line, line_movement, movement_magnitude,
            num_books, game_datetime_utc
        FROM v_sharp_line_movement
        WHERE 1=1
    """
    params = []
    
    if game_id:
        query += " AND game_id = %s"
        params.append(game_id)
    
    if movement_magnitude:
        query += " AND movement_magnitude = %s"
        params.append(movement_magnitude)
    
    if season_year:
        # Need to join to get season_year
        query = query.replace(
            "FROM v_sharp_line_movement",
            """FROM v_sharp_line_movement slm
               INNER JOIN game g ON slm.game_id = g.game_id
               INNER JOIN season s ON g.season_id = s.season_id"""
        )
        query += " AND s.year = %s"
        params.append(season_year)
    
    if week:
        if "FROM v_sharp_line_movement slm" not in query:
            query = query.replace(
                "FROM v_sharp_line_movement",
                """FROM v_sharp_line_movement slm
                   INNER JOIN game g ON slm.game_id = g.game_id"""
            )
        query += " AND g.week = %s"
        params.append(week)
    
    query += " ORDER BY ABS(line_movement) DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return results

# =========================================================
# ENDPOINT 7: BOOKMAKER COMPARISON
# =========================================================

@router.get("/bookmakers", response_model=List[BookmakerComparison])
async def get_bookmaker_comparison(
    season_year: int,
    market_key: Optional[MarketKey] = None,
    min_best_odds_pct: float = Query(default=0, ge=0, le=100),
    conn = Depends(get_db)
):
    """
    Compare bookmakers head-to-head.
    
    **Use Case:** Bookmaker ratings, finding best books
    **View Used:** v_bookmaker_comparison
    
    **Returns:** Bookmaker performance metrics
    - Coverage (games, players, props offered)
    - Competitiveness (how often they have best odds)
    - Best odds percentage
    
    **Example:** "FanDuel has best odds 42% of the time on pass_yds props"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            book_id, bookmaker_name, season_year, market_key,
            games_covered, players_covered, total_props_offered,
            avg_odds_american, times_had_best_odds, best_odds_pct
        FROM v_bookmaker_comparison
        WHERE season_year = %s
          AND best_odds_pct >= %s
    """
    params = [season_year, min_best_odds_pct]
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    query += " ORDER BY best_odds_pct DESC, total_props_offered DESC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail="No bookmaker data found")
    
    return results

# =========================================================
# ENDPOINT 8: PLAYER STREAKS
# =========================================================

@router.get("/streaks", response_model=List[PlayerStreak])
async def get_player_streaks(
    season_year: int,
    streak_type: Optional[Literal["over", "under", "push"]] = None,
    min_streak_length: int = Query(default=3, ge=1),
    market_key: Optional[MarketKey] = None,
    limit: int = Query(default=50, le=200),
    conn = Depends(get_db)
):
    """
    Track player hot and cold streaks.
    
    **Use Case:** Betting trends, streak riders/faders
    **View Used:** v_player_prop_streaks
    
    **Returns:** Current and longest streaks
    - Current streak type and length
    - Longest over streak in season
    - Longest under streak in season
    
    **Example:** "Tyreek Hill on 6-game OVER streak for reception_yds"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            player_id, player_name, position, market_key, season_year,
            current_streak_type, current_streak_length, most_recent_week,
            longest_over_streak, longest_under_streak
        FROM v_player_prop_streaks
        WHERE season_year = %s
          AND current_streak_length >= %s
    """
    params = [season_year, min_streak_length]
    
    if streak_type:
        query += " AND current_streak_type = %s"
        params.append(streak_type)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    query += " ORDER BY current_streak_length DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return results

# =========================================================
# ENDPOINT 9: HOME/AWAY SPLITS
# =========================================================

@router.get("/home-away-splits", response_model=List[HomeAwaySplit])
async def get_home_away_splits(
    season_year: int,
    player_id: Optional[int] = None,
    market_key: Optional[MarketKey] = None,
    min_home_away_diff: float = Query(default=0),
    limit: int = Query(default=100, le=500),
    conn = Depends(get_db)
):
    """
    Analyze player performance at home vs away.
    
    **Use Case:** Situational betting, home field advantage analysis
    **View Used:** v_home_away_splits
    
    **Returns:** Performance splits
    - Home games average
    - Away games average
    - Home/away differential
    
    **Example:** "Josh Allen averages 40 more pass_yds at home"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            player_id, player_name, position, market_key, season_year,
            home_games, home_avg, away_games, away_avg, home_away_diff
        FROM v_home_away_splits
        WHERE season_year = %s
          AND ABS(home_away_diff) >= %s
    """
    params = [season_year, min_home_away_diff]
    
    if player_id:
        query += " AND player_id = %s"
        params.append(player_id)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key.value)
    
    query += " ORDER BY ABS(home_away_diff) DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return results

# =========================================================
# ENDPOINT 10: GAMES WITH PROP AVAILABILITY
# =========================================================

@router.get("/games", response_model=List[GamePropsAvailability])
async def get_games_with_props(
    season_year: int,
    week: Optional[int] = None,
    min_players: int = Query(default=10, ge=0),
    conn = Depends(get_db)
):
    """
    Get games with player prop availability.
    
    **Use Case:** Game listing, prop coverage check
    **View Used:** v_player_odds_by_game
    
    **Returns:** Game-level prop summary
    - How many players have props
    - How many markets offered
    - Which QBs/RBs have props
    - Total prop count
    
    **Example:** "Week 5 Chiefs vs Bills: 87 players, 5 markets, 423 total props"
    """
    cursor = conn.cursor()
    
    query = """
        SELECT 
            g.game_id, g.week, g.season_year, g.home_team, g.away_team,
            g.players_with_props, g.markets_offered, g.bookmakers,
            g.total_prop_count, g.qbs_with_props, g.rbs_with_props,
            g.game_datetime_utc
        FROM v_player_odds_by_game g
        INNER JOIN season s ON g.season_year = s.year
        WHERE g.season_year = %s
          AND COALESCE(g.players_with_props, 0) >= %s
    """
    params = [season_year, min_players]
    
    if week:
        query += " AND g.week = %s"
        params.append(week)
    
    query += " ORDER BY g.week, g.game_datetime_utc"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    if not results:
        raise HTTPException(status_code=404, detail="No games found with props")
    
    return results

# =========================================================
# BONUS ENDPOINT: COMBINED PLAYER ANALYSIS
# =========================================================

class PlayerAnalysis(BaseModel):
    """Complete player prop analysis combining multiple views."""
    player_id: int
    player_name: str
    position: str
    season_year: int
    
    # From v_player_over_under_record
    overall_record: Optional[OverUnderRecord]
    
    # From v_player_prop_streaks
    current_streaks: Optional[List[PlayerStreak]]
    
    # From v_home_away_splits
    home_away_splits: Optional[List[HomeAwaySplit]]
    
    # From v_player_props_history (recent games)
    recent_games: Optional[List[PlayerPropHistory]]

@router.get("/player/{player_id}/analysis", response_model=PlayerAnalysis)
async def get_player_complete_analysis(
    player_id: int,
    season_year: int,
    market_key: MarketKey,
    conn = Depends(get_db)
):
    """
    Get comprehensive player prop analysis.
    
    **Use Case:** Player detail page - everything in one call
    **Views Used:** Multiple (record, streaks, splits, history)
    
    **Returns:** Complete player analysis
    - Overall O/U record
    - Current streaks
    - Home/away splits
    - Recent game results
    
    **Example:** One endpoint call gets all data for player detail page
    """
    cursor = conn.cursor()
    
    # Get overall record
    cursor.execute("""
        SELECT * FROM v_player_over_under_record
        WHERE player_id = %s AND season_year = %s AND market_key = %s
    """, [player_id, season_year, market_key.value])
    record = cursor.fetchone()
    
    # Get current streaks
    cursor.execute("""
        SELECT * FROM v_player_prop_streaks
        WHERE player_id = %s AND season_year = %s AND market_key = %s
    """, [player_id, season_year, market_key.value])
    streaks = cursor.fetchall()
    
    # Get home/away splits
    cursor.execute("""
        SELECT * FROM v_home_away_splits
        WHERE player_id = %s AND season_year = %s AND market_key = %s
    """, [player_id, season_year, market_key.value])
    splits = cursor.fetchall()
    
    # Get recent games (last 10)
    cursor.execute("""
        SELECT * FROM v_player_props_history
        WHERE player_id = %s AND season_year = %s AND market_key = %s
        ORDER BY week DESC LIMIT 10
    """, [player_id, season_year, market_key.value])
    recent = cursor.fetchall()
    
    cursor.close()
    
    if not record and not streaks and not splits and not recent:
        raise HTTPException(status_code=404, detail=f"No data found for player {player_id}")
    
    return {
        "player_id": player_id,
        "player_name": record['player_name'] if record else (recent[0]['player_name'] if recent else "Unknown"),
        "position": record['position'] if record else (recent[0]['position'] if recent else "Unknown"),
        "season_year": season_year,
        "overall_record": record,
        "current_streaks": streaks,
        "home_away_splits": splits,
        "recent_games": recent
    }
