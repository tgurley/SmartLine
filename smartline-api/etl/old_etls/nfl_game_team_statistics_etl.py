#!/usr/bin/env python3
"""
NFL Game Team Statistics ETL
================================
Ingests team statistics for individual games from API-Sports.

Features:
- Fetches team statistics by game ID
- Minimal API calls: Only fetches games for specified season
- Stores detailed stats per team per game
- Efficient upsert logic

Usage:
    # Ingest all 2023 regular season games
    python nfl_game_team_statistics_etl.py --season 2023
    
    # Ingest specific game
    python nfl_game_team_statistics_etl.py --game-id 1985
    
    # Update existing stats (re-fetch all)
    python nfl_game_team_statistics_etl.py --season 2023 --update

API Endpoint: GET /games/statistics/teams?id={game_id}
Returns: 2 team stat records per game (home & away)
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
    """Configuration for Game Team Statistics ETL"""
    
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
        
    def get_game_statistics(self, game_id: int) -> Optional[Dict]:
        """
        Fetch team statistics for a specific game.
        
        Args:
            game_id: The external game ID from API-Sports
            
        Returns:
            Dict with game statistics or None if error
        """
        url = f"{self.config.api_base_url}/games/statistics/teams"
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
            logger.error(f"Failed to fetch statistics for game {game_id}: {e}")
            return None
        finally:
            # Rate limiting
            time.sleep(self.config.delay_between_requests)
    
    def get_api_call_count(self) -> int:
        """Return the number of API calls made."""
        return self.request_count


class GameStatisticsTransformer:
    """Transforms API data into database-ready format."""
    
    @staticmethod
    def extract_value(data: Dict, key: str) -> Any:
        """Safely extract value from nested dict."""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value
    
    @staticmethod
    def transform_team_statistics(
        game_data: Dict,
        game_id: int,
        team_mapping: Dict[int, int]
    ) -> List[Dict]:
        """
        Transform API response into database records.
        
        Args:
            game_data: Raw API response
            game_id: Internal game_id from database
            team_mapping: Maps external_team_key to internal team_id
            
        Returns:
            List of stat records (one per team)
        """
        records = []
        
        response = game_data.get('response', [])
        
        for team_stat in response:
            team_info = team_stat.get('team', {})
            stats = team_stat.get('statistics', {})
            
            external_team_id = team_info.get('id')
            internal_team_id = team_mapping.get(external_team_id)
            
            if not internal_team_id:
                logger.warning(f"Unknown team ID {external_team_id}, skipping")
                continue
            
            # Extract all statistics
            first_downs = stats.get('first_downs', {})
            plays = stats.get('plays', {})
            yards = stats.get('yards', {})
            passing = stats.get('passing', {})
            rushings = stats.get('rushings', {})
            red_zone = stats.get('red_zone', {})
            penalties = stats.get('penalties', {})
            turnovers = stats.get('turnovers', {})
            possession = stats.get('posession', {})  # Note: API has typo "posession"
            
            record = {
                'game_id': game_id,
                'team_id': internal_team_id,
                
                # First Downs
                'first_downs_total': first_downs.get('total'),
                'first_downs_passing': first_downs.get('passing'),
                'first_downs_rushing': first_downs.get('rushing'),
                'first_downs_from_penalties': first_downs.get('from_penalties'),
                'third_down_efficiency': first_downs.get('third_down_efficiency'),
                'fourth_down_efficiency': first_downs.get('fourth_down_efficiency'),
                
                # Plays & Yards
                'plays_total': plays.get('total'),
                'yards_total': yards.get('total'),
                'yards_per_play': yards.get('yards_per_play'),
                'total_drives': yards.get('total_drives'),
                
                # Passing
                'passing_yards': passing.get('total'),
                'passing_comp_att': passing.get('comp_att'),
                'passing_yards_per_pass': passing.get('yards_per_pass'),
                'passing_interceptions_thrown': passing.get('interceptions_thrown'),
                'passing_sacks_yards_lost': passing.get('sacks_yards_lost'),
                
                # Rushing
                'rushing_yards': rushings.get('total'),
                'rushing_attempts': rushings.get('attempts'),
                'rushing_yards_per_rush': rushings.get('yards_per_rush'),
                
                # Red Zone
                'red_zone_made_att': red_zone.get('made_att'),
                
                # Penalties
                'penalties_total': penalties.get('total'),
                
                # Turnovers
                'turnovers_total': turnovers.get('total'),
                'turnovers_lost_fumbles': turnovers.get('lost_fumbles'),
                'turnovers_interceptions': turnovers.get('interceptions'),
                
                # Possession
                'possession_total': possession.get('total'),
                
                # Defensive Stats
                'interceptions_total': stats.get('interceptions', {}).get('total'),
                'fumbles_recovered_total': stats.get('fumbles_recovered', {}).get('total'),
                'sacks_total': stats.get('sacks', {}).get('total'),
                'safeties_total': stats.get('safeties', {}).get('total'),
                'int_touchdowns_total': stats.get('int_touchdowns', {}).get('total'),
                'points_against_total': stats.get('points_against', {}).get('total'),
                
                'source': 'api-sports',
                'pulled_at_utc': datetime.utcnow()
            }
            
            records.append(record)
        
        return records


class GameStatisticsDatabaseLoader:
    """Handles database operations for game statistics."""
    
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
        Get games that don't have statistics yet.
        
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
            LEFT JOIN game_team_statistics gts ON g.game_id = gts.game_id
            WHERE s.year = %s
              AND g.external_game_key IS NOT NULL
              AND g.status = 'final'
              AND gts.game_id IS NULL
            ORDER BY g.week, g.game_datetime_utc
        """
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (season_year,))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def upsert_statistics(self, records: List[Dict]) -> int:
        """
        Insert or update game team statistics.
        
        Args:
            records: List of statistic records
            
        Returns:
            Number of records affected
        """
        if not records:
            return 0
        
        upsert_query = """
            INSERT INTO game_team_statistics (
                game_id, team_id,
                first_downs_total, first_downs_passing, first_downs_rushing,
                first_downs_from_penalties, third_down_efficiency, fourth_down_efficiency,
                plays_total, yards_total, yards_per_play, total_drives,
                passing_yards, passing_comp_att, passing_yards_per_pass,
                passing_interceptions_thrown, passing_sacks_yards_lost,
                rushing_yards, rushing_attempts, rushing_yards_per_rush,
                red_zone_made_att, penalties_total,
                turnovers_total, turnovers_lost_fumbles, turnovers_interceptions,
                possession_total,
                interceptions_total, fumbles_recovered_total, sacks_total,
                safeties_total, int_touchdowns_total, points_against_total,
                source, pulled_at_utc
            ) VALUES %s
            ON CONFLICT (game_id, team_id) 
            DO UPDATE SET
                first_downs_total = EXCLUDED.first_downs_total,
                first_downs_passing = EXCLUDED.first_downs_passing,
                first_downs_rushing = EXCLUDED.first_downs_rushing,
                first_downs_from_penalties = EXCLUDED.first_downs_from_penalties,
                third_down_efficiency = EXCLUDED.third_down_efficiency,
                fourth_down_efficiency = EXCLUDED.fourth_down_efficiency,
                plays_total = EXCLUDED.plays_total,
                yards_total = EXCLUDED.yards_total,
                yards_per_play = EXCLUDED.yards_per_play,
                total_drives = EXCLUDED.total_drives,
                passing_yards = EXCLUDED.passing_yards,
                passing_comp_att = EXCLUDED.passing_comp_att,
                passing_yards_per_pass = EXCLUDED.passing_yards_per_pass,
                passing_interceptions_thrown = EXCLUDED.passing_interceptions_thrown,
                passing_sacks_yards_lost = EXCLUDED.passing_sacks_yards_lost,
                rushing_yards = EXCLUDED.rushing_yards,
                rushing_attempts = EXCLUDED.rushing_attempts,
                rushing_yards_per_rush = EXCLUDED.rushing_yards_per_rush,
                red_zone_made_att = EXCLUDED.red_zone_made_att,
                penalties_total = EXCLUDED.penalties_total,
                turnovers_total = EXCLUDED.turnovers_total,
                turnovers_lost_fumbles = EXCLUDED.turnovers_lost_fumbles,
                turnovers_interceptions = EXCLUDED.turnovers_interceptions,
                possession_total = EXCLUDED.possession_total,
                interceptions_total = EXCLUDED.interceptions_total,
                fumbles_recovered_total = EXCLUDED.fumbles_recovered_total,
                sacks_total = EXCLUDED.sacks_total,
                safeties_total = EXCLUDED.safeties_total,
                int_touchdowns_total = EXCLUDED.int_touchdowns_total,
                points_against_total = EXCLUDED.points_against_total,
                pulled_at_utc = EXCLUDED.pulled_at_utc
        """
        
        values = [
            (
                r['game_id'], r['team_id'],
                r['first_downs_total'], r['first_downs_passing'], r['first_downs_rushing'],
                r['first_downs_from_penalties'], r['third_down_efficiency'], r['fourth_down_efficiency'],
                r['plays_total'], r['yards_total'], r['yards_per_play'], r['total_drives'],
                r['passing_yards'], r['passing_comp_att'], r['passing_yards_per_pass'],
                r['passing_interceptions_thrown'], r['passing_sacks_yards_lost'],
                r['rushing_yards'], r['rushing_attempts'], r['rushing_yards_per_rush'],
                r['red_zone_made_att'], r['penalties_total'],
                r['turnovers_total'], r['turnovers_lost_fumbles'], r['turnovers_interceptions'],
                r['possession_total'],
                r['interceptions_total'], r['fumbles_recovered_total'], r['sacks_total'],
                r['safeties_total'], r['int_touchdowns_total'], r['points_against_total'],
                r['source'], r['pulled_at_utc']
            )
            for r in records
        ]
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                execute_values(cur, upsert_query, values)
                conn.commit()
                return len(records)


