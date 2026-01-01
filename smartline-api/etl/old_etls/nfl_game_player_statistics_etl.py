#!/usr/bin/env python3
"""
NFL Game Player Statistics ETL
================================
Ingests player statistics for individual games from API-Sports.

Features:
- Fetches player statistics by game ID
- Stores flexible key-value pairs for any stat type
- Supports 10 stat groups (Passing, Rushing, Receiving, Defense, etc.)
- Efficient upsert logic

Usage:
    # Ingest all 2023 regular season games
    python nfl_game_player_statistics_etl.py --season 2023
    
    # Ingest specific game
    python nfl_game_player_statistics_etl.py --game-id 1985
    
    # Update existing stats (re-fetch all)
    python nfl_game_player_statistics_etl.py --season 2023 --update

API Endpoint: GET /games/statistics/players?id={game_id}
Returns: Player statistics grouped by stat type (Passing, Rushing, etc.)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any

import psycopg2
from psycopg2.extras import execute_values
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ETLConfig:
    """Configuration for Game Player Statistics ETL"""
    
    def __init__(self, args):
        self.api_key = os.environ.get('API_SPORTS_KEY')
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY environment variable not set")
        
        self.api_base_url = "https://v1.american-football.api-sports.io"
        self.season = args.season
        self.game_id = args.game_id
        self.update_mode = args.update
        self.delay_between_requests = 1.0  # Rate limiting


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


class SportsAPIClient:
    """Client for interacting with API-Sports."""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'x-apisports-key': config.api_key
        })
        self.request_count = 0
        
    def get_game_player_statistics(self, game_id: int) -> Optional[Dict]:
        """
        Fetch player statistics for a specific game.
        
        Args:
            game_id: The external game ID from API-Sports
            
        Returns:
            Dict with game player statistics or None if error
        """
        url = f"{self.config.api_base_url}/games/statistics/players"
        params = {'id': game_id}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self.request_count += 1
            
            data = response.json()
            
            if data.get('errors'):
                logger.error(f"API returned errors for game {game_id}: {data['errors']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch player statistics for game {game_id}: {e}")
            return None
        finally:
            # Rate limiting
            time.sleep(self.config.delay_between_requests)
    
    def get_api_call_count(self) -> int:
        """Return the number of API calls made."""
        return self.request_count


class GamePlayerStatisticsTransformer:
    """Transforms API data into database-ready format."""
    
    # Mapping of API group names to our database stat_group values
    GROUP_NAME_MAPPING = {
        'Passing': 'Passing',
        'Rushing': 'Rushing',
        'Receiving': 'Receiving',
        'Defensive': 'Defense',
        'Defense': 'Defense',
        'Fumbles': 'Fumbles',
        'Interceptions': 'Interceptions',
        'Kicking': 'Kicking',
        'Punting': 'Punting',
        'Kick Returns': 'Kick Returns',
        'Kick_Returns': 'Kick Returns',
        'kick_returns': 'Kick Returns',
        'Punt Returns': 'Punt Returns',
        'Punt_Returns': 'Punt Returns',
        'punt_returns': 'Punt Returns',
    }
    
    @staticmethod
    def normalize_group_name(api_group_name: str) -> str:
        """Normalize API group name to database stat_group value."""
        # First try direct mapping
        if api_group_name in GamePlayerStatisticsTransformer.GROUP_NAME_MAPPING:
            return GamePlayerStatisticsTransformer.GROUP_NAME_MAPPING[api_group_name]
        
        # If not found, try replacing underscores with spaces and title casing
        normalized = api_group_name.replace('_', ' ').title()
        if normalized in GamePlayerStatisticsTransformer.GROUP_NAME_MAPPING.values():
            return normalized
        
        # Last resort: replace underscores and return
        return api_group_name.replace('_', ' ').title()
    
    @staticmethod
    def transform_player_statistics(
        game_data: Dict,
        game_id: int,
        team_mapping: Dict[int, int],
        player_mapping: Dict[int, int]
    ) -> List[Dict]:
        """
        Transform API response into database records.
        
        Args:
            game_data: Raw API response
            game_id: Internal game_id from database
            team_mapping: Maps external_team_key to internal team_id
            player_mapping: Maps external_player_id to internal player_id
            
        Returns:
            List of stat records (one per player per stat group per metric)
        """
        records = []
        
        response = game_data.get('response', [])
        
        for team_data in response:
            team_info = team_data.get('team', {})
            external_team_id = team_info.get('id')
            internal_team_id = team_mapping.get(external_team_id)
            
            if not internal_team_id:
                logger.warning(f"Unknown team ID {external_team_id}, skipping")
                continue
            
            groups = team_data.get('groups', [])
            
            for group in groups:
                group_name = group.get('name', '')
                normalized_group = GamePlayerStatisticsTransformer.normalize_group_name(group_name)
                
                players = group.get('players', [])
                
                for player_data in players:
                    player_info = player_data.get('player', {})
                    external_player_id = player_info.get('id')
                    internal_player_id = player_mapping.get(external_player_id)
                    
                    if not internal_player_id:
                        logger.debug(f"Unknown player ID {external_player_id}, skipping")
                        continue
                    
                    statistics = player_data.get('statistics', [])
                    
                    for stat in statistics:
                        metric_name = stat.get('name', '')
                        metric_value = stat.get('value', '')
                        
                        # Convert value to string, handle None
                        if metric_value is None:
                            metric_value = None
                        else:
                            metric_value = str(metric_value)
                        
                        record = {
                            'game_id': game_id,
                            'player_id': internal_player_id,
                            'team_id': internal_team_id,
                            'stat_group': normalized_group,
                            'metric_name': metric_name,
                            'metric_value': metric_value,
                            'source': 'api-sports',
                            'pulled_at_utc': datetime.utcnow()
                        }
                        
                        records.append(record)
        
        return records


class GamePlayerStatisticsDatabaseLoader:
    """Handles database operations for game player statistics."""
    
    def get_team_mapping(self) -> Dict[int, int]:
        """
        Get mapping of external_team_key to internal team_id.
        
        Returns:
            Dict mapping external_team_key -> team_id
        """
        query = """
            SELECT external_team_key, team_id 
            FROM team
        """
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return {row[0]: row[1] for row in cur.fetchall()}
    
    def get_player_mapping(self) -> Dict[int, int]:
        """
        Get mapping of external_player_id to internal player_id.
        
        Returns:
            Dict mapping external_player_id -> player_id
        """
        query = """
            SELECT external_player_id, player_id 
            FROM player
            WHERE external_player_id IS NOT NULL
        """
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return {row[0]: row[1] for row in cur.fetchall()}
    
    def get_games_for_season(self, season_year: int) -> List[Dict]:
        """
        Get all games for a specific season that need statistics.
        
        Args:
            season_year: Year of the season (e.g., 2023)
            
        Returns:
            List of dicts with game_id and external_game_key
        """
        query = """
            SELECT 
                g.game_id,
                g.external_game_key,
                g.status,
                g.week
            FROM game g
            JOIN season s ON g.season_id = s.season_id
            WHERE s.year = %s
              AND g.external_game_key IS NOT NULL
              AND g.status = 'final'
            ORDER BY g.week, g.game_datetime_utc
        """
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (season_year,))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_games_without_statistics(self, season_year: int) -> List[Dict]:
        """
        Get games that don't have player statistics yet.
        
        Args:
            season_year: Year of the season
            
        Returns:
            List of games without statistics
        """
        query = """
            SELECT 
                g.game_id,
                g.external_game_key,
                g.status,
                g.week
            FROM game g
            JOIN season s ON g.season_id = s.season_id
            LEFT JOIN game_player_statistics gps ON g.game_id = gps.game_id
            WHERE s.year = %s
              AND g.external_game_key IS NOT NULL
              AND g.status = 'final'
              AND gps.game_id IS NULL
            ORDER BY g.week, g.game_datetime_utc
        """
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (season_year,))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def upsert_statistics(self, records: List[Dict]) -> int:
        """
        Insert or update game player statistics.
        
        Args:
            records: List of statistic records
            
        Returns:
            Number of records affected
        """
        if not records:
            return 0
        
        upsert_query = """
            INSERT INTO game_player_statistics (
                game_id, player_id, team_id, stat_group,
                metric_name, metric_value, source, pulled_at_utc
            ) VALUES %s
            ON CONFLICT (game_id, player_id, team_id, stat_group, metric_name) 
            DO UPDATE SET
                metric_value = EXCLUDED.metric_value,
                pulled_at_utc = EXCLUDED.pulled_at_utc
        """
        
        values = [
            (
                r['game_id'], r['player_id'], r['team_id'], r['stat_group'],
                r['metric_name'], r['metric_value'], r['source'], r['pulled_at_utc']
            )
            for r in records
        ]
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(cur, upsert_query, values)
                conn.commit()
                return len(records)


class GamePlayerStatisticsETL:
    """Main ETL orchestrator for game player statistics."""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.api_client = SportsAPIClient(config)
        self.db_loader = GamePlayerStatisticsDatabaseLoader()
        self.transformer = GamePlayerStatisticsTransformer()
        
    def run_for_season(self, season_year: int) -> Dict[str, int]:
        """
        Run ETL for all games in a season.
        
        Args:
            season_year: Year of the season
            
        Returns:
            Dict with summary statistics
        """
        logger.info(f"Starting ETL for {season_year} season")
        
        # Get mappings
        team_mapping = self.db_loader.get_team_mapping()
        player_mapping = self.db_loader.get_player_mapping()
        logger.info(f"Loaded {len(team_mapping)} teams and {len(player_mapping)} players")
        
        # Get games to process
        if self.config.update_mode:
            games = self.db_loader.get_games_for_season(season_year)
            logger.info(f"Update mode: Processing all {len(games)} games")
        else:
            games = self.db_loader.get_games_without_statistics(season_year)
            logger.info(f"Incremental mode: Processing {len(games)} games without statistics")
        
        if not games:
            logger.info("No games to process")
            return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 0}
        
        # Process games
        total_stats = 0
        games_processed = 0
        games_failed = 0
        
        for i, game in enumerate(games, 1):
            game_id = game['game_id']
            external_game_key = game['external_game_key']
            
            logger.info(f"[{i}/{len(games)}] Processing game {game_id} (Week {game['week']})")
            
            # Fetch statistics from API
            game_data = self.api_client.get_game_player_statistics(external_game_key)
            
            if not game_data:
                logger.warning(f"Failed to fetch statistics for game {game_id}")
                games_failed += 1
                continue
            
            # Transform data
            stat_records = self.transformer.transform_player_statistics(
                game_data, 
                game_id,
                team_mapping,
                player_mapping
            )
            
            if not stat_records:
                logger.warning(f"No statistics extracted for game {game_id}")
                games_failed += 1
                continue
            
            # Load into database
            inserted = self.db_loader.upsert_statistics(stat_records)
            total_stats += inserted
            games_processed += 1
            
            logger.info(f"  → Inserted {inserted} player stat records")
        
        # Summary
        summary = {
            'games_processed': games_processed,
            'games_failed': games_failed,
            'stats_inserted': total_stats,
            'api_calls': self.api_client.get_api_call_count()
        }
        
        logger.info("=" * 60)
        logger.info("ETL COMPLETE")
        logger.info(f"Games processed: {games_processed}")
        logger.info(f"Games failed: {games_failed}")
        logger.info(f"Player stat records inserted: {total_stats}")
        logger.info(f"Total API calls: {summary['api_calls']}")
        logger.info("=" * 60)
        
        return summary
    
    def run_for_game(self, game_id: int) -> Dict[str, int]:
        """
        Run ETL for a specific game.
        
        Args:
            game_id: Internal game_id from database
            
        Returns:
            Dict with summary statistics
        """
        logger.info(f"Starting ETL for game {game_id}")
        
        # Get mappings
        team_mapping = self.db_loader.get_team_mapping()
        player_mapping = self.db_loader.get_player_mapping()
        
        # Get game info
        query = "SELECT game_id, external_game_key FROM game WHERE game_id = %s"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (game_id,))
                result = cur.fetchone()
                
                if not result:
                    logger.error(f"Game {game_id} not found")
                    return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 0}
                
                _, external_game_key = result
        
        # Fetch statistics
        game_data = self.api_client.get_game_player_statistics(external_game_key)
        
        if not game_data:
            logger.error(f"Failed to fetch statistics for game {game_id}")
            return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 1}
        
        # Transform and load
        stat_records = self.transformer.transform_player_statistics(
            game_data,
            game_id,
            team_mapping,
            player_mapping
        )
        
        if stat_records:
            inserted = self.db_loader.upsert_statistics(stat_records)
            logger.info(f"Inserted {inserted} player stat records for game {game_id}")
            return {'games_processed': 1, 'stats_inserted': inserted, 'api_calls': 1}
        
        return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 1}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ETL for NFL game player statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all 2023 regular season games (incremental)
  python nfl_game_player_statistics_etl.py --season 2023
  
  # Update all 2023 games (re-fetch)
  python nfl_game_player_statistics_etl.py --season 2023 --update
  
  # Ingest specific game
  python nfl_game_player_statistics_etl.py --game-id 1234
        """
    )
    
    parser.add_argument(
        '--season',
        type=int,
        help='Season year (e.g., 2023)'
    )
    
    parser.add_argument(
        '--game-id',
        type=int,
        help='Process specific game by internal game_id'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='Re-fetch and update existing statistics'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.season and not args.game_id:
        parser.error("Either --season or --game-id must be provided")
    
    if args.season and args.game_id:
        parser.error("Cannot specify both --season and --game-id")
    
    # Check required environment variables
    required_vars = ['API_SPORTS_KEY', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Create config
    try:
        config = ETLConfig(args)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run ETL
    etl = GamePlayerStatisticsETL(config)
    
    try:
        if args.game_id:
            summary = etl.run_for_game(args.game_id)
        else:
            summary = etl.run_for_season(args.season)
        
        # Exit with appropriate code
        if summary['games_processed'] == 0:
            sys.exit(1)
        
    except Exception as e:
        logger.exception(f"ETL failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
