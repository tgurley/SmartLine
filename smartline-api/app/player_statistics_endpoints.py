"""
SmartLine Player Statistics API Endpoints
==========================================
FastAPI endpoints for querying player statistics data.

Endpoints:
- GET /players/{player_id}/statistics - Get all stats for a player
- GET /players/{player_id}/statistics/{season} - Get stats for specific season
- GET /players/{player_id}/statistics/{season}/{stat_group} - Get specific stat group
- GET /statistics/leaders/{stat_group}/{metric_name} - Get statistical leaders
- GET /statistics/compare - Compare multiple players

Author: SmartLine Development Team
Date: 2024-12-22
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
    
router = APIRouter(prefix="/statistics", tags=["Player Statistics"])


# =========================================================
# PLAYER STATISTICS ENDPOINTS
# =========================================================

@router.get("/players/{player_id}/statistics")
async def get_player_all_statistics(
    player_id: int,
    season: Optional[int] = None
):
    """
    Get all statistics for a player, optionally filtered by season
    
    Returns data grouped by season and stat_group
    """
    conn = get_conn()
    
    try:
        with conn.cursor() as cur:
            if season:
                query = """
                    SELECT 
                        s.year as season,
                        t.name as team_name,
                        t.abbrev as team_abbrev,
                        ps.stat_group,
                        json_object_agg(ps.metric_name, ps.metric_value) as statistics,
                        MAX(ps.pulled_at_utc) as last_updated
                    FROM player_statistic ps
                    JOIN season s ON ps.season_id = s.season_id
                    JOIN team t ON ps.team_id = t.team_id
                    WHERE ps.player_id = %s
                      AND s.year = %s
                    GROUP BY s.year, t.name, t.abbrev, ps.stat_group
                    ORDER BY ps.stat_group
                """
                cur.execute(query, (player_id, season))
            else:
                query = """
                    SELECT 
                        s.year as season,
                        t.name as team_name,
                        t.abbrev as team_abbrev,
                        ps.stat_group,
                        json_object_agg(ps.metric_name, ps.metric_value) as statistics,
                        MAX(ps.pulled_at_utc) as last_updated
                    FROM player_statistic ps
                    JOIN season s ON ps.season_id = s.season_id
                    JOIN team t ON ps.team_id = t.team_id
                    WHERE ps.player_id = %s
                    GROUP BY s.year, t.name, t.abbrev, ps.stat_group
                    ORDER BY s.year DESC, ps.stat_group
                """
                cur.execute(query, (player_id,))
            
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail="No statistics found for this player")
            
            seasons_data = {}
            for row in results:
                season_key = row['season']
                if season_key not in seasons_data:
                    seasons_data[season_key] = {
                        'season': season_key,
                        'team_name': row['team_name'],
                        'team_abbrev': row['team_abbrev'],
                        'stat_groups': {},
                        'last_updated': row['last_updated']
                    }
                
                seasons_data[season_key]['stat_groups'][row['stat_group']] = row['statistics']
            
            return {
                'player_id': player_id,
                'seasons': list(seasons_data.values())
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {e}")
    finally:
        conn.close()


@router.get("/leaders/{stat_group}/{metric_name}")
async def get_statistical_leaders(
    stat_group: str,
    metric_name: str,
    season: int = Query(..., description="Season year"),
    limit: int = Query(10, ge=1, le=100, description="Number of leaders to return")
):
    """
    Get statistical leaders for a specific metric
    
    Example: /leaders/Passing/yards?season=2023&limit=10
    """
    conn = get_conn()
    
    try:
        with conn.cursor() as cur:
            query = """
                SELECT 
                    p.player_id,
                    p.full_name,
                    p.position,
                    t.name as team_name,
                    t.abbrev as team_abbrev,
                    ps.metric_value,
                    ps.pulled_at_utc as last_updated
                FROM player_statistic ps
                JOIN player p ON ps.player_id = p.player_id
                JOIN team t ON ps.team_id = t.team_id
                JOIN season s ON ps.season_id = s.season_id
                WHERE s.year = %s
                  AND ps.stat_group = %s
                  AND ps.metric_name = %s
                  AND ps.metric_value IS NOT NULL
                  AND ps.metric_value != ''
                ORDER BY 
                    CASE 
                        WHEN ps.metric_value ~ '^[0-9.]+$' 
                        THEN CAST(ps.metric_value AS NUMERIC)
                        ELSE 0 
                    END DESC
                LIMIT %s
            """
            cur.execute(query, (season, stat_group, metric_name, limit))
            
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for {stat_group} - {metric_name} in season {season}"
                )
            
            return {
                'season': season,
                'stat_group': stat_group,
                'metric_name': metric_name,
                'leaders': results
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leaders: {e}")
    finally:
        conn.close()


@router.get("/compare")
async def compare_players(
    player_ids: str = Query(..., description="Comma-separated player IDs"),
    season: int = Query(..., description="Season year"),
    stat_group: Optional[str] = Query(None, description="Optional stat group filter")
):
    """
    Compare statistics for multiple players in the same season
    """
    try:
        player_id_list = [int(pid.strip()) for pid in player_ids.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player_ids format")
    
    if len(player_id_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 players allowed")
    
    conn = get_conn()
    
    try:
        with conn.cursor() as cur:
            if stat_group:
                query = """
                    SELECT 
                        p.player_id, p.full_name, p.position,
                        t.name as team_name, t.abbrev as team_abbrev,
                        ps.stat_group,
                        json_object_agg(ps.metric_name, ps.metric_value) as statistics
                    FROM player_statistic ps
                    JOIN player p ON ps.player_id = p.player_id
                    JOIN team t ON ps.team_id = t.team_id
                    JOIN season s ON ps.season_id = s.season_id
                    WHERE ps.player_id = ANY(%s) AND s.year = %s AND ps.stat_group = %s
                    GROUP BY p.player_id, p.full_name, p.position, t.name, t.abbrev, ps.stat_group
                    ORDER BY p.full_name
                """
                cur.execute(query, (player_id_list, season, stat_group))
            else:
                query = """
                    SELECT 
                        p.player_id, p.full_name, p.position,
                        t.name as team_name, t.abbrev as team_abbrev,
                        ps.stat_group,
                        json_object_agg(ps.metric_name, ps.metric_value) as statistics
                    FROM player_statistic ps
                    JOIN player p ON ps.player_id = p.player_id
                    JOIN team t ON ps.team_id = t.team_id
                    JOIN season s ON ps.season_id = s.season_id
                    WHERE ps.player_id = ANY(%s) AND s.year = %s
                    GROUP BY p.player_id, p.full_name, p.position, t.name, t.abbrev, ps.stat_group
                    ORDER BY p.full_name, ps.stat_group
                """
                cur.execute(query, (player_id_list, season))
            
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail="No statistics found")
            
            players_data = {}
            for row in results:
                player_id = row['player_id']
                if player_id not in players_data:
                    players_data[player_id] = {
                        'player_id': player_id,
                        'full_name': row['full_name'],
                        'position': row['position'],
                        'team_name': row['team_name'],
                        'team_abbrev': row['team_abbrev'],
                        'stat_groups': {}
                    }
                
                players_data[player_id]['stat_groups'][row['stat_group']] = row['statistics']
            
            return {
                'season': season,
                'stat_group_filter': stat_group,
                'players': list(players_data.values())
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare players: {e}")
    finally:
        conn.close()


@router.get("/season-summary/{season}")
async def get_season_summary(season: int):
    """Get summary statistics for a season using the materialized view"""
    conn = get_conn()
    
    try:
        with conn.cursor() as cur:
            query = """
                SELECT * FROM player_season_summary
                WHERE season_year = %s
                ORDER BY full_name
            """
            cur.execute(query, (season,))
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail=f"No summary data for season {season}")
            
            return {
                'season': season,
                'player_count': len(results),
                'players': results
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch season summary: {e}")
    finally:
        conn.close()
