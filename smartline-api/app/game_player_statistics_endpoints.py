"""
Game Player Statistics API Endpoints
=====================================
Provides endpoints for querying individual player performance statistics for games.

Endpoints:
- GET /statistics/games/{game_id}/players - Get player stats for a specific game
- GET /statistics/players/{player_id}/games - Get game-by-game stats for a player
- GET /statistics/players/leaders/{stat_group}/{metric} - Get statistical leaders
"""

from typing import Optional, List
from datetime import datetime
import psycopg2
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
import os

# Initialize router
router = APIRouter(prefix="/statistics", tags=["Game Player Statistics"])


# ==================== Database Connection ====================

def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )


# =========================================================
# Response Models
# =========================================================

class PlayerGameStat(BaseModel):
    """Model for a single player statistic."""
    stat_id: int
    player_id: int
    player_name: str
    stat_group: str
    metric_name: str
    metric_value: Optional[str]


class GamePlayerStatisticsResponse(BaseModel):
    """Response model for game player statistics."""
    game_id: int
    week: int
    game_datetime_utc: datetime
    stat_count: int
    players: List[dict]  # Grouped by player


class PlayerGameStatsResponse(BaseModel):
    """Response model for player's game-by-game statistics."""
    player_id: int
    player_name: str
    position: Optional[str]
    season: Optional[int]
    game_count: int
    games: List[dict]


class StatLeaderItem(BaseModel):
    """Model for statistical leaders."""
    player_id: int
    player_name: str
    position: Optional[str]
    team_name: str
    team_abbrev: str
    game_id: int
    week: int
    metric_value: str
    game_date: datetime


# =========================================================
# Endpoints
# =========================================================

