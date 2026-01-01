"""
NFL Player ETL Pipeline
=======================
Extracts player data from sports-api and loads into PostgreSQL database.
Supports single season ingestion with extensibility for multi-season processing.

Author: SmartLine Development Team
Version: 1.0.0
"""

import os
import sys
import http.client
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch


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


# ==================== Configuration ====================

@dataclass
class ETLConfig:
    """Configuration for the ETL pipeline"""
    api_key: str
    season: int
    batch_size: int = 100
    api_delay: float = 1.0  # Seconds between API calls to respect rate limits
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls, season: int) -> 'ETLConfig':
        """Create configuration from environment variables"""
        return cls(
            api_key=os.getenv('API_SPORTS_KEY', ''),
            season=season,
            batch_size=int(os.getenv('ETL_BATCH_SIZE', '100')),
            api_delay=float(os.getenv('API_DELAY', '1.0')),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )


# ==================== Logging Setup ====================

def setup_logging(config: ETLConfig) -> logging.Logger:
    """Configure logging for the ETL pipeline"""
    logger = logging.getLogger('nfl_player_etl')
    logger.setLevel(getattr(logging, config.log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_level))
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# ==================== API Client ====================

class SportsAPIClient:
    """Client for interacting with the sports-api"""
    
    def __init__(self, api_key: str, logger: logging.Logger, delay: float = 1.0):
        self.api_key = api_key
        self.logger = logger
        self.delay = delay
        self.base_url = "v1.american-football.api-sports.io"
        self.request_count = 0  # Track API requests
        self.cache = {}  # Simple in-memory cache
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to the API"""
        # Create cache key
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
        
        # Check cache first to avoid duplicate requests
        if cache_key in self.cache:
            self.logger.debug(f"Using cached response for {endpoint}")
            return self.cache[cache_key]
        
        try:
            conn = http.client.HTTPSConnection(self.base_url)
            headers = {'x-apisports-key': self.api_key}
            
            # Build query string
            query_string = ""
            if params:
                query_string = "?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            full_endpoint = f"{endpoint}{query_string}"
            
            # Increment request counter
            self.request_count += 1
            self.logger.info(f"API Request #{self.request_count}: {full_endpoint}")
            
            conn.request("GET", full_endpoint, headers=headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            conn.close()
            
            # Parse JSON
            result = json.loads(data)
            
            # Check for errors
            if result.get('errors'):
                self.logger.error(f"API Error: {result['errors']}")
                return None
            
            # Log API response info
            results_count = result.get('results', 0)
            self.logger.info(f"  ✓ Response: {results_count} results returned")
            
            # Cache the result
            self.cache[cache_key] = result
            
            # Rate limiting - wait between requests
            time.sleep(self.delay)
            
            return result
            
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None
    
    def get_all_teams_players(self, season: int, team_mapping: Dict[int, int] = None) -> List[Dict]:
        """
        Fetch all players for a season by iterating through all teams
        
        The API requires a team parameter, so we need to make one request per team.
        For NFL, this means 32 API requests per season.
        
        Args:
            season: The season year (e.g., 2023)
            team_mapping: Dict mapping external_team_key -> internal team_id
            
        Returns:
            List of all player dictionaries from all teams (with team_id populated)
        """
        self.logger.info(f"Fetching players for ALL teams in season {season}")
        self.logger.info(f"Note: API requires team parameter, so this will make ~32 requests (one per team)")
        
        all_players = []
        
        # Use provided team mapping or default to 1-32
        if team_mapping:
            team_keys = list(team_mapping.keys())
            self.logger.info(f"Using {len(team_keys)} teams from database")
        else:
            # NFL team IDs from the API (1-32)
            team_keys = list(range(1, 33))
            team_mapping = {}  # Empty mapping, will need to resolve later
            self.logger.info(f"Using default NFL teams (1-32)")
        
        teams_processed = 0
        teams_failed = 0
        
        for external_team_key in team_keys:
            try:
                players = self.get_players_by_team(external_team_key, season)
                
                if players:
                    # Add team_id to each player
                    internal_team_id = team_mapping.get(external_team_key)
                    for player in players:
                        player['_team_id'] = internal_team_id  # Store for later mapping
                        player['_external_team_key'] = external_team_key
                    
                    all_players.extend(players)
                    teams_processed += 1
                    self.logger.info(f"  ✓ Team {external_team_key}: {len(players)} players (team_id: {internal_team_id})")
                else:
                    # Some team IDs might not exist or have no data
                    self.logger.debug(f"  - Team {external_team_key}: No players found")
                    
            except Exception as e:
                teams_failed += 1
                self.logger.warning(f"  ✗ Team {external_team_key}: Failed - {str(e)}")
                continue
        
        self.logger.info(f"Completed: {teams_processed} teams processed, {teams_failed} failed")
        self.logger.info(f"Total players retrieved: {len(all_players)}")
        
        return all_players
    
    def get_players_by_season(self, season: int, team_mapping: Dict[int, int] = None) -> List[Dict]:
        """
        Fetch all players for a given season
        
        Since the API requires a team parameter, this method fetches
        players for all NFL teams (32 requests).
        
        Args:
            season: The season year (e.g., 2023)
            team_mapping: Dict mapping external_team_key -> internal team_id
            
        Returns:
            List of player dictionaries with team information
        """
        return self.get_all_teams_players(season, team_mapping)
    
    def get_players_by_team(self, team_id: int, season: int) -> List[Dict]:
        """
        Fetch players for a specific team in a season
        NOTE: Only use this if you need team-specific data
        For full season ingestion, use get_players_by_season() instead
        
        Args:
            team_id: The external team ID
            season: The season year
            
        Returns:
            List of player dictionaries
        """
        self.logger.info(f"Fetching players for team {team_id}, season {season}")
        
        params = {'team': team_id, 'season': season}
        result = self._make_request('/players', params)
        
        if result and result.get('response'):
            players = result['response']
            self.logger.info(f"✓ Retrieved {len(players)} players for team {team_id}")
            return players
        
        return []
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict]:
        """
        Fetch a specific player by ID
        NOTE: This makes 1 API request per player - avoid using in loops!
        Only use for testing or single player lookups
        
        Args:
            player_id: The player's ID in the API
            
        Returns:
            Player dictionary or None
        """
        self.logger.warning(f"Single player fetch (uses 1 API request)")
        
        params = {'id': player_id}
        result = self._make_request('/players', params)
        
        if result and result.get('response') and len(result['response']) > 0:
            return result['response'][0]
        
        return None
    
    def get_request_count(self) -> int:
        """Get the total number of API requests made"""
        return self.request_count


# ==================== Data Transformer ====================

class PlayerDataTransformer:
    """Transform API player data to database format"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def transform_player(self, api_player: Dict, team_id: Optional[int] = None) -> Dict:
        """
        Transform API player data to database format
        
        API Format:
        {
            "id": 1,
            "name": "Derek Carr",
            "age": 31,
            "height": "6' 3\"",
            "weight": "210 lbs",
            "college": "Fresno State",
            "group": "Offense",
            "position": "QB",
            "number": 4,
            "salary": "$19,375,000",
            "experience": 9,
            "image": "https://...",
            "_team_id": 1,  # Added by API client
            "_external_team_key": 5  # Added by API client
        }
        
        DB Format:
        {
            "external_player_id": 1,
            "full_name": "Derek Carr",
            "position": "QB",
            "team_id": 1,
            "jersey_number": 4,
            "height": "6' 3\"",
            "weight": "210 lbs",
            "age": 31,
            "college": "Fresno State",
            "experience_years": 9,
            "salary": "$19,375,000",
            "image_url": "https://..."
        }
        
        Args:
            api_player: Player data from API
            team_id: Internal team_id (if known, overrides API data)
            
        Returns:
            Transformed player dictionary
        """
        # Use provided team_id or extract from API player data
        final_team_id = team_id if team_id is not None else api_player.get('_team_id')
        
        return {
            'external_player_id': api_player.get('id'),
            'full_name': api_player.get('name'),
            'position': api_player.get('position'),
            'team_id': final_team_id,
            'jersey_number': api_player.get('number'),
            'height': api_player.get('height'),
            'weight': api_player.get('weight'),
            'age': api_player.get('age'),
            'college': api_player.get('college'),
            'experience_years': api_player.get('experience'),
            'salary': api_player.get('salary'),
            'image_url': api_player.get('image'),
            'player_group': api_player.get('group')  # Offense/Defense/Special Teams
        }


# ==================== Database Loader ====================

class PlayerDatabaseLoader:
    """Load player data into PostgreSQL database"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.logger.info("Connecting to database...")
            self.conn = get_conn()
            self.cursor = self.conn.cursor()
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("Database connection closed")
    
    def get_team_mapping(self) -> Dict[int, int]:
        """
        Get mapping of external_team_key to internal team_id
        
        Returns:
            Dictionary mapping external_team_key -> team_id
        """
        query = """
            SELECT external_team_key, team_id 
            FROM team 
            WHERE external_team_key IS NOT NULL
            ORDER BY external_team_key
        """
        
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            mapping = {external_key: team_id for external_key, team_id in results}
            self.logger.info(f"Loaded team mapping: {len(mapping)} teams")
            return mapping
        except Exception as e:
            self.logger.error(f"Error fetching team mapping: {str(e)}")
            return {}
    
    def get_all_external_team_keys(self) -> List[int]:
        """
        Get all external_team_key values from the database
        
        Returns:
            List of external team keys
        """
        query = """
            SELECT external_team_key 
            FROM team 
            WHERE external_team_key IS NOT NULL
            ORDER BY external_team_key
        """
        
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching team keys: {str(e)}")
            return []
    
    def get_team_id_by_external_key(self, external_team_key: int) -> Optional[int]:
        """
        Get internal team_id from external_team_key
        
        Args:
            external_team_key: The team's external ID
            
        Returns:
            Internal team_id or None
        """
        query = """
            SELECT team_id 
            FROM team 
            WHERE external_team_key = %s
        """
        
        try:
            self.cursor.execute(query, (external_team_key,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error fetching team_id: {str(e)}")
            return None
    
    def ensure_player_table_exists(self):
        """
        Ensure player table has all necessary columns.
        The base schema has: player_id, full_name, position, team_id
        
        We need to add additional columns for comprehensive player data.
        """
        additional_columns = [
            ("external_player_id", "INTEGER UNIQUE"),
            ("jersey_number", "SMALLINT"),
            ("height", "TEXT"),
            ("weight", "TEXT"),
            ("age", "SMALLINT"),
            ("college", "TEXT"),
            ("experience_years", "SMALLINT"),
            ("salary", "TEXT"),
            ("image_url", "TEXT"),
            ("player_group", "TEXT"),
            ("created_at", "TIMESTAMPTZ DEFAULT NOW()"),
            ("updated_at", "TIMESTAMPTZ DEFAULT NOW()")
        ]
        
        for column_name, column_def in additional_columns:
            try:
                alter_query = f"""
                    ALTER TABLE player 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                """
                self.cursor.execute(alter_query)
                self.conn.commit()
                self.logger.debug(f"Ensured column exists: {column_name}")
            except Exception as e:
                self.logger.warning(f"Could not add column {column_name}: {str(e)}")
                self.conn.rollback()
    
    def upsert_player(self, player_data: Dict) -> Tuple[bool, str]:
        """
        Insert or update a player record
        
        Args:
            player_data: Transformed player data
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if player exists by external_player_id
            check_query = """
                SELECT player_id FROM player 
                WHERE external_player_id = %s
            """
            self.cursor.execute(check_query, (player_data['external_player_id'],))
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing player
                update_query = """
                    UPDATE player SET
                        full_name = %s,
                        position = %s,
                        team_id = %s,
                        jersey_number = %s,
                        height = %s,
                        weight = %s,
                        age = %s,
                        college = %s,
                        experience_years = %s,
                        salary = %s,
                        image_url = %s,
                        player_group = %s,
                        updated_at = NOW()
                    WHERE external_player_id = %s
                """
                
                self.cursor.execute(update_query, (
                    player_data['full_name'],
                    player_data['position'],
                    player_data['team_id'],
                    player_data['jersey_number'],
                    player_data['height'],
                    player_data['weight'],
                    player_data['age'],
                    player_data['college'],
                    player_data['experience_years'],
                    player_data['salary'],
                    player_data['image_url'],
                    player_data['player_group'],
                    player_data['external_player_id']
                ))
                
                return True, f"Updated player: {player_data['full_name']}"
            else:
                # Insert new player
                insert_query = """
                    INSERT INTO player (
                        external_player_id, full_name, position, team_id,
                        jersey_number, height, weight, age, college,
                        experience_years, salary, image_url, player_group
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                self.cursor.execute(insert_query, (
                    player_data['external_player_id'],
                    player_data['full_name'],
                    player_data['position'],
                    player_data['team_id'],
                    player_data['jersey_number'],
                    player_data['height'],
                    player_data['weight'],
                    player_data['age'],
                    player_data['college'],
                    player_data['experience_years'],
                    player_data['salary'],
                    player_data['image_url'],
                    player_data['player_group']
                ))
                
                return True, f"Inserted player: {player_data['full_name']}"
                
        except Exception as e:
            self.logger.error(f"Error upserting player {player_data.get('full_name')}: {str(e)}")
            return False, str(e)
    
    def batch_upsert_players(self, players_data: List[Dict]) -> Dict[str, int]:
        """
        Batch upsert players
        
        Args:
            players_data: List of transformed player dictionaries
            
        Returns:
            Dictionary with counts: {inserted: int, updated: int, failed: int}
        """
        stats = {'inserted': 0, 'updated': 0, 'failed': 0}
        
        for player_data in players_data:
            success, message = self.upsert_player(player_data)
            
            if success:
                if 'Updated' in message:
                    stats['updated'] += 1
                else:
                    stats['inserted'] += 1
                self.logger.debug(message)
            else:
                stats['failed'] += 1
        
        self.conn.commit()
        return stats


# ==================== ETL Orchestrator ====================

class PlayerETL:
    """Main ETL orchestrator for player data"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = setup_logging(config)
        self.api_client = SportsAPIClient(config.api_key, self.logger, config.api_delay)
        self.transformer = PlayerDataTransformer(self.logger)
        self.db_loader = PlayerDatabaseLoader(self.logger)
    
    def run(self) -> Dict[str, any]:
        """
        Run the complete ETL pipeline
        
        Returns:
            Statistics dictionary
        """
        start_time = datetime.now()
        self.logger.info("="*60)
        self.logger.info(f"Starting NFL Player ETL for season {self.config.season}")
        self.logger.info("="*60)
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            # Ensure table structure
            self.db_loader.ensure_player_table_exists()
            
            # Get team mapping (external_team_key -> team_id)
            team_mapping = self.db_loader.get_team_mapping()
            
            if not team_mapping:
                self.logger.warning("No teams found in database! Players will not have team assignments.")
                self.logger.warning("Make sure you have teams in your database with external_team_key values.")
            else:
                self.logger.info(f"Using team mapping for {len(team_mapping)} teams")
            
            # Extract: Fetch all players for the season with team mapping
            api_players = self.api_client.get_players_by_season(self.config.season, team_mapping)
            
            if not api_players:
                self.logger.warning("No players retrieved from API")
                return {'status': 'no_data', 'players_processed': 0}
            
            # Transform: Convert API format to DB format
            transformed_players = []
            players_with_teams = 0
            players_without_teams = 0
            
            for api_player in api_players:
                transformed = self.transformer.transform_player(api_player)
                transformed_players.append(transformed)
                
                if transformed['team_id'] is not None:
                    players_with_teams += 1
                else:
                    players_without_teams += 1
            
            self.logger.info(f"Transformed {len(transformed_players)} players")
            self.logger.info(f"  - With team assignment: {players_with_teams}")
            self.logger.info(f"  - Without team assignment: {players_without_teams}")
            
            if players_without_teams > 0:
                self.logger.warning(f"{players_without_teams} players will be inserted without team assignments")
                self.logger.warning("This usually means their external_team_key is not in your database")
            
            # Load: Insert/update players in database
            stats = self.db_loader.batch_upsert_players(transformed_players)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Summary
            self.logger.info("="*60)
            self.logger.info("ETL Summary:")
            self.logger.info(f"  Season: {self.config.season}")
            self.logger.info(f"  API Requests Made: {self.api_client.get_request_count()}")
            self.logger.info(f"  Total Players: {len(api_players)}")
            self.logger.info(f"  Inserted: {stats['inserted']}")
            self.logger.info(f"  Updated: {stats['updated']}")
            self.logger.info(f"  Failed: {stats['failed']}")
            self.logger.info(f"  Duration: {duration:.2f}s")
            self.logger.info("="*60)
            
            return {
                'status': 'success',
                'season': self.config.season,
                'api_requests': self.api_client.get_request_count(),
                'players_processed': len(api_players),
                'inserted': stats['inserted'],
                'updated': stats['updated'],
                'failed': stats['failed'],
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.logger.error(f"ETL pipeline failed: {str(e)}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e)
            }
        
        finally:
            self.db_loader.disconnect()
    
    def run_for_team(self, external_team_key: int) -> Dict[str, any]:
        """
        Run ETL for a specific team
        
        Args:
            external_team_key: The team's external ID
            
        Returns:
            Statistics dictionary
        """
        start_time = datetime.now()
        self.logger.info(f"Starting team-specific ETL for team {external_team_key}, season {self.config.season}")
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            # Ensure table structure
            self.db_loader.ensure_player_table_exists()
            
            # Get internal team_id
            team_id = self.db_loader.get_team_id_by_external_key(external_team_key)
            
            if not team_id:
                self.logger.error(f"Team not found with external_team_key: {external_team_key}")
                return {'status': 'team_not_found', 'external_team_key': external_team_key}
            
            # Extract: Fetch players for this team
            api_players = self.api_client.get_players_by_team(external_team_key, self.config.season)
            
            if not api_players:
                self.logger.warning(f"No players retrieved for team {external_team_key}")
                return {'status': 'no_data', 'team_id': team_id}
            
            # Transform
            transformed_players = []
            for api_player in api_players:
                transformed = self.transformer.transform_player(api_player, team_id)
                transformed_players.append(transformed)
            
            # Load
            stats = self.db_loader.batch_upsert_players(transformed_players)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Team ETL complete: API requests: {self.api_client.get_request_count()}, {stats['inserted']} inserted, {stats['updated']} updated, {stats['failed']} failed in {duration:.2f}s")
            
            return {
                'status': 'success',
                'team_id': team_id,
                'external_team_key': external_team_key,
                'season': self.config.season,
                'api_requests': self.api_client.get_request_count(),
                'players_processed': len(api_players),
                'inserted': stats['inserted'],
                'updated': stats['updated'],
                'failed': stats['failed'],
                'duration_seconds': duration
            }
            
        except Exception as e:
            self.logger.error(f"Team ETL failed: {str(e)}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}
        
        finally:
            self.db_loader.disconnect()


# ==================== CLI ====================

def main():
    """Main entry point for CLI execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NFL Player ETL Pipeline')
    parser.add_argument('--season', type=int, required=True, help='Season year (e.g., 2023)')
    parser.add_argument('--team', type=int, help='External team key (optional, for team-specific ETL)')
    parser.add_argument('--api-key', help='Sports API key (or set SPORTS_API_KEY env var)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for database operations')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Override environment variables with CLI arguments if provided
    if args.api_key:
        os.environ['SPORTS_API_KEY'] = args.api_key
    if args.batch_size:
        os.environ['ETL_BATCH_SIZE'] = str(args.batch_size)
    if args.log_level:
        os.environ['LOG_LEVEL'] = args.log_level
    
    # Create configuration
    config = ETLConfig.from_env(args.season)
    
    # Validate configuration
    if not config.api_key:
        print("Error: SPORTS_API_KEY environment variable or --api-key argument is required")
        sys.exit(1)
    
    # Validate database environment variables
    required_db_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_db_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required database environment variables: {', '.join(missing_vars)}")
        print("Required: PGHOST, PGDATABASE, PGUSER, PGPASSWORD")
        print("Optional: PGPORT (defaults to 5432)")
        sys.exit(1)
    
    # Create and run ETL
    etl = PlayerETL(config)
    
    if args.team:
        result = etl.run_for_team(args.team)
    else:
        result = etl.run()
    
    # Exit with appropriate code
    if result.get('status') == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()