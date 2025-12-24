"""
Game Player Statistics API Endpoints
=====================================
Provides endpoints for querying individual player performance statistics for games.

Endpoints:
- GET /statistics/games/{game_id}/players - Get player stats for a specific game
- GET /statistics/players/{player_id}/games - Get game-by-game stats for a player
- GET /statistics/players/leaders/{stat_group}/{metric} - Get statistical leaders
- GET /statistics/players/{player_id}/rankings - Get player's season rankings (NEW)
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


class PlayerRankingItem(BaseModel):
    """Model for a player's ranking in a specific metric."""
    metric_name: str
    stat_group: str
    total_value: float
    rank: int
    total_players: int
    percentile: float


class PlayerRankingsResponse(BaseModel):
    """Response model for player's season rankings."""
    player_id: int
    player_name: str
    position: str
    season: int
    rankings: List[PlayerRankingItem]


# =========================================================
# Endpoints
# =========================================================

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
        WITH recent_games AS (
            SELECT
                g.game_id,
                g.game_datetime_utc
            FROM game_player_statistics gps
            JOIN game g ON gps.game_id = g.game_id
            JOIN season s ON g.season_id = s.season_id
            WHERE gps.player_id = %s
            AND s.year = %s
            GROUP BY g.game_id, g.game_datetime_utc
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
        WHERE gps.player_id = %s          -- 🔥 THIS WAS MISSING
        ORDER BY rg.game_datetime_utc DESC;
    """
    
    params = [player_id, season, limit, player_id]
    
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
    # Build the base query
    base_query = """
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
        LEFT JOIN team ht ON g.home_team_id = ht.team_id
        LEFT JOIN team at ON g.away_team_id = at.team_id
        WHERE gps.player_id = %s
    """
    
    params = [player_id]
    filters = []
    
    if season:
        filters.append("s.year = %s")
        params.append(season)
    
    if stat_group:
        filters.append("gps.stat_group = %s")
        params.append(stat_group)
    
    if filters:
        base_query += " AND " + " AND ".join(filters)
    
    base_query += """
        ORDER BY g.game_datetime_utc DESC, gps.stat_group, gps.metric_name
        LIMIT %s
    """
    params.append(limit)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(base_query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No statistics found for player {player_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                stats = [dict(zip(columns, row)) for row in rows]
                
                # Extract player info
                player_name = stats[0]['player_name']
                position = stats[0]['position']
                
                # Group by game
                games_dict = {}
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
    "/players/{player_id}/rankings",
    response_model=PlayerRankingsResponse,
    summary="Get Player Season Rankings by Position"
)
async def get_player_season_rankings(
    player_id: int = Path(..., description="Player ID"),
    season: int = Query(..., description="Season year"),
    position: Optional[str] = Query(None, description="Override position for comparison")
):
    """
    Get a player's rankings across all relevant metrics for their position.
    
    Compares the player against all other players at the same position for the season.
    Returns rankings for metrics where the player ranks in the top 10.
    
    Examples:
    - /statistics/players/1349/rankings?season=2023
    - /statistics/players/1349/rankings?season=2023&position=QB
    """
    
    # First, get the player's position
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT full_name, position FROM player WHERE player_id = %s",
                    (player_id,)
                )
                player_row = cur.fetchone()
                
                if not player_row:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Player {player_id} not found"
                    )
                
                player_name = player_row[0]
                player_position = position or player_row[1]
                
                if not player_position:
                    raise HTTPException(
                        status_code=400,
                        detail="Player position is required"
                    )
                
                # Define relevant stat groups and metrics by position
                position_metrics = {
                    'QB': {
                        'Passing': ['yards', 'passing touch downs', 'rating', 'interceptions', 'comp att']
                    },
                    'RB': {
                        'Rushing': ['yards', 'rushing touch downs', 'average', 'total rushes'],
                        'Receiving': ['yards', 'receiving touch downs', 'receptions']
                    },
                    'WR': {
                        'Receiving': ['yards', 'receiving touch downs', 'receptions', 'targets']
                    },
                    'TE': {
                        'Receiving': ['yards', 'receiving touch downs', 'receptions', 'targets']
                    },
                    'K': {
                        'Kicking': ['field goals made', 'field goal pct', 'extra points made']
                    },
                    'P': {
                        'Punting': ['average', 'gross avg', 'inside 20']
                    },
                    'DB': {
                        'Defense': ['tackles', 'interceptions', 'passes defended']
                    },
                    'CB': {
                        'Defense': ['tackles', 'interceptions', 'passes defended']
                    },
                    'S': {
                        'Defense': ['tackles', 'interceptions', 'passes defended']
                    },
                    'LB': {
                        'Defense': ['tackles', 'sacks', 'tfl']
                    },
                    'DL': {
                        'Defense': ['tackles', 'sacks', 'tfl']
                    },
                    'DE': {
                        'Defense': ['tackles', 'sacks', 'tfl', 'qb hts']
                    },
                    'DT': {
                        'Defense': ['tackles', 'sacks', 'tfl']
                    }
                }
                
                # Get metrics for this position
                metrics_to_check = position_metrics.get(player_position, {})
                
                if not metrics_to_check:
                    return PlayerRankingsResponse(
                        player_id=player_id,
                        player_name=player_name,
                        position=player_position,
                        season=season,
                        rankings=[]
                    )
                
                rankings = []
                
                # For each stat group and metric, calculate rankings
                for stat_group, metrics in metrics_to_check.items():
                    for metric_name in metrics:
                        # Query to calculate season totals and rank players
                        ranking_query = """
                            WITH player_totals AS (
                                SELECT 
                                    gps.player_id,
                                    p.full_name,
                                    p.position,
                                    SUM(
                                        CASE 
                                            WHEN gps.metric_value ~ '^[0-9]+(\.[0-9]+)?$' 
                                            THEN CAST(gps.metric_value AS NUMERIC)
                                            WHEN gps.metric_value ~ '^[0-9]+/'
                                            THEN CAST(SPLIT_PART(gps.metric_value, '/', 1) AS NUMERIC)
                                            WHEN gps.metric_value ~ '^[0-9]+-'
                                            THEN CAST(SPLIT_PART(gps.metric_value, '-', 1) AS NUMERIC)
                                            ELSE 0
                                        END
                                    ) as total_value,
                                    COUNT(DISTINCT gps.game_id) as game_count
                                FROM game_player_statistics gps
                                JOIN player p ON gps.player_id = p.player_id
                                JOIN game g ON gps.game_id = g.game_id
                                JOIN season s ON g.season_id = s.season_id
                                WHERE s.year = %s
                                  AND p.position = %s
                                  AND gps.stat_group = %s
                                  AND gps.metric_name = %s
                                  AND gps.metric_value IS NOT NULL
                                GROUP BY gps.player_id, p.full_name, p.position
                                HAVING SUM(
                                    CASE 
                                        WHEN gps.metric_value ~ '^[0-9]+(\.[0-9]+)?$' 
                                        THEN CAST(gps.metric_value AS NUMERIC)
                                        WHEN gps.metric_value ~ '^[0-9]+/'
                                        THEN CAST(SPLIT_PART(gps.metric_value, '/', 1) AS NUMERIC)
                                        WHEN gps.metric_value ~ '^[0-9]+-'
                                        THEN CAST(SPLIT_PART(gps.metric_value, '-', 1) AS NUMERIC)
                                        ELSE 0
                                    END
                                ) > 0
                            ),
                            ranked_players AS (
                                SELECT 
                                    player_id,
                                    full_name,
                                    position,
                                    total_value,
                                    game_count,
                                    RANK() OVER (ORDER BY total_value DESC) as rank,
                                    COUNT(*) OVER () as total_players
                                FROM player_totals
                            )
                            SELECT 
                                player_id,
                                full_name,
                                position,
                                total_value,
                                rank,
                                total_players
                            FROM ranked_players
                            WHERE player_id = %s
                        """
                        
                        cur.execute(
                            ranking_query,
                            (season, player_position, stat_group, metric_name, player_id)
                        )
                        
                        result = cur.fetchone()
                        
                        if result and result[4] <= 10:  # Only include top 10 rankings
                            rankings.append(PlayerRankingItem(
                                metric_name=metric_name,
                                stat_group=stat_group,
                                total_value=float(result[3]),
                                rank=int(result[4]),
                                total_players=int(result[5]),
                                percentile=round((1 - (result[4] / result[5])) * 100, 1)
                            ))
                
                # Sort by rank (best rankings first)
                rankings.sort(key=lambda x: x.rank)
                
                return PlayerRankingsResponse(
                    player_id=player_id,
                    player_name=player_name,
                    position=player_position,
                    season=season,
                    rankings=rankings
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
    query = """
        SELECT 
            gps.player_id,
            p.full_name as player_name,
            p.position,
            t.name as team_name,
            t.abbrev as team_abbrev,
            gps.game_id,
            g.week,
            g.game_datetime_utc as game_date,
            gps.metric_value
        FROM game_player_statistics gps
        JOIN player p ON gps.player_id = p.player_id
        JOIN team t ON gps.team_id = t.team_id
        JOIN game g ON gps.game_id = g.game_id
        {season_filter}
        WHERE gps.stat_group = %s
          AND gps.metric_name = %s
          AND gps.metric_value IS NOT NULL
          AND gps.metric_value ~ '^[0-9]+(\.[0-9]+)?$'
        ORDER BY CAST(gps.metric_value AS NUMERIC) DESC
        LIMIT %s
    """
    
    params = []
    season_filter = ""
    
    if season:
        season_filter = "JOIN season s ON g.season_id = s.season_id WHERE s.year = %s AND"
        params.append(season)
    else:
        season_filter = "WHERE"
    
    params.extend([stat_group, metric_name, limit])
    
    query = query.format(season_filter=season_filter)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    return []
                
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