class GameStatisticsETL:
    """Main ETL orchestrator for game team statistics."""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.api_client = SportsAPIClient(config)
        self.db_loader = GameStatisticsDatabaseLoader()
        self.transformer = GameStatisticsTransformer()
        
    def run_for_season(self, season_year: int) -> Dict[str, int]:
        """
        Run ETL for all games in a season.
        
        Args:
            season_year: Year of the season
            
        Returns:
            Dict with summary statistics
        """
        logger.info(f"Starting ETL for {season_year} season")
        
        # Get team mapping
        team_mapping = self.db_loader.get_team_mapping()
        logger.info(f"Loaded {len(team_mapping)} teams")
        
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
            game_data = self.api_client.get_game_statistics(external_game_key)
            
            if not game_data:
                logger.warning(f"Failed to fetch statistics for game {game_id}")
                games_failed += 1
                continue
            
            # Transform data
            stat_records = self.transformer.transform_team_statistics(
                game_data, 
                game_id,
                team_mapping
            )
            
            if not stat_records:
                logger.warning(f"No statistics extracted for game {game_id}")
                games_failed += 1
                continue
            
            # Load into database
            inserted = self.db_loader.upsert_statistics(stat_records)
            total_stats += inserted
            games_processed += 1
            
            logger.info(f"  → Inserted {inserted} team stat records")
        
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
        logger.info(f"Team stat records inserted: {total_stats}")
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
        
        # Get team mapping
        team_mapping = self.db_loader.get_team_mapping()
        
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
        game_data = self.api_client.get_game_statistics(external_game_key)
        
        if not game_data:
            logger.error(f"Failed to fetch statistics for game {game_id}")
            return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 1}
        
        # Transform and load
        stat_records = self.transformer.transform_team_statistics(
            game_data,
            game_id,
            team_mapping
        )
        
        if stat_records:
            inserted = self.db_loader.upsert_statistics(stat_records)
            logger.info(f"Inserted {inserted} team stat records for game {game_id}")
            return {'games_processed': 1, 'stats_inserted': inserted, 'api_calls': 1}
        
        return {'games_processed': 0, 'stats_inserted': 0, 'api_calls': 1}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ETL for NFL game team statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all 2023 regular season games (incremental)
  python nfl_game_team_statistics_etl.py --season 2023
  
  # Update all 2023 games (re-fetch)
  python nfl_game_team_statistics_etl.py --season 2023 --update
  
  # Ingest specific game
  python nfl_game_team_statistics_etl.py --game-id 1234
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
    etl = GameStatisticsETL(config)
    
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
