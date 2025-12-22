#!/usr/bin/env python3
"""
NFL Player Statistics ETL
==========================
Fetches player statistics from API-Sports and loads into database.

Key Optimization: Uses team-based fetching (only 32 API calls for full season!)

Usage:
    python nfl_player_statistics_etl.py --season 2023 --all          # All teams (32 calls)
    python nfl_player_statistics_etl.py --season 2023 --team-id 17   # Specific team (1 call)
    python nfl_player_statistics_etl.py --refresh-view               # Refresh materialized view
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import requests


# ==================== Configuration ====================

class ETLConfig:
    """Configuration for Player Statistics ETL"""
    
    def __init__(self, args):
        self.api_key = os.environ.get('API_SPORTS_KEY')
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY environment variable not set")
        
        self.api_base_url = "https://v1.american-football.api-sports.io"
        self.season = args.season
        self.team_id = args.team_id  # External team key (API ID)
        self.fetch_all = args.all
        self.update_only = args.update
        self.refresh_view_only = args.refresh_view
        self.delay_between_requests = 1.0  # Rate limiting
        
        # Validation
        if self.season and self.season < 2022:
            raise ValueError("Player statistics only available from 2022 onwards")


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


# ==================== API Client ====================

class SportsAPIClient:
    """Client for API-Sports player statistics"""
    
    def __init__(self, api_key: str, base_url: str, logger: logging.Logger):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logger
        self.request_count = 0
        self.cache = {}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with caching and rate limiting"""
        cache_key = f"{endpoint}?{str(params)}"
        
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit: {endpoint}")
            return self.cache[cache_key]
        
        url = f"{self.base_url}{endpoint}"
        headers = {'x-apisports-key': self.api_key}
        
        self.request_count += 1
        self.logger.info(f"API Request #{self.request_count}: {endpoint} {params or ''}")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errors') and len(data['errors']) > 0:
                self.logger.error(f"API returned errors: {data['errors']}")
                return None
            
            self.cache[cache_key] = data
            
            # Rate limiting
            time.sleep(self.delay)
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None
    
    def set_delay(self, delay: float):
        """Set delay between requests"""
        self.delay = delay
    
    def get_team_statistics(self, team_id: int, season: int) -> List[Dict]:
        """
        Get statistics for all players on a team (PRIMARY METHOD - Only 1 API call!)
        
        This fetches all players on a team in a single request, which is far more
        efficient than fetching player-by-player.
        
        Args:
            team_id: External API-Sports team ID (e.g., 17 for Kansas City Chiefs)
            season: Season year (e.g., 2023)
            
        Returns:
            List of player statistics dictionaries
        """
        self.logger.info(f"Fetching statistics for team {team_id}, season {season}")
        
        result = self._make_request('/players/statistics', {
            'team': team_id,
            'season': season
        })
        
        if result and result.get('response'):
            player_count = len(result['response'])
            self.logger.info(f"✓ Retrieved statistics for {player_count} players")
            return result['response']
        
        self.logger.warning(f"No statistics found for team {team_id}, season {season}")
        return []
    
    def get_request_count(self) -> int:
        """Get total number of API requests made"""
        return self.request_count


# ==================== Data Transformer ====================