@router.get(
    "/games/{game_id}/players",
    response_model=GamePlayerStatisticsResponse,
    summary="Get Player Statistics for a Game"
)
async def get_game_player_statistics(
    game_id: int = Path(..., description="Game ID"),
    stat_group: Optional[str] = Query(
        None,
        description="Filter by stat group (Passing, Rushing, Receiving, etc.)"
    )
):
    """
    Get detailed player statistics for a specific game.
    
    Optionally filter by stat group (Passing, Rushing, Receiving, Defense, etc.)
    """
    query = """
        SELECT 
            gps.stat_id,
            gps.player_id,
            p.full_name as player_name,
            p.position,
            t.name as team_name,
            t.abbrev as team_abbrev,
            gps.stat_group,
            gps.metric_name,
            gps.metric_value,
            g.week,
            g.game_datetime_utc
        FROM game_player_statistics gps
        JOIN player p ON gps.player_id = p.player_id
        JOIN team t ON gps.team_id = t.team_id
        JOIN game g ON gps.game_id = g.game_id
        WHERE gps.game_id = %s
        {stat_group_filter}
        ORDER BY 
            t.name,
            p.full_name,
            gps.stat_group,
            gps.metric_name
    """
    
    params = [game_id]
    stat_group_filter = ""
    
    if stat_group:
        stat_group_filter = "AND gps.stat_group = %s"
        params.append(stat_group)
    
    query = query.format(stat_group_filter=stat_group_filter)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Statistics not found for game {game_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                stats = [dict(zip(columns, row)) for row in rows]
                
                # Group by player
                players_dict = {}
                week = stats[0]['week']
                game_datetime = stats[0]['game_datetime_utc']
                
                for stat in stats:
                    player_id = stat['player_id']
                    if player_id not in players_dict:
                        players_dict[player_id] = {
                            'player_id': player_id,
                            'player_name': stat['player_name'],
                            'position': stat['position'],
                            'team_name': stat['team_name'],
                            'team_abbrev': stat['team_abbrev'],
                            'stat_groups': {}
                        }
                    
                    stat_group = stat['stat_group']
                    if stat_group not in players_dict[player_id]['stat_groups']:
                        players_dict[player_id]['stat_groups'][stat_group] = []
                    
                    players_dict[player_id]['stat_groups'][stat_group].append({
                        'metric_name': stat['metric_name'],
                        'metric_value': stat['metric_value']
                    })
                
                return GamePlayerStatisticsResponse(
                    game_id=game_id,
                    week=week,
                    game_datetime_utc=game_datetime,
                    stat_count=len(stats),
                    players=list(players_dict.values())
                )
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/players/{player_id}/games",
    response_model=PlayerGameStatsResponse,
    summary="Get Game-by-Game Statistics for a Player"
)
async def get_player_game_statistics(
    player_id: int = Path(..., description="Player ID"),
    season: Optional[int] = Query(None, description="Filter by season year"),
    stat_group: Optional[str] = Query(
        None,
        description="Filter by stat group (Passing, Rushing, etc.)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum games to return")
):
    """
    Get game-by-game statistics for a specific player.
    
    Optionally filter by season and/or stat group.
    """
    query = """
        SELECT 
            gps.game_id,
            g.week,
            g.game_datetime_utc,
            s.year as season,
            gps.stat_group,
            gps.metric_name,
            gps.metric_value,
            t.name as team_name,
            t.abbrev as team_abbrev,
            CASE 
                WHEN gps.team_id = g.home_team_id THEN at.name
                ELSE ht.name
            END as opponent_name,
            CASE 
                WHEN gps.team_id = g.home_team_id THEN at.abbrev
                ELSE ht.abbrev
            END as opponent_abbrev,
            p.full_name as player_name,
            p.position
        FROM game_player_statistics gps
        JOIN game g ON gps.game_id = g.game_id
        JOIN season s ON g.season_id = s.season_id
        JOIN player p ON gps.player_id = p.player_id
        JOIN team t ON gps.team_id = t.team_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        WHERE gps.player_id = %s
        {season_filter}
        {stat_group_filter}
        ORDER BY g.game_datetime_utc DESC
        LIMIT %s
    """
    
    params = [player_id]
    season_filter = ""
    stat_group_filter = ""
    
    if season:
        season_filter = "AND s.year = %s"
        params.append(season)
    
    if stat_group:
        stat_group_filter = "AND gps.stat_group = %s"
        params.append(stat_group)
    
    params.append(limit)
    
    query = query.format(
        season_filter=season_filter,
        stat_group_filter=stat_group_filter
    )
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No statistics found for player {player_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                stats = [dict(zip(columns, row)) for row in rows]
                
                # Group by game
                games_dict = {}
                player_name = stats[0]['player_name']
                position = stats[0]['position']
                
                for stat in stats:
                    game_id = stat['game_id']
                    if game_id not in games_dict:
                        games_dict[game_id] = {
                            'game_id': game_id,
                            'week': stat['week'],
                            'game_date': stat['game_datetime_utc'],
                            'season': stat['season'],
                            'team_name': stat['team_name'],
                            'team_abbrev': stat['team_abbrev'],
                            'opponent': stat['opponent_name'],
                            'opponent_abbrev': stat['opponent_abbrev'],
                            'stat_groups': {}
                        }
                    
                    stat_group = stat['stat_group']
                    if stat_group not in games_dict[game_id]['stat_groups']:
                        games_dict[game_id]['stat_groups'][stat_group] = []
                    
                    games_dict[game_id]['stat_groups'][stat_group].append({
                        'metric_name': stat['metric_name'],
                        'metric_value': stat['metric_value']
                    })
                
                return PlayerGameStatsResponse(
                    player_id=player_id,
                    player_name=player_name,
                    position=position,
                    season=season,
                    game_count=len(games_dict),
                    games=list(games_dict.values())
                )
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/players/leaders/{stat_group}/{metric_name}",
    response_model=List[StatLeaderItem],
    summary="Get Statistical Leaders"
)
async def get_player_stat_leaders(
    stat_group: str = Path(
        ...,
        description="Stat group (Passing, Rushing, Receiving, Defense, etc.)"
    ),
    metric_name: str = Path(
        ...,
        description="Metric name (e.g., 'yards', 'touchdowns', 'completions')"
    ),
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get statistical leaders for a specific stat category.
    
    Examples:
    - /players/leaders/Passing/yards?season=2023&limit=10
    - /players/leaders/Rushing/touchdowns?season=2023
    - /players/leaders/Receiving/receptions
    """
    # Note: This query assumes numeric values. For ratio values like "6/12",
    # we'll need to handle them differently or convert them.
    query = """
        WITH recent_games AS (
            SELECT DISTINCT g.game_id
            FROM game_player_statistics gps
            JOIN game g ON gps.game_id = g.game_id
            JOIN season s ON g.season_id = s.season_id
            WHERE gps.player_id = %s
            AND s.year = %s
            ORDER BY g.game_datetime_utc DESC
            LIMIT %s
        )
        SELECT
            gps.game_id,
            g.week,
            g.game_datetime_utc,
            s.year AS season,
            gps.stat_group,
            gps.metric_name,
            gps.metric_value,
            t.name AS team_name,
            t.abbrev AS team_abbrev,
            CASE
                WHEN gps.team_id = g.home_team_id THEN at.name
                ELSE ht.name
            END AS opponent_name,
            CASE
                WHEN gps.team_id = g.home_team_id THEN at.abbrev
                ELSE ht.abbrev
            END AS opponent_abbrev,
            p.full_name AS player_name,
            p.position
        FROM game_player_statistics gps
        JOIN recent_games rg ON gps.game_id = rg.game_id
        JOIN game g ON gps.game_id = g.game_id
        JOIN season s ON g.season_id = s.season_id
        JOIN player p ON gps.player_id = p.player_id
        JOIN team t ON gps.team_id = t.team_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        ORDER BY g.game_datetime_utc DESC;
    """
    
    params = []
    season_filter = ""
    
    if season:
        season_filter = "JOIN season s ON g.season_id = s.season_id WHERE s.year = %s"
        params.append(season)
    
    params.extend([stat_group, metric_name, limit])
    
    query = query.format(season_filter=season_filter)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    return []  # Return empty list instead of 404
                
                columns = [desc[0] for desc in cur.description]
                leaders = [dict(zip(columns, row)) for row in rows]
                
                return [StatLeaderItem(**leader) for leader in leaders]
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/players/{player_id}/summary",
    summary="Get Player Statistics Summary"
)
async def get_player_statistics_summary(
    player_id: int = Path(..., description="Player ID"),
    season: Optional[int] = Query(None, description="Filter by season")
):
    """
    Get aggregated statistics summary for a player.
    
    Groups all stats by stat_group and provides key metrics.
    """
    query = """
        SELECT 
            p.full_name as player_name,
            p.position,
            t.name as team_name,
            t.abbrev as team_abbrev,
            s.year as season,
            gps.stat_group,
            gps.metric_name,
            COUNT(*) as game_count,
            ARRAY_AGG(gps.metric_value ORDER BY g.game_datetime_utc DESC) as values
        FROM game_player_statistics gps
        JOIN player p ON gps.player_id = p.player_id
        JOIN team t ON gps.team_id = t.team_id
        JOIN game g ON gps.game_id = g.game_id
        JOIN season s ON g.season_id = s.season_id
        WHERE gps.player_id = %s
        {season_filter}
        GROUP BY 
            p.full_name, p.position, t.name, t.abbrev, 
            s.year, gps.stat_group, gps.metric_name
        ORDER BY s.year DESC, gps.stat_group, gps.metric_name
    """
    
    params = [player_id]
    season_filter = ""
    
    if season:
        season_filter = "AND s.year = %s"
        params.append(season)
    
    query = query.format(season_filter=season_filter)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No statistics found for player {player_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                stats = [dict(zip(columns, row)) for row in rows]
                
                # Group by season and stat_group
                result = {
                    'player_name': stats[0]['player_name'],
                    'position': stats[0]['position'],
                    'team_name': stats[0]['team_name'],
                    'team_abbrev': stats[0]['team_abbrev'],
                    'seasons': {}
                }
                
                for stat in stats:
                    season_key = stat['season']
                    if season_key not in result['seasons']:
                        result['seasons'][season_key] = {}
                    
                    stat_group = stat['stat_group']
                    if stat_group not in result['seasons'][season_key]:
                        result['seasons'][season_key][stat_group] = []
                    
                    result['seasons'][season_key][stat_group].append({
                        'metric_name': stat['metric_name'],
                        'game_count': stat['game_count'],
                        'recent_values': stat['values'][:5]  # Last 5 games
                    })
                
                return result
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# =========================================================
# Health Check
# =========================================================

@router.get("/games/player-stats/health", summary="Health Check")
async def health_check():
    """Check if the game player statistics endpoints are operational."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM game_player_statistics")
                count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT game_id) FROM game_player_statistics")
                game_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT player_id) FROM game_player_statistics")
                player_count = cur.fetchone()[0]
                
                return {
                    "status": "healthy",
                    "total_stat_records": count,
                    "games_with_stats": game_count,
                    "players_with_stats": player_count
                }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
