"""
FastAPI Integration Example
============================
Example endpoints for integrating the Player ETL with your existing FastAPI backend.

Add these to your main.py to expose player data and ETL functionality via REST API.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Import your ETL components
from nfl_player_etl import ETLConfig, PlayerETL


# ==================== Database Connection ====================

def get_conn():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )


# ==================== Player Endpoints ====================

def get_all_players(conn, limit: int = 100, offset: int = 0, position: Optional[str] = None):
    """
    Get all players with optional filtering
    
    Args:
        conn: Database connection
        limit: Number of players to return
        offset: Number of players to skip
        position: Filter by position (QB, RB, WR, etc.)
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build query
    base_query = """
        SELECT 
            p.player_id,
            p.external_player_id,
            p.full_name,
            p.position,
            p.jersey_number,
            p.height,
            p.weight,
            p.age,
            p.college,
            p.experience_years,
            p.salary,
            p.image_url,
            p.player_group,
            t.name as team_name,
            t.abbrev as team_abbrev,
            t.team_id
        FROM player p
        LEFT JOIN team t ON p.team_id = t.team_id
    """
    
    # Add position filter if provided
    where_clause = ""
    params = []
    if position:
        where_clause = " WHERE p.position = %s"
        params.append(position)
    
    # Add pagination
    query = f"{base_query}{where_clause} ORDER BY p.full_name LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    players = cursor.fetchall()
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM player p{where_clause}"
    cursor.execute(count_query, params[:1] if position else [])
    total = cursor.fetchone()['count']
    
    cursor.close()
    
    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'players': players
    }


def get_player_by_id(conn, player_id: int):
    """Get a specific player by ID"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT 
            p.*,
            t.name as team_name,
            t.abbrev as team_abbrev,
            t.city as team_city
        FROM player p
        LEFT JOIN team t ON p.team_id = t.team_id
        WHERE p.player_id = %s
    """
    
    cursor.execute(query, (player_id,))
    player = cursor.fetchone()
    cursor.close()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player


def get_players_by_team(conn, team_id: int):
    """Get all players for a specific team"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT 
            p.player_id,
            p.full_name,
            p.position,
            p.jersey_number,
            p.height,
            p.weight,
            p.age,
            p.college,
            p.experience_years,
            p.player_group,
            p.image_url
        FROM player p
        WHERE p.team_id = %s
        ORDER BY 
            CASE p.position
                WHEN 'QB' THEN 1
                WHEN 'RB' THEN 2
                WHEN 'WR' THEN 3
                WHEN 'TE' THEN 4
                WHEN 'OL' THEN 5
                ELSE 99
            END,
            p.full_name
    """
    
    cursor.execute(query, (team_id,))
    players = cursor.fetchall()
    cursor.close()
    
    return {'team_id': team_id, 'players': players}


def search_players(conn, query: str, limit: int = 20):
    """Search players by name"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    search_query = """
        SELECT 
            p.player_id,
            p.full_name,
            p.position,
            p.jersey_number,
            t.name as team_name,
            t.abbrev as team_abbrev,
            p.image_url
        FROM player p
        LEFT JOIN team t ON p.team_id = t.team_id
        WHERE p.full_name ILIKE %s
        ORDER BY p.full_name
        LIMIT %s
    """
    
    cursor.execute(search_query, (f'%{query}%', limit))
    players = cursor.fetchall()
    cursor.close()
    
    return {'query': query, 'results': players}


# ==================== FastAPI Route Definitions ====================

app = FastAPI()  # Use your existing app instance

@app.get("/players")
def api_get_players(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    position: Optional[str] = Query(default=None)
):
    """
    Get all players with pagination and optional position filter
    
    Query Parameters:
    - limit: Number of results to return (1-500, default 100)
    - offset: Number of results to skip (default 0)
    - position: Filter by position (e.g., QB, RB, WR)
    
    Example:
    - GET /players?limit=20&offset=0&position=QB
    """
    conn = get_db_connection()  # Use your existing connection method
    try:
        result = get_all_players(conn, limit, offset, position)
        return result
    finally:
        conn.close()


@app.get("/players/{player_id}")
def api_get_player(player_id: int):
    """
    Get detailed information for a specific player
    
    Example:
    - GET /players/42
    """
    conn = get_db_connection()
    try:
        player = get_player_by_id(conn, player_id)
        return player
    finally:
        conn.close()


@app.get("/teams/{team_id}/players")
def api_get_team_players(team_id: int):
    """
    Get all players on a specific team
    
    Example:
    - GET /teams/1/players
    """
    conn = get_db_connection()
    try:
        result = get_players_by_team(conn, team_id)
        return result
    finally:
        conn.close()


@app.get("/players/search")
def api_search_players(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Search for players by name
    
    Query Parameters:
    - q: Search query (minimum 2 characters)
    - limit: Maximum results to return (default 20)
    
    Example:
    - GET /players/search?q=mahomes
    """
    conn = get_db_connection()
    try:
        result = search_players(conn, q, limit)
        return result
    finally:
        conn.close()


# ==================== Admin ETL Endpoints ====================

@app.post("/admin/etl/players")
async def trigger_player_etl(
    season: int = Query(..., ge=2000, le=2030),
    background_tasks: BackgroundTasks = None
):
    """
    Trigger player ETL for a specific season
    
    This endpoint runs the ETL in the background and returns immediately.
    
    Example:
    - POST /admin/etl/players?season=2023
    """
    def run_etl(season: int):
        """Background task to run ETL"""
        try:
            config = ETLConfig.from_env(season)
            etl = PlayerETL(config)
            result = etl.run()
            # Optionally: Store result in database or send notification
            print(f"ETL completed: {result}")
        except Exception as e:
            print(f"ETL failed: {str(e)}")
    
    # Add to background tasks
    background_tasks.add_task(run_etl, season)
    
    return {
        'status': 'started',
        'message': f'Player ETL for season {season} started in background',
        'season': season,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.post("/admin/etl/players/sync")
def trigger_player_etl_sync(season: int = Query(..., ge=2000, le=2030)):
    """
    Trigger player ETL synchronously (waits for completion)
    
    Warning: This will block until the ETL completes (20-30 seconds)
    
    Example:
    - POST /admin/etl/players/sync?season=2023
    """
    try:
        config = ETLConfig.from_env(season)
        etl = PlayerETL(config)
        result = etl.run()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/etl/players/team/{team_id}")
async def trigger_team_player_etl(
    team_id: int,
    season: int = Query(..., ge=2000, le=2030),
    background_tasks: BackgroundTasks = None
):
    """
    Trigger player ETL for a specific team
    
    Example:
    - POST /admin/etl/players/team/1?season=2023
    """
    def run_team_etl(team_id: int, season: int):
        """Background task to run team ETL"""
        try:
            # Get external_team_key from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT external_team_key FROM team WHERE team_id = %s", (team_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                print(f"Team {team_id} not found")
                return
            
            external_team_key = result[0]
            
            # Run ETL
            config = ETLConfig.from_env(season)
            etl = PlayerETL(config)
            result = etl.run_for_team(external_team_key)
            print(f"Team ETL completed: {result}")
        except Exception as e:
            print(f"Team ETL failed: {str(e)}")
    
    background_tasks.add_task(run_team_etl, team_id, season)
    
    return {
        'status': 'started',
        'message': f'Player ETL for team {team_id}, season {season} started',
        'team_id': team_id,
        'season': season
    }


# ==================== Player Statistics Endpoints ====================

@app.get("/players/stats/summary")
def get_player_stats_summary():
    """
    Get summary statistics about players in database
    
    Example:
    - GET /players/stats/summary
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    stats_query = """
        SELECT 
            COUNT(*) as total_players,
            COUNT(DISTINCT team_id) as teams_with_players,
            COUNT(DISTINCT position) as unique_positions,
            COUNT(*) FILTER (WHERE player_group = 'Offense') as offense_count,
            COUNT(*) FILTER (WHERE player_group = 'Defense') as defense_count,
            COUNT(*) FILTER (WHERE player_group = 'Special Teams') as special_teams_count,
            AVG(age) as avg_age,
            MIN(created_at) as earliest_record,
            MAX(updated_at) as latest_update
        FROM player
    """
    
    cursor.execute(stats_query)
    stats = cursor.fetchone()
    
    # Position breakdown
    position_query = """
        SELECT position, COUNT(*) as count
        FROM player
        WHERE position IS NOT NULL
        GROUP BY position
        ORDER BY count DESC
        LIMIT 10
    """
    
    cursor.execute(position_query)
    positions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        'summary': stats,
        'top_positions': positions
    }


# ==================== Helper Function ====================

def get_db_connection():
    """
    Get database connection
    Uses the same connection pattern as your existing ETL files
    """
    return get_conn()


# ==================== Example Usage ====================

if __name__ == "__main__":
    """
    This file is meant to be integrated into your existing FastAPI main.py
    
    To add these endpoints to your app:
    
    1. Copy the route definitions (@app.get, @app.post) into your main.py
    2. Copy the helper functions (get_all_players, etc.)
    3. Update get_db_connection() to use your existing connection method
    4. Add the routes to your CORS allowed origins if needed
    """
    pass
