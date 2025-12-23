"""
Game Team Statistics API Endpoints
====================================
Provides endpoints for querying team performance statistics for individual games.

Endpoints:
- GET /statistics/games/{game_id}/teams - Get team stats for a specific game
- GET /statistics/teams/{team_id}/games - Get game-by-game stats for a team
- GET /statistics/teams/leaders - Get statistical leaders across all games
"""

from typing import Optional, List
from datetime import datetime
import psycopg2
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
import os

# Initialize router
router = APIRouter(prefix="/statistics", tags=["Game Team Statistics"])


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

class TeamStatistics(BaseModel):
    """Model for team statistics in a game."""
    stat_id: int
    game_id: int
    team_id: int
    team_name: str
    team_abbrev: str
    
    # First Downs
    first_downs_total: Optional[int]
    first_downs_passing: Optional[int]
    first_downs_rushing: Optional[int]
    first_downs_from_penalties: Optional[int]
    third_down_efficiency: Optional[str]
    fourth_down_efficiency: Optional[str]
    
    # Plays & Yards
    plays_total: Optional[int]
    yards_total: Optional[int]
    yards_per_play: Optional[float]
    total_drives: Optional[float]
    
    # Passing
    passing_yards: Optional[int]
    passing_comp_att: Optional[str]
    passing_yards_per_pass: Optional[float]
    passing_interceptions_thrown: Optional[int]
    passing_sacks_yards_lost: Optional[str]
    
    # Rushing
    rushing_yards: Optional[int]
    rushing_attempts: Optional[int]
    rushing_yards_per_rush: Optional[float]
    
    # Red Zone
    red_zone_made_att: Optional[str]
    
    # Penalties
    penalties_total: Optional[str]
    
    # Turnovers
    turnovers_total: Optional[int]
    turnovers_lost_fumbles: Optional[int]
    turnovers_interceptions: Optional[int]
    
    # Possession
    possession_total: Optional[str]
    
    # Defensive Stats
    interceptions_total: Optional[int]
    fumbles_recovered_total: Optional[int]
    sacks_total: Optional[int]
    safeties_total: Optional[int]
    int_touchdowns_total: Optional[int]
    points_against_total: Optional[int]
    
    pulled_at_utc: datetime


class GameTeamStatisticsResponse(BaseModel):
    """Response model for game statistics."""
    game_id: int
    week: int
    game_datetime_utc: datetime
    home_team: TeamStatistics
    away_team: TeamStatistics


class TeamGameStatsResponse(BaseModel):
    """Response model for team's game-by-game statistics."""
    team_id: int
    team_name: str
    season: Optional[int]
    game_count: int
    games: List[dict]


class StatLeader(BaseModel):
    """Model for statistical leaders."""
    team_id: int
    team_name: str
    team_abbrev: str
    game_id: int
    week: int
    opponent: str
    stat_value: Optional[int]
    game_date: datetime


# =========================================================
# Endpoints
# =========================================================

