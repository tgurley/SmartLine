"""
Team API Endpoints
==================
Add these to your main.py FastAPI application
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
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
router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/search")
async def search_teams(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Search for teams by name or abbreviation
    
    Returns teams matching the search query.
    Case-insensitive, partial match on name or abbreviation.
    
    Example: GET /teams/search?q=chiefs&limit=10
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Search query - case-insensitive partial match on name or abbrev
        query = """
            SELECT 
                t.team_id,
                t.name,
                t.abbrev,
                t.city,
                t.external_team_key,
                t.logo_url,
                COUNT(p.player_id) as player_count
            FROM team t
            LEFT JOIN player p ON t.team_id = p.team_id
            WHERE 
                t.name ILIKE %s 
                OR t.abbrev ILIKE %s
                OR t.city ILIKE %s
            GROUP BY t.team_id, t.name, t.abbrev, t.city, t.external_team_key, t.logo_url
            ORDER BY 
                -- Exact matches first
                CASE 
                    WHEN LOWER(t.name) = LOWER(%s) THEN 0
                    WHEN LOWER(t.abbrev) = LOWER(%s) THEN 1
                    ELSE 2 
                END,
                t.name
            LIMIT %s
        """
        
        search_pattern = f"%{q}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, q, q, limit))
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


@router.get("/{team_id}")
async def get_team_detail(team_id: int):
    """
    Get detailed information about a specific team
    
    Returns complete team profile.
    
    Example: GET /teams/17
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                t.team_id,
                t.name,
                t.abbrev,
                t.city,
                t.external_team_key,
                t.league_id,
                l.name as league_name,
                t.coach,
                t.owner,
                t.stadium,
                t.established,
                t.logo_url,
                t.country_name,
                t.country_code,
                t.country_flag_url,
                COUNT(p.player_id) as player_count
            FROM team t
            LEFT JOIN league l ON t.league_id = l.league_id
            LEFT JOIN player p ON t.team_id = p.team_id
            WHERE t.team_id = %s
            GROUP BY t.team_id, t.name, t.abbrev, t.city, t.external_team_key, t.league_id, l.name,
                     t.coach, t.owner, t.stadium, t.established, t.logo_url,
                     t.country_name, t.country_code, t.country_flag_url
        """
        
        cursor.execute(query, (team_id,))
        team = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return team
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team: {str(e)}")


@router.get("/{team_id}/roster")
async def get_team_roster(team_id: int):
    """
    Get roster for a specific team
    
    Returns all players on the team.
    
    Example: GET /teams/17/roster
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First verify team exists
        cursor.execute("SELECT team_id, name FROM team WHERE team_id = %s", (team_id,))
        team = cursor.fetchone()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get roster
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
                CASE p.player_group
                    WHEN 'Offense' THEN 1
                    WHEN 'Defense' THEN 2
                    WHEN 'Special Teams' THEN 3
                    ELSE 4
                END,
                p.position,
                p.full_name
        """
        
        cursor.execute(query, (team_id,))
        players = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "team_id": team_id,
            "team_name": team['name'],
            "player_count": len(players),
            "players": players
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roster: {str(e)}")


@router.get("/{team_id}/games")
async def get_team_games(
    team_id: int,
    season: Optional[int] = Query(None, description="Filter by season year"),
    limit: int = Query(10, ge=1, le=100, description="Maximum games to return")
):
    """
    Get games for a specific team
    
    Returns games where team is home or away.
    
    Example: GET /teams/17/games?season=2023&limit=10
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify team exists
        cursor.execute("SELECT team_id, name FROM team WHERE team_id = %s", (team_id,))
        team = cursor.fetchone()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Build query
        where_conditions = ["(g.home_team_id = %s OR g.away_team_id = %s)"]
        params = [team_id, team_id]
        
        if season:
            where_conditions.append("s.year = %s")
            params.append(season)
        
        where_clause = " AND ".join(where_conditions)
        params.append(limit)
        
        query = f"""
            SELECT 
                g.game_id,
                g.week,
                g.game_datetime_utc,
                g.status,
                g.home_team_id,
                ht.name as home_team_name,
                ht.abbrev as home_team_abbrev,
                g.away_team_id,
                at.name as away_team_name,
                at.abbrev as away_team_abbrev,
                s.year as season,
                gr.home_score,
                gr.away_score,
                v.name as venue_name,
                v.city as venue_city,
                v.is_dome
            FROM game g
            JOIN season s ON g.season_id = s.season_id
            JOIN team ht ON g.home_team_id = ht.team_id
            JOIN team at ON g.away_team_id = at.team_id
            LEFT JOIN game_result gr ON g.game_id = gr.game_id
            LEFT JOIN venue v ON g.venue_id = v.venue_id
            WHERE {where_clause}
            ORDER BY g.game_datetime_utc DESC
            LIMIT %s
        """
        
        cursor.execute(query, params)
        games = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "team_id": team_id,
            "team_name": team['name'],
            "game_count": len(games),
            "games": games
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {str(e)}")


@router.get("/")
async def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(32, ge=1, le=100, description="Results per page")
):
    """
    List all teams
    
    Returns all teams with pagination.
    
    Example: GET /teams?page=1&limit=32
    """
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count total
        cursor.execute("SELECT COUNT(*) as total FROM team")
        total = cursor.fetchone()['total']
        
        # Get teams
        offset = (page - 1) * limit
        
        query = """
            SELECT 
                t.team_id,
                t.name,
                t.abbrev,
                t.city,
                t.external_team_key,
                t.logo_url,
                COUNT(p.player_id) as player_count
            FROM team t
            LEFT JOIN player p ON t.team_id = p.team_id
            GROUP BY t.team_id, t.name, t.abbrev, t.city, t.external_team_key, t.logo_url
            ORDER BY t.name
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, offset))
        teams = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "teams": teams
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")


# Integration instructions for main.py:
"""
To add these endpoints to your main.py:

1. Import the router:
   from team_endpoints import router as team_router

2. Include the router in your app:
   app.include_router(team_router)

Complete example:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from player_endpoints import router as player_router
from team_endpoints import router as team_router

app = FastAPI(title="SmartLine NFL Betting Intelligence")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(player_router)
app.include_router(team_router)

# Your other routes...
```
"""