class PlayerStatisticsTransformer:
    """Transform API player statistics to database format"""
    
    VALID_STAT_GROUPS = [
        'Passing', 'Rushing', 'Receiving', 'Defense',
        'Kicking', 'Punting', 'Returning', 'Scoring'
    ]
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def transform_player_statistics(
        self, 
        player_data: Dict,
        season_id: int
    ) -> Tuple[int, int, List[Tuple]]:
        """
        Transform API player statistics to database records
        
        API Format:
        {
            "player": {"id": 1, "name": "Patrick Mahomes"},
            "teams": [{
                "team": {"id": 17, "name": "Kansas City Chiefs"},
                "groups": [{
                    "name": "Passing",
                    "statistics": [
                        {"name": "passing attempts", "value": "520"},
                        {"name": "completions", "value": "345"}
                    ]
                }]
            }]
        }
        
        Returns:
            Tuple of (external_player_id, external_team_id, records_list)
            where records_list contains tuples of:
            (season_id, stat_group, metric_name, metric_value)
        """
        # Extract player info
        player_info = player_data.get('player', {})
        external_player_id = player_info.get('id')
        player_name = player_info.get('name', 'Unknown')
        
        if not external_player_id:
            self.logger.warning(f"Skipping player with no ID: {player_name}")
            return None, None, []
        
        # Process teams (a player can have stats for multiple teams in one season)
        all_records = []
        teams = player_data.get('teams', [])
        
        if not teams:
            self.logger.debug(f"No team data for {player_name}")
            return external_player_id, None, []
        
        # We'll use the first team as the primary team
        primary_team = teams[0]
        team_info = primary_team.get('team', {})
        external_team_id = team_info.get('id')
        
        if not external_team_id:
            self.logger.warning(f"No team ID for {player_name}")
            return external_player_id, None, []
        
        # Process all teams (in case player was traded mid-season)
        for team_data in teams:
            team_info = team_data.get('team', {})
            ext_team_id = team_info.get('id')
            
            if not ext_team_id:
                continue
            
            # Process stat groups
            groups = team_data.get('groups', [])
            
            for group in groups:
                stat_group = group.get('name')
                
                # Validate stat group
                if stat_group not in self.VALID_STAT_GROUPS:
                    self.logger.warning(f"Unknown stat group for {player_name}: {stat_group}")
                    continue
                
                # Process statistics within the group
                statistics = group.get('statistics', [])
                
                for stat in statistics:
                    metric_name = stat.get('name')
                    metric_value = stat.get('value')
                    
                    # Skip if no metric name
                    if not metric_name:
                        continue
                    
                    # Create record tuple:
                    # (external_team_id, season_id, stat_group, metric_name, metric_value)
                    all_records.append((
                        ext_team_id,
                        season_id,
                        stat_group,
                        metric_name,
                        metric_value
                    ))
        
        return external_player_id, external_team_id, all_records


# ==================== Database Loader ====================

class PlayerStatisticsDatabaseLoader:
    """Load player statistics into database"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database"""
        self.conn = get_conn()
        self.cursor = self.conn.cursor()
        self.logger.info("✓ Database connection established")
    
    def get_season_id(self, season_year: int) -> Optional[int]:
        """Get season_id for a given year"""
        try:
            self.cursor.execute("""
                SELECT s.season_id 
                FROM season s
                JOIN league l ON s.league_id = l.league_id
                WHERE l.name = 'NFL' AND s.year = %s
            """, (season_year,))
            
            result = self.cursor.fetchone()
            if result:
                return result[0]
            
            self.logger.error(f"Season {season_year} not found in database")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get season_id: {e}")
            return None
    
    def get_player_id_by_external_id(self, external_player_id: int) -> Optional[int]:
        """Get internal player_id from external_player_id"""
        try:
            self.cursor.execute("""
                SELECT player_id 
                FROM player 
                WHERE external_player_id = %s
            """, (external_player_id,))
            
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get player_id for external ID {external_player_id}: {e}")
            return None
    
    def get_team_id_by_external_key(self, external_team_id: int) -> Optional[int]:
        """Get internal team_id from external_team_key"""
        try:
            self.cursor.execute("""
                SELECT team_id 
                FROM team 
                WHERE external_team_key = %s
            """, (external_team_id,))
            
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Failed to get team_id for external key {external_team_id}: {e}")
            return None
    
    def get_all_teams(self) -> List[Tuple]:
        """
        Get all teams to process
        
        Returns:
            List of (team_id, external_team_key, name, abbrev) tuples
        """
        try:
            self.cursor.execute("""
                SELECT team_id, external_team_key, name, abbrev
                FROM team
                WHERE external_team_key IS NOT NULL
                ORDER BY name
            """)
            
            return self.cursor.fetchall()
            
        except Exception as e:
            self.logger.error(f"Failed to get teams: {e}")
            return []
    
    def get_team_by_external_key(self, external_team_key: int) -> Optional[Tuple]:
        """Get team info by external key"""
        try:
            self.cursor.execute("""
                SELECT team_id, external_team_key, name, abbrev
                FROM team
                WHERE external_team_key = %s
            """, (external_team_key,))
            
            return self.cursor.fetchone()
            
        except Exception as e:
            self.logger.error(f"Failed to get team: {e}")
            return None
    
    def upsert_player_statistics(
        self,
        player_id: int,
        team_id: int,
        records: List[Tuple]
    ) -> int:
        """
        Insert or update player statistics in batch
        
        Args:
            player_id: Internal database player_id
            team_id: Internal database team_id
            records: List of (season_id, stat_group, metric_name, metric_value) tuples
            
        Returns:
            Number of records inserted/updated
        """
        if not records:
            return 0
        
        try:
            # Prepare data with player_id, team_id, and timestamp
            now = datetime.utcnow()
            data_with_ids = [
                (player_id, team_id, r[0], r[1], r[2], r[3], now, 'api-sports')
                for r in records
            ]
            
            # Use INSERT ... ON CONFLICT to upsert
            execute_values(
                self.cursor,
                """
                INSERT INTO player_statistic 
                    (player_id, team_id, season_id, stat_group, metric_name, metric_value, pulled_at_utc, source)
                VALUES %s
                ON CONFLICT (player_id, team_id, season_id, stat_group, metric_name)
                DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    pulled_at_utc = EXCLUDED.pulled_at_utc
                """,
                data_with_ids
            )
            
            self.conn.commit()
            return len(records)
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Failed to upsert statistics: {e}")
            return 0
    
    def refresh_materialized_view(self):
        """Refresh the player_season_summary materialized view"""
        try:
            self.logger.info("Refreshing player_season_summary materialized view...")
            self.cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY player_season_summary")
            self.conn.commit()
            self.logger.info("✓ Materialized view refreshed successfully")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"✗ Failed to refresh materialized view: {e}")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("Database connection closed")


# ==================== Main ETL ====================

class PlayerStatisticsETL:
    """Main ETL orchestrator for player statistics"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.api_client = SportsAPIClient(
            config.api_key,
            config.api_base_url,
            self.logger
        )
        self.api_client.set_delay(config.delay_between_requests)
        self.transformer = PlayerStatisticsTransformer(self.logger)
        self.db_loader = PlayerStatisticsDatabaseLoader(self.logger)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def _process_team_statistics(
        self,
        external_team_id: int,
        team_name: str,
        season_id: int,
        db_team_id: int
    ) -> Tuple[int, int]:
        """
        Process statistics for all players on a team (1 API call!)
        
        Returns:
            Tuple of (players_processed, total_stats_loaded)
        """
        # Fetch all players for the team in one API call
        team_players_data = self.api_client.get_team_statistics(
            external_team_id,
            self.config.season
        )
        
        if not team_players_data:
            self.logger.warning(f"No statistics found for {team_name}")
            return 0, 0
        
        self.logger.info(f"Processing {len(team_players_data)} players from {team_name}")
        
        total_stats = 0
        players_processed = 0
        players_failed = 0
        
        for player_data in team_players_data:
            try:
                # Transform player statistics
                external_player_id, ext_team_id, records = \
                    self.transformer.transform_player_statistics(player_data, season_id)
                
                if not external_player_id:
                    players_failed += 1
                    continue
                
                # Get player name for logging
                player_name = player_data.get('player', {}).get('name', 'Unknown')
                
                # Find player in our database
                db_player_id = self.db_loader.get_player_id_by_external_id(external_player_id)
                
                if not db_player_id:
                    self.logger.debug(
                        f"Player {player_name} (external ID: {external_player_id}) "
                        f"not found in database - skipping"
                    )
                    players_failed += 1
                    continue
                
                if not records:
                    self.logger.debug(f"No statistics for {player_name}")
                    players_failed += 1
                    continue
                
                # Group records by team (in case player was traded)
                team_records = {}
                for record in records:
                    ext_team_id = record[0]
                    if ext_team_id not in team_records:
                        team_records[ext_team_id] = []
                    team_records[ext_team_id].append(record[1:])  # Remove team_id from tuple
                
                # Insert statistics for each team
                player_total_stats = 0
                for ext_team_id, team_stats in team_records.items():
                    # Get internal team_id
                    team_id = self.db_loader.get_team_id_by_external_key(ext_team_id)
                    if not team_id:
                        self.logger.warning(f"Team with external key {ext_team_id} not found")
                        continue
                    
                    # Insert into database
                    count = self.db_loader.upsert_player_statistics(
                        db_player_id,
                        team_id,
                        team_stats
                    )
                    player_total_stats += count
                
                if player_total_stats > 0:
                    total_stats += player_total_stats
                    players_processed += 1
                    self.logger.debug(f"  ✓ {player_name}: {player_total_stats} statistics")
                else:
                    players_failed += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process player: {e}")
                players_failed += 1
        
        self.logger.info(
            f"Team {team_name} summary: {players_processed} players, "
            f"{total_stats} stats loaded, {players_failed} failed"
        )
        return players_processed, total_stats
    
    def run(self) -> Dict:
        """Run the ETL pipeline"""
        start_time = datetime.now()
        self.logger.info("="*70)
        self.logger.info("NFL PLAYER STATISTICS ETL - Starting")
        self.logger.info(f"Season: {self.config.season}")
        self.logger.info(f"Mode: {'All teams (32 API calls)' if self.config.fetch_all else f'Team ID {self.config.team_id} (1 API call)'}")
        self.logger.info("="*70)
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            # Get season_id
            season_id = self.db_loader.get_season_id(self.config.season)
            if not season_id:
                return {
                    'success': False,
                    'error': f'Season {self.config.season} not found in database'
                }
            
            # Get teams to process
            if self.config.team_id:
                # Single team
                team_info = self.db_loader.get_team_by_external_key(self.config.team_id)
                if not team_info:
                    return {
                        'success': False,
                        'error': f'Team with external key {self.config.team_id} not found'
                    }
                teams = [team_info]
            else:
                # All teams
                teams = self.db_loader.get_all_teams()
            
            if not teams:
                return {'success': False, 'error': 'No teams found to process'}
            
            self.logger.info(f"Found {len(teams)} team(s) to process")
            self.logger.info(f"Total API calls needed: {len(teams)}")
            
            # Process each team
            total_stats = 0
            total_players = 0
            successful_teams = 0
            failed_teams = 0
            
            for idx, (db_team_id, ext_team_key, team_name, team_abbrev) in enumerate(teams, 1):
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"[{idx}/{len(teams)}] Processing: {team_name} ({team_abbrev})")
                self.logger.info(f"External Team Key: {ext_team_key}")
                self.logger.info(f"{'='*70}")
                
                try:
                    players_count, stats_count = self._process_team_statistics(
                        ext_team_key, team_name, season_id, db_team_id
                    )
                    
                    if stats_count > 0:
                        total_players += players_count
                        total_stats += stats_count
                        successful_teams += 1
                    else:
                        failed_teams += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {team_name}: {e}")
                    failed_teams += 1
                
                # Rate limiting between teams
                if idx < len(teams):
                    self.logger.debug(f"Waiting {self.config.delay_between_requests}s before next team...")
                    time.sleep(self.config.delay_between_requests)
            
            # Refresh materialized view if we loaded data
            if total_stats > 0:
                self.db_loader.refresh_materialized_view()
            
            # Summary
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info("\n" + "="*70)
            self.logger.info("ETL Summary:")
            self.logger.info(f"  API Requests Made: {self.api_client.get_request_count()}")
            self.logger.info(f"  Teams Processed: {len(teams)}")
            self.logger.info(f"  Successful Teams: {successful_teams}")
            self.logger.info(f"  Failed Teams: {failed_teams}")
            self.logger.info(f"  Total Players: {total_players}")
            self.logger.info(f"  Total Statistics Loaded: {total_stats}")
            self.logger.info(f"  Duration: {duration:.2f}s")
            self.logger.info("="*70)
            
            return {
                'success': True,
                'api_requests': self.api_client.get_request_count(),
                'teams_processed': len(teams),
                'successful_teams': successful_teams,
                'failed_teams': failed_teams,
                'total_players': total_players,
                'total_statistics': total_stats,
                'duration': duration
            }
            
        except Exception as e:
            self.logger.error(f"ETL failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
        
        finally:
            self.db_loader.close()
    
    def refresh_view_only(self) -> Dict:
        """Only refresh the materialized view (no API calls)"""
        start_time = datetime.now()
        self.logger.info("="*70)
        self.logger.info("Refreshing Materialized View Only")
        self.logger.info("="*70)
        
        try:
            self.db_loader.connect()
            self.db_loader.refresh_materialized_view()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info("="*70)
            
            return {
                'success': True,
                'view_refreshed': True,
                'duration': duration
            }
            
        except Exception as e:
            self.logger.error(f"View refresh failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
        
        finally:
            self.db_loader.close()


# ==================== CLI ====================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NFL Player Statistics ETL - Team-based fetching (only 32 API calls!)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all player stats for 2023 season (32 API calls - one per team!)
  python nfl_player_statistics_etl.py --season 2023 --all
  
  # Fetch stats for Kansas City Chiefs only (external_team_key=17, 1 API call)
  python nfl_player_statistics_etl.py --season 2023 --team-id 17
  
  # Fetch stats for Dallas Cowboys (external_team_key=8, 1 API call)
  python nfl_player_statistics_etl.py --season 2023 --team-id 8
  
  # Update existing stats
  python nfl_player_statistics_etl.py --season 2023 --all --update
  
  # Refresh materialized view only (no API calls)
  python nfl_player_statistics_etl.py --refresh-view

Environment Variables Required:
  API_SPORTS_KEY - Your API key from api-sports.io
  PGHOST, PGDATABASE, PGUSER, PGPASSWORD - Database credentials
  
Note: --team-id expects the external_team_key (API ID), not internal database team_id
      Kansas City Chiefs = 17, Dallas Cowboys = 8, etc.
        """
    )
    
    parser.add_argument('--season', type=int,
                        help='Season year (2022+, e.g., 2023, 2024)')
    parser.add_argument('--all', action='store_true',
                        help='Fetch all 32 NFL teams (32 API calls)')
    parser.add_argument('--team-id', type=int,
                        help='Fetch specific team by external_team_key (1 API call)')
    parser.add_argument('--update', action='store_true',
                        help='Update existing statistics')
    parser.add_argument('--refresh-view', action='store_true',
                        help='Only refresh materialized view (no API calls)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.refresh_view:
        # Refresh view only - no other args needed
        pass
    else:
        if not args.season:
            parser.error("--season is required (unless using --refresh-view)")
        
        if not args.all and not args.team_id:
            parser.error("Must specify either --all or --team-id")
    
    # Check environment variables
    required_vars = ['API_SPORTS_KEY', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Run ETL
    try:
        config = ETLConfig(args)
        etl = PlayerStatisticsETL(config)
        
        if args.refresh_view:
            result = etl.refresh_view_only()
        else:
            result = etl.run()
        
        sys.exit(0 if result.get('success') else 1)
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()