@router.get(
    "/games/{game_id}/teams",
    response_model=GameTeamStatisticsResponse,
    summary="Get Team Statistics for a Game"
)
async def get_game_team_statistics(
    game_id: int = Path(..., description="Game ID")
):
    """
    Get detailed team statistics for both teams in a specific game.
    
    Returns offensive, defensive, and special teams stats for home and away teams.
    """
    query = """
        SELECT 
            gts.*,
            t.name as team_name,
            t.abbrev as team_abbrev,
            g.week,
            g.game_datetime_utc,
            g.home_team_id,
            g.away_team_id
        FROM game_team_statistics gts
        JOIN team t ON gts.team_id = t.team_id
        JOIN game g ON gts.game_id = g.game_id
        WHERE gts.game_id = %s
        ORDER BY 
            CASE WHEN gts.team_id = g.home_team_id THEN 0 ELSE 1 END
    """
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (game_id,))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Statistics not found for game {game_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                stats = [dict(zip(columns, row)) for row in rows]
                
                if len(stats) != 2:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Expected 2 team records, found {len(stats)}"
                    )
                
                home_stats = stats[0]
                away_stats = stats[1]
                
                return GameTeamStatisticsResponse(
                    game_id=game_id,
                    week=home_stats['week'],
                    game_datetime_utc=home_stats['game_datetime_utc'],
                    home_team=TeamStatistics(**home_stats),
                    away_team=TeamStatistics(**away_stats)
                )
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/teams/{team_id}/games",
    response_model=TeamGameStatsResponse,
    summary="Get Game-by-Game Statistics for a Team"
)
async def get_team_game_statistics(
    team_id: int = Path(..., description="Team ID"),
    season: Optional[int] = Query(None, description="Filter by season year"),
    limit: int = Query(20, ge=1, le=100, description="Maximum games to return")
):
    """
    Get game-by-game statistics for a specific team.
    
    Optionally filter by season and limit the number of games returned.
    """
    query = """
        SELECT 
            gts.*,
            g.week,
            g.game_datetime_utc,
            g.home_team_id,
            g.away_team_id,
            s.year as season,
            ht.name as home_team_name,
            ht.abbrev as home_team_abbrev,
            at.name as away_team_name,
            at.abbrev as away_team_abbrev,
            gr.home_score,
            gr.away_score,
            t.name as team_name
        FROM game_team_statistics gts
        JOIN game g ON gts.game_id = g.game_id
        JOIN season s ON g.season_id = s.season_id
        JOIN team t ON gts.team_id = t.team_id
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        LEFT JOIN game_result gr ON g.game_id = gr.game_id
        WHERE gts.team_id = %s
        {season_filter}
        ORDER BY g.game_datetime_utc DESC
        LIMIT %s
    """
    
    params = [team_id]
    season_filter = ""
    
    if season:
        season_filter = "AND s.year = %s"
        params.append(season)
    
    params.append(limit)
    
    query = query.format(season_filter=season_filter)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No statistics found for team {team_id}"
                    )
                
                columns = [desc[0] for desc in cur.description]
                games_data = [dict(zip(columns, row)) for row in rows]
                
                # Format response
                team_name = games_data[0]['team_name']
                season_year = games_data[0]['season'] if season else None
                
                games = []
                for game in games_data:
                    is_home = game['team_id'] == game['home_team_id']
                    opponent = game['away_team_name'] if is_home else game['home_team_name']
                    opponent_abbrev = game['away_team_abbrev'] if is_home else game['home_team_abbrev']
                    
                    team_score = game['home_score'] if is_home else game['away_score']
                    opponent_score = game['away_score'] if is_home else game['home_score']
                    
                    games.append({
                        'game_id': game['game_id'],
                        'week': game['week'],
                        'game_date': game['game_datetime_utc'],
                        'is_home': is_home,
                        'opponent': opponent,
                        'opponent_abbrev': opponent_abbrev,
                        'team_score': team_score,
                        'opponent_score': opponent_score,
                        'result': 'W' if (team_score or 0) > (opponent_score or 0) else 'L' if team_score != opponent_score else 'T',
                        'total_yards': game['yards_total'],
                        'passing_yards': game['passing_yards'],
                        'rushing_yards': game['rushing_yards'],
                        'turnovers': game['turnovers_total'],
                        'points_against': game['points_against_total'],
                        'time_of_possession': game['possession_total']
                    })
                
                return TeamGameStatsResponse(
                    team_id=team_id,
                    team_name=team_name,
                    season=season_year,
                    game_count=len(games),
                    games=games
                )
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

"""
CORRECTED Team Endpoints - Add as SEPARATE functions to your backend
These are NEW endpoints, not modifications to existing ones!
"""

# ==================== ADD THESE AS NEW ENDPOINTS ====================

"""
CORRECTED Team Endpoints - Using game_result table
Add these 3 NEW endpoints to your backend
"""

from typing import Optional, List
from datetime import datetime
import psycopg2
from fastapi import APIRouter, HTTPException, Query, Path

# ==================== ADD THESE 3 NEW ENDPOINTS ====================

