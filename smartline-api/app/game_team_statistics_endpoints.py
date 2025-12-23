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

# Add these new endpoints to game_team_statistics_endpoints.py

@router.get(
    "/teams/leaders/points",
    response_model=List[StatLeader],
    summary="Get Points Scored Leaders"
)
async def get_points_leaders(
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get team leaders for points scored (calculated from game results).
    This aggregates team_score from the games table.
    """
    
    if season:
        query = """
            WITH team_points AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    SUM(
                        CASE 
                            WHEN g.home_team_id = t.team_id THEN g.home_score
                            WHEN g.away_team_id = t.team_id THEN g.away_score
                            ELSE 0
                        END
                    ) as total_points,
                    COUNT(DISTINCT g.game_id) as games_played,
                    ROUND(
                        SUM(
                            CASE 
                                WHEN g.home_team_id = t.team_id THEN g.home_score
                                WHEN g.away_team_id = t.team_id THEN g.away_score
                                ELSE 0
                            END
                        )::NUMERIC / NULLIF(COUNT(DISTINCT g.game_id), 0), 1
                    ) as points_per_game
                FROM team t
                JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                JOIN season s ON g.season_id = s.season_id
                WHERE s.year = %s
                  AND g.home_score IS NOT NULL
                  AND g.away_score IS NOT NULL
                GROUP BY t.team_id, t.name, t.abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                points_per_game::TEXT as stat_value,
                '' as opponent
            FROM team_points
            ORDER BY points_per_game DESC
            LIMIT %s
        """
        params = [season, limit]
    else:
        query = """
            WITH team_points AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    SUM(
                        CASE 
                            WHEN g.home_team_id = t.team_id THEN g.home_score
                            WHEN g.away_team_id = t.team_id THEN g.away_score
                            ELSE 0
                        END
                    ) as total_points,
                    COUNT(DISTINCT g.game_id) as games_played,
                    ROUND(
                        SUM(
                            CASE 
                                WHEN g.home_team_id = t.team_id THEN g.home_score
                                WHEN g.away_team_id = t.team_id THEN g.away_score
                                ELSE 0
                            END
                        )::NUMERIC / NULLIF(COUNT(DISTINCT g.game_id), 0), 1
                    ) as points_per_game
                FROM team t
                JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                WHERE g.home_score IS NOT NULL
                  AND g.away_score IS NOT NULL
                GROUP BY t.team_id, t.name, t.abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                points_per_game::TEXT as stat_value,
                '' as opponent
            FROM team_points
            ORDER BY points_per_game DESC
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


@router.get(
    "/teams/leaders/points_allowed",
    response_model=List[StatLeader],
    summary="Get Points Allowed Leaders"
)
async def get_points_allowed_leaders(
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """
    Get team leaders for points allowed (calculated from game results).
    Lower is better (best defenses).
    """
    
    if season:
        query = """
            WITH team_points_allowed AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    SUM(
                        CASE 
                            WHEN g.home_team_id = t.team_id THEN g.away_score
                            WHEN g.away_team_id = t.team_id THEN g.home_score
                            ELSE 0
                        END
                    ) as total_points_allowed,
                    COUNT(DISTINCT g.game_id) as games_played,
                    ROUND(
                        SUM(
                            CASE 
                                WHEN g.home_team_id = t.team_id THEN g.away_score
                                WHEN g.away_team_id = t.team_id THEN g.home_score
                                ELSE 0
                            END
                        )::NUMERIC / NULLIF(COUNT(DISTINCT g.game_id), 0), 1
                    ) as points_allowed_per_game
                FROM team t
                JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                JOIN season s ON g.season_id = s.season_id
                WHERE s.year = %s
                  AND g.home_score IS NOT NULL
                  AND g.away_score IS NOT NULL
                GROUP BY t.team_id, t.name, t.abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                points_allowed_per_game::TEXT as stat_value,
                '' as opponent
            FROM team_points_allowed
            ORDER BY points_allowed_per_game ASC
            LIMIT %s
        """
        params = [season, limit]
    else:
        query = """
            WITH team_points_allowed AS (
                SELECT 
                    t.team_id,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    SUM(
                        CASE 
                            WHEN g.home_team_id = t.team_id THEN g.away_score
                            WHEN g.away_team_id = t.team_id THEN g.home_score
                            ELSE 0
                        END
                    ) as total_points_allowed,
                    COUNT(DISTINCT g.game_id) as games_played,
                    ROUND(
                        SUM(
                            CASE 
                                WHEN g.home_team_id = t.team_id THEN g.away_score
                                WHEN g.away_team_id = t.team_id THEN g.home_score
                                ELSE 0
                            END
                        )::NUMERIC / NULLIF(COUNT(DISTINCT g.game_id), 0), 1
                    ) as points_allowed_per_game
                FROM team t
                JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                WHERE g.home_score IS NOT NULL
                  AND g.away_score IS NOT NULL
                GROUP BY t.team_id, t.name, t.abbrev
            )
            SELECT 
                team_id,
                team_name,
                team_abbrev,
                0 as game_id,
                0 as week,
                NOW() as game_date,
                points_allowed_per_game::TEXT as stat_value,
                '' as opponent
            FROM team_points_allowed
            ORDER BY points_allowed_per_game ASC
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


# Helper function to determine conference and division from team abbreviation
def get_team_conference_division(team_abbrev: str) -> tuple:
    """Returns (conference, division) for a team based on their abbreviation."""
    
    # NFL Conference and Division mapping
    team_mapping = {
        # AFC East
        'BUF': ('AFC', 'AFC East'),
        'MIA': ('AFC', 'AFC East'),
        'NE': ('AFC', 'AFC East'),
        'NYJ': ('AFC', 'AFC East'),
        
        # AFC North
        'BAL': ('AFC', 'AFC North'),
        'CIN': ('AFC', 'AFC North'),
        'CLE': ('AFC', 'AFC North'),
        'PIT': ('AFC', 'AFC North'),
        
        # AFC South
        'HOU': ('AFC', 'AFC South'),
        'IND': ('AFC', 'AFC South'),
        'JAX': ('AFC', 'AFC South'),
        'TEN': ('AFC', 'AFC South'),
        
        # AFC West
        'DEN': ('AFC', 'AFC West'),
        'KC': ('AFC', 'AFC West'),
        'LV': ('AFC', 'AFC West'),
        'LAC': ('AFC', 'AFC West'),
        
        # NFC East
        'DAL': ('NFC', 'NFC East'),
        'NYG': ('NFC', 'NFC East'),
        'PHI': ('NFC', 'NFC East'),
        'WAS': ('NFC', 'NFC East'),
        
        # NFC North
        'CHI': ('NFC', 'NFC North'),
        'DET': ('NFC', 'NFC North'),
        'GB': ('NFC', 'NFC North'),
        'MIN': ('NFC', 'NFC North'),
        
        # NFC South
        'ATL': ('NFC', 'NFC South'),
        'CAR': ('NFC', 'NFC South'),
        'NO': ('NFC', 'NFC South'),
        'TB': ('NFC', 'NFC South'),
        
        # NFC West
        'ARI': ('NFC', 'NFC West'),
        'LAR': ('NFC', 'NFC West'),
        'SF': ('NFC', 'NFC West'),
        'SEA': ('NFC', 'NFC West'),
    }
    
    return team_mapping.get(team_abbrev, ('Unknown', 'Unknown'))


@router.get(
    "/teams/{team_id}/standings",
    summary="Get Team Standings Info"
)
async def get_team_standings(
    team_id: int = Path(..., description="Team ID"),
    season: int = Query(..., description="Season year")
):
    """
    Get team's conference rank and division rank for a season.
    Returns the team's position in their conference and division based on win percentage.
    """
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # First get the team info
                cur.execute(
                    "SELECT name, abbrev FROM team WHERE team_id = %s",
                    (team_id,)
                )
                team_row = cur.fetchone()
                
                if not team_row:
                    raise HTTPException(status_code=404, detail="Team not found")
                
                team_name = team_row[0]
                team_abbrev = team_row[1]
                
                conference, division = get_team_conference_division(team_abbrev)
                
                # Calculate standings for all teams in the season
                standings_query = """
                    WITH team_records AS (
                        SELECT 
                            t.team_id,
                            t.name,
                            t.abbrev,
                            COUNT(DISTINCT g.game_id) as games_played,
                            SUM(
                                CASE 
                                    WHEN (g.home_team_id = t.team_id AND g.home_score > g.away_score) OR
                                         (g.away_team_id = t.team_id AND g.away_score > g.home_score)
                                    THEN 1 ELSE 0
                                END
                            ) as wins,
                            SUM(
                                CASE 
                                    WHEN (g.home_team_id = t.team_id AND g.home_score < g.away_score) OR
                                         (g.away_team_id = t.team_id AND g.away_score < g.home_score)
                                    THEN 1 ELSE 0
                                END
                            ) as losses,
                            SUM(
                                CASE 
                                    WHEN g.home_score = g.away_score
                                    THEN 1 ELSE 0
                                END
                            ) as ties
                        FROM team t
                        JOIN game g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                        JOIN season s ON g.season_id = s.season_id
                        WHERE s.year = %s
                          AND g.home_score IS NOT NULL
                          AND g.away_score IS NOT NULL
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
                        ROUND((wins::NUMERIC + ties::NUMERIC * 0.5) / NULLIF(games_played, 0), 3) as win_pct
                    FROM team_records
                    ORDER BY win_pct DESC, wins DESC
                """
                
                cur.execute(standings_query, (season,))
                all_standings = cur.fetchall()
                
                # Calculate conference and division ranks
                conference_rank = None
                division_rank = None
                
                conference_teams = []
                division_teams = []
                
                for idx, row in enumerate(all_standings):
                    tid, name, abbrev, wins, losses, ties, gp, win_pct = row
                    team_conf, team_div = get_team_conference_division(abbrev)
                    
                    if team_conf == conference:
                        conference_teams.append((tid, win_pct))
                        if tid == team_id:
                            conference_rank = len(conference_teams)
                    
                    if team_div == division:
                        division_teams.append((tid, win_pct))
                        if tid == team_id:
                            division_rank = len(division_teams)
                
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

# =========================================================
# Health Check
# =========================================================

@router.get("/games/stats/health", summary="Health Check")
async def health_check():
    """Check if the game statistics endpoints are operational."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM game_team_statistics")
                count = cur.fetchone()[0]
                
                return {
                    "status": "healthy",
                    "total_stat_records": count
                }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
