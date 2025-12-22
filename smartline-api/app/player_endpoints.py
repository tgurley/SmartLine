"""
Player API Endpoints
====================
Add these to your main.py FastAPI application
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection helper
def get_conn():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )

# Create router
router = APIRouter(prefix="/players", tags=["players"])


@router.get("/search")
async def search_players(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search for players by name
    
    Returns players matching the search query with their basic info.
    Case-insensitive, partial match on full_name.
    
    Example: GET /players/search?q=mahomes&limit=10
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Search query - case-insensitive partial match
        query = """
            SELECT 
                p.player_id,
                p.full_name,
                p.position,
                p.jersey_number,
                p.team_id,
                t.name as team_name,
                t.abbrev as team_abbrev,
                p.college,
                p.age,
                p.image_url
            FROM player p
            LEFT JOIN team t ON p.team_id = t.team_id
            WHERE p.full_name ILIKE %s
            ORDER BY 
                -- Exact matches first
                CASE WHEN LOWER(p.full_name) = LOWER(%s) THEN 0 ELSE 1 END,
                -- Then by name
                p.full_name
            LIMIT %s
        """
        
        search_pattern = f"%{q}%"
        cursor.execute(query, (search_pattern, q, limit))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{player_id}")
async def get_player_detail(player_id: int):
    """
    Get detailed information about a specific player
    
    Returns complete player profile including stats and team info.
    
    Example: GET /players/123
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
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
                p.created_at,
                p.updated_at,
                p.team_id,
                t.name as team_name,
                t.abbrev as team_abbrev,
                t.external_team_key
            FROM player p
            LEFT JOIN team t ON p.team_id = t.team_id
            WHERE p.player_id = %s
        """
        
        cursor.execute(query, (player_id,))
        player = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return player
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch player: {str(e)}")


@router.get("/")
async def list_players(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    position: Optional[str] = Query(None, description="Filter by position"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Results per page")
):
    """
    List all players with optional filters
    
    Supports pagination and filtering by team or position.
    
    Examples:
    - GET /players?page=1&limit=50
    - GET /players?team_id=5&page=1
    - GET /players?position=QB
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if team_id is not None:
            where_conditions.append("p.team_id = %s")
            params.append(team_id)
        
        if position:
            where_conditions.append("p.position = %s")
            params.append(position.upper())
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM player p
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get players
        offset = (page - 1) * limit
        params.extend([limit, offset])
        
        query = f"""
            SELECT 
                p.player_id,
                p.full_name,
                p.position,
                p.jersey_number,
                p.team_id,
                t.name as team_name,
                t.abbrev as team_abbrev,
                p.age,
                p.college,
                p.image_url
            FROM player p
            LEFT JOIN team t ON p.team_id = t.team_id
            {where_clause}
            ORDER BY p.full_name
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, params)
        players = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "players": players
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list players: {str(e)}")


@router.get("/stats/summary")
async def get_player_stats_summary():
    """
    Get summary statistics about players
    
    Returns counts by position, team distribution, etc.
    
    Example: GET /players/stats/summary
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total players
        cursor.execute("SELECT COUNT(*) as total FROM player")
        total_players = cursor.fetchone()['total']
        
        # By position
        cursor.execute("""
            SELECT position, COUNT(*) as count
            FROM player
            WHERE position IS NOT NULL
            GROUP BY position
            ORDER BY count DESC
        """)
        by_position = cursor.fetchall()
        
        # By team
        cursor.execute("""
            SELECT 
                t.name as team_name,
                t.abbrev,
                COUNT(p.player_id) as player_count
            FROM team t
            LEFT JOIN player p ON t.team_id = p.team_id
            GROUP BY t.team_id, t.name, t.abbrev
            ORDER BY player_count DESC
        """)
        by_team = cursor.fetchall()
        
        # Players with/without teams
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE team_id IS NOT NULL) as with_team,
                COUNT(*) FILTER (WHERE team_id IS NULL) as without_team
            FROM player
        """)
        team_assignment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_players": total_players,
            "by_position": by_position,
            "by_team": by_team,
            "team_assignment": team_assignment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")