@router.get(
    "/teams/leaders/points",
    summary="Get Points Scored Leaders"
)
async def get_team_points_leaders(
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get team leaders for points scored per game.
    Uses game_result table for scores.
    """
    
    if season:
        query = """
            WITH team_games AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    g.game_id,
                    g.week,
                    g.game_datetime_utc,
                    CASE 
                        WHEN g.home_team_id = t.team_id THEN gr.home_score
                        WHEN g.away_team_id = t.team_id THEN gr.away_score
                    END as team_score
                FROM team t
                INNER JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                INNER JOIN game_result gr ON g.game_id = gr.game_id
                INNER JOIN season s ON g.season_id = s.season_id
                WHERE s.year = %s
            ),
            team_avg AS (
                SELECT 
                    team_id,
                    team_name,
                    team_abbrev,
                    ROUND(AVG(team_score), 1) as avg_points
                FROM team_games
                GROUP BY team_id, team_name, team_abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                avg_points::TEXT as stat_value,
                '' as opponent
            FROM team_avg
            WHERE avg_points IS NOT NULL
            ORDER BY avg_points DESC
            LIMIT %s
        """
        params = (season, limit)
    else:
        query = """
            WITH team_games AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    CASE 
                        WHEN g.home_team_id = t.team_id THEN gr.home_score
                        WHEN g.away_team_id = t.team_id THEN gr.away_score
                    END as team_score
                FROM team t
                INNER JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                INNER JOIN game_result gr ON g.game_id = gr.game_id
            ),
            team_avg AS (
                SELECT 
                    team_id,
                    team_name,
                    team_abbrev,
                    ROUND(AVG(team_score), 1) as avg_points
                FROM team_games
                GROUP BY team_id, team_name, team_abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                avg_points::TEXT as stat_value,
                '' as opponent
            FROM team_avg
            WHERE avg_points IS NOT NULL
            ORDER BY avg_points DESC
            LIMIT %s
        """
        params = (limit,)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                columns = [desc[0] for desc in cur.description]
                leaders = [dict(zip(columns, row)) for row in rows]
                
                return leaders
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/teams/leaders/points_allowed",
    summary="Get Points Allowed Leaders"
)
async def get_team_points_allowed_leaders(
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get team leaders for points allowed (best defense).
    Uses game_result table for scores.
    """
    
    if season:
        query = """
            WITH team_games AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    g.game_id,
                    g.week,
                    g.game_datetime_utc,
                    CASE 
                        WHEN g.home_team_id = t.team_id THEN gr.away_score
                        WHEN g.away_team_id = t.team_id THEN gr.home_score
                    END as points_allowed
                FROM team t
                INNER JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                INNER JOIN game_result gr ON g.game_id = gr.game_id
                INNER JOIN season s ON g.season_id = s.season_id
                WHERE s.year = %s
            ),
            team_avg AS (
                SELECT 
                    team_id,
                    team_name,
                    team_abbrev,
                    ROUND(AVG(points_allowed), 1) as avg_points_allowed
                FROM team_games
                GROUP BY team_id, team_name, team_abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                avg_points_allowed::TEXT as stat_value,
                '' as opponent
            FROM team_avg
            WHERE avg_points_allowed IS NOT NULL
            ORDER BY avg_points_allowed ASC
            LIMIT %s
        """
        params = (season, limit)
    else:
        query = """
            WITH team_games AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    CASE 
                        WHEN g.home_team_id = t.team_id THEN gr.away_score
                        WHEN g.away_team_id = t.team_id THEN gr.home_score
                    END as points_allowed
                FROM team t
                INNER JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                INNER JOIN game_result gr ON g.game_id = gr.game_id
            ),
            team_avg AS (
                SELECT 
                    team_id,
                    team_name,
                    team_abbrev,
                    ROUND(AVG(points_allowed), 1) as avg_points_allowed
                FROM team_games
                GROUP BY team_id, team_name, team_abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                avg_points_allowed::TEXT as stat_value,
                '' as opponent
            FROM team_avg
            WHERE avg_points_allowed IS NOT NULL
            ORDER BY avg_points_allowed ASC
            LIMIT %s
        """
        params = (limit,)
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                
                columns = [desc[0] for desc in cur.description]
                leaders = [dict(zip(columns, row)) for row in rows]
                
                return leaders
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.get(
    "/teams/leaders/{stat_category}",
    response_model=List[StatLeader],
    summary="Get Statistical Leaders"
)
async def get_stat_leaders(
    stat_category: str = Path(
        ...,
        description="Stat category (e.g., 'yards_total', 'passing_yards', 'rushing_yards', 'sacks_total')"
    ),
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get statistical leaders for a specific category.
    
    Available categories:
    - yards_total: Total yards
    - passing_yards: Passing yards
    - rushing_yards: Rushing yards
    - first_downs_total: First downs
    - sacks_total: Sacks (defensive)
    - turnovers_total: Turnovers forced
    - points_against_total: Points allowed
    """
    # Validate stat category (basic SQL injection prevention)
    valid_stats = [
        'yards_total', 'passing_yards', 'rushing_yards', 'first_downs_total',
        'sacks_total', 'turnovers_total', 'points_against_total', 'plays_total',
        'interceptions_total', 'fumbles_recovered_total'
    ]
    
    if stat_category not in valid_stats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stat category. Must be one of: {', '.join(valid_stats)}"
        )
    
    # Build the query with proper WHERE clause handling
    if season:
        query = f"""
            SELECT 
                gts.team_id,
                t.name as team_name,
                t.abbrev as team_abbrev,
                gts.game_id,
                g.week,
                g.game_datetime_utc as game_date,
                gts.{stat_category} as stat_value,
                CASE 
                    WHEN gts.team_id = g.home_team_id THEN at.name
                    ELSE ht.name
                END as opponent
            FROM game_team_statistics gts
            JOIN game g ON gts.game_id = g.game_id
            JOIN season s ON g.season_id = s.season_id
            JOIN team t ON gts.team_id = t.team_id
            JOIN team ht ON g.home_team_id = ht.team_id
            JOIN team at ON g.away_team_id = at.team_id
            WHERE s.year = %s
              AND gts.{stat_category} IS NOT NULL
            ORDER BY gts.{stat_category} DESC
            LIMIT %s
        """
        params = [season, limit]
    else:
        query = f"""
            SELECT 
                gts.team_id,
                t.name as team_name,
                t.abbrev as team_abbrev,
                gts.game_id,
                g.week,
                g.game_datetime_utc as game_date,
                gts.{stat_category} as stat_value,
                CASE 
                    WHEN gts.team_id = g.home_team_id THEN at.name
                    ELSE ht.name
                END as opponent
            FROM game_team_statistics gts
            JOIN game g ON gts.game_id = g.game_id
            JOIN team t ON gts.team_id = t.team_id
            JOIN team ht ON g.home_team_id = ht.team_id
            JOIN team at ON g.away_team_id = at.team_id
            WHERE gts.{stat_category} IS NOT NULL
            ORDER BY gts.{stat_category} DESC
            LIMIT %s
        """
        params = [limit]
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                columns = [desc[0] for desc in cur.description]
                leaders = [dict(zip(columns, row)) for row in rows]
                
                return [StatLeader(**leader) for leader in leaders]
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

# NFL Division mapping helper
def get_team_conference_division(team_abbrev: str) -> tuple:
    """Returns (conference, division) for a team."""
    
    team_mapping = {
        'BUF': ('AFC', 'AFC East'), 'MIA': ('AFC', 'AFC East'),
        'NE': ('AFC', 'AFC East'), 'NYJ': ('AFC', 'AFC East'),
        'BAL': ('AFC', 'AFC North'), 'CIN': ('AFC', 'AFC North'),
        'CLE': ('AFC', 'AFC North'), 'PIT': ('AFC', 'AFC North'),
        'HOU': ('AFC', 'AFC South'), 'IND': ('AFC', 'AFC South'),
        'JAX': ('AFC', 'AFC South'), 'TEN': ('AFC', 'AFC South'),
        'DEN': ('AFC', 'AFC West'), 'KC': ('AFC', 'AFC West'),
        'LV': ('AFC', 'AFC West'), 'LAC': ('AFC', 'AFC West'),
        'DAL': ('NFC', 'NFC East'), 'NYG': ('NFC', 'NFC East'),
        'PHI': ('NFC', 'NFC East'), 'WAS': ('NFC', 'NFC East'),
        'CHI': ('NFC', 'NFC North'), 'DET': ('NFC', 'NFC North'),
        'GB': ('NFC', 'NFC North'), 'MIN': ('NFC', 'NFC North'),
        'ATL': ('NFC', 'NFC South'), 'CAR': ('NFC', 'NFC South'),
        'NO': ('NFC', 'NFC South'), 'TB': ('NFC', 'NFC South'),
        'ARI': ('NFC', 'NFC West'), 'LAR': ('NFC', 'NFC West'),
        'SF': ('NFC', 'NFC West'), 'SEA': ('NFC', 'NFC West'),
    }
    
    return team_mapping.get(team_abbrev, ('Unknown', 'Unknown'))


@router.get(
    "/teams/{team_id}/standings",
    summary="Get Team Conference and Division Rankings"
)
async def get_team_standings(
    team_id: int = Path(..., description="Team ID"),
    season: int = Query(..., description="Season year")
):
    """
    Get team's conference and division rankings.
    Uses game_result table for scores.
    """
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get team info
                cur.execute(
                    "SELECT name, abbrev FROM team WHERE team_id = %s",
                    (team_id,)
                )
                team_row = cur.fetchone()
                
                if not team_row:
                    raise HTTPException(status_code=404, detail="Team not found")
                
                team_name, team_abbrev = team_row
                conference, division = get_team_conference_division(team_abbrev)
                
                # Calculate standings using game_result table
                query = """
                    WITH team_records AS (
                        SELECT 
                            t.team_id,
                            t.name,
                            t.abbrev,
                            COUNT(g.game_id) as games_played,
                            SUM(CASE 
                                WHEN (g.home_team_id = t.team_id AND gr.home_score > gr.away_score) OR
                                     (g.away_team_id = t.team_id AND gr.away_score > gr.home_score)
                                THEN 1 ELSE 0 
                            END) as wins,
                            SUM(CASE 
                                WHEN (g.home_team_id = t.team_id AND gr.home_score < gr.away_score) OR
                                     (g.away_team_id = t.team_id AND gr.away_score < gr.home_score)
                                THEN 1 ELSE 0 
                            END) as losses,
                            SUM(CASE 
                                WHEN gr.home_score = gr.away_score THEN 1 ELSE 0 
                            END) as ties
                        FROM team t
                        INNER JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                        INNER JOIN game_result gr ON g.game_id = gr.game_id
                        INNER JOIN season s ON g.season_id = s.season_id
                        WHERE s.year = %s
                        GROUP BY t.team_id, t.name, t.abbrev
                    )
                    SELECT 
                        team_id,
                        name,
                        abbrev,
                        wins,
                        losses,
                        ties,
                        games_played,
                        CASE 
                            WHEN games_played > 0 
                            THEN (wins + ties * 0.5) / games_played 
                            ELSE 0 
                        END as win_pct
                    FROM team_records
                    ORDER BY win_pct DESC, wins DESC
                """
                
                cur.execute(query, (season,))
                all_standings = cur.fetchall()
                
                # Calculate ranks
                conference_teams = []
                division_teams = []
                
                for row in all_standings:
                    tid, name, abbrev, wins, losses, ties, gp, win_pct = row
                    team_conf, team_div = get_team_conference_division(abbrev)
                    
                    if team_conf == conference:
                        conference_teams.append((tid, float(win_pct or 0)))
                    
                    if team_div == division:
                        division_teams.append((tid, float(win_pct or 0)))
                
                # Sort and find ranks
                conference_teams.sort(key=lambda x: x[1], reverse=True)
                division_teams.sort(key=lambda x: x[1], reverse=True)
                
                conference_rank = next((i + 1 for i, (tid, _) in enumerate(conference_teams) if tid == team_id), None)
                division_rank = next((i + 1 for i, (tid, _) in enumerate(division_teams) if tid == team_id), None)
                
                return {
                    "team_id": team_id,
                    "team_name": team_name,
                    "team_abbrev": team_abbrev,
                    "season": season,
                    "conference": conference,
                    "division": division,
                    "conference_rank": conference_rank,
                    "division_rank": division_rank,
                    "total_conference_teams": len(conference_teams),
                    "total_division_teams": len(division_teams)
                }
                
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )