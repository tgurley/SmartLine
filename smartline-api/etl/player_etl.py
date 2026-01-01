#!/usr/bin/env python3
"""
Multi-Sport Player ETL
======================
Fetches player data from API-SPORTS and loads into database.
Supports: NFL, NCAAF, NBA, NCAAB, Soccer leagues
Skips: NHL, MLB (no player endpoints available - placeholder for future)

Usage:
    python player_etl.py --sport NFL --season 2024 --all
    python player_etl.py --sport NBA --season 2024 --all
    python player_etl.py --sport MLS --season 2024 --all --league-id 253
    python player_etl.py --sport NFL --season 2024 --team-id 1
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
from dotenv import load_dotenv

load_dotenv()


# ==================== Sport Configuration ====================

SPORT_CONFIG = {
    'NFL': {
        'sport_code': 'NFL',
        'api_url': 'https://v1.american-football.api-sports.io',
        'default_league_id': 1,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'NCAAF': {
        'sport_code': 'NCAAF',
        'api_url': 'https://v1.american-football.api-sports.io',
        'default_league_id': 2,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'NBA': {
        'sport_code': 'NBA',
        'api_url': 'https://v2.nba.api-sports.io',
        'default_league_id': 'standard',
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'NCAAB': {
        'sport_code': 'NCAAB',
        'api_url': 'https://v1.basketball.api-sports.io',
        'default_league_id': 116,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'MLB': {
        'sport_code': 'MLB',
        'api_url': '',  # No player endpoint available
        'default_league_id': 1,
        'player_endpoint': None,
        'supports_team_param': False,
        'supports_season_param': False,
        'batch_by_team': False
    },
    'NHL': {
        'sport_code': 'NHL',
        'api_url': '',  # No player endpoint available
        'default_league_id': 57,
        'player_endpoint': None,
        'supports_team_param': False,
        'supports_season_param': False,
        'batch_by_team': False
    },
    'MLS': {
        'sport_code': 'MLS',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 253,
        'player_endpoint': '/players',  # Note: /players/profiles doesn't support team param
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'EPL': {
        'sport_code': 'EPL',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 39,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'LA_LIGA': {
        'sport_code': 'LA_LIGA',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 140,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'BUNDESLIGA': {
        'sport_code': 'BUNDESLIGA',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 78,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'SERIE_A': {
        'sport_code': 'SERIE_A',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 135,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'LIGUE_1': {
        'sport_code': 'LIGUE_1',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 61,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    },
    'CHAMPIONS': {
        'sport_code': 'CHAMPIONS',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 2,
        'player_endpoint': '/players',
        'supports_team_param': True,
        'supports_season_param': True,
        'batch_by_team': True
    }
}


# ==================== Configuration ====================

class ETLConfig:
    """Configuration for Player ETL"""
    
    def __init__(self, args):
        self.api_key = os.environ.get('API_SPORTS_KEY')
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY environment variable not set")
        
        # Validate sport
        if args.sport not in SPORT_CONFIG:
            raise ValueError(f"Unknown sport: {args.sport}. Valid: {list(SPORT_CONFIG.keys())}")
        
        self.sport = args.sport
        self.sport_config = SPORT_CONFIG[args.sport]
        self.api_base_url = self.sport_config['api_url']
        self.api_league_id = args.league_id or self.sport_config['default_league_id']
        self.season = args.season
        self.team_id = args.team_id
        self.player_id = args.player_id
        self.fetch_all = args.all
        self.update_only = args.update
        self.delay_between_requests = 1.0
        
        # Check if sport has player endpoint
        if not self.api_base_url or not self.sport_config.get('player_endpoint'):
            raise ValueError(
                f"{args.sport} does not have a player endpoint available. "
                f"Supported sports: NFL, NCAAF, NBA, NCAAB, MLS, EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, CHAMPIONS"
            )


# ==================== Database Helpers ====================

def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )


def get_sport_id(cursor, sport_code: str) -> int:
    """Get sport_id from sport_code"""
    cursor.execute(
        "SELECT sport_id FROM sport_type WHERE sport_code = %s",
        (sport_code,)
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Unknown sport_code in database: {sport_code}")
    return result[0]


# ==================== API Client ====================

class SportsAPIClient:
    """Unified client for all API-SPORTS player endpoints"""
    
    def __init__(self, api_key: str, base_url: str, sport: str, sport_config: Dict, logger: logging.Logger):
        self.api_key = api_key
        self.base_url = base_url
        self.sport = sport
        self.sport_config = sport_config
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
            time.sleep(1.0)
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None
    
    def get_players_by_team(self, team_external_id: int, season: str) -> List[Dict]:
        """Get all players for a specific team"""
        endpoint = self.sport_config['player_endpoint']
        
        params = {'team': team_external_id}
        
        if self.sport_config.get('supports_season_param'):
            params['season'] = season
        
        data = self._make_request(endpoint, params)
        
        if not data or 'response' not in data:
            return []
        
        return data['response']
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict]:
        """Get single player by ID"""
        endpoint = self.sport_config['player_endpoint']
        
        params = {'id': player_id}
        
        data = self._make_request(endpoint, params)
        
        if not data or 'response' not in data or len(data['response']) == 0:
            return None
        
        return data['response'][0]
    
    def get_request_count(self) -> int:
        """Get total API requests made"""
        return self.request_count


# ==================== Data Transformer ====================

class PlayerDataTransformer:
    """Transform API player data to database format"""
    
    def __init__(self, sport: str, logger: logging.Logger):
        self.sport = sport
        self.logger = logger
    
    def transform_player(self, api_player: Dict, team_id: Optional[int] = None) -> Optional[Dict]:
        """Transform API player to DB format based on sport"""
        
        try:
            if self.sport in ['NFL', 'NCAAF']:
                return self._transform_american_football_player(api_player, team_id)
            elif self.sport == 'NBA':
                return self._transform_nba_player(api_player, team_id)
            elif self.sport == 'NCAAB':
                return self._transform_basketball_player(api_player, team_id)
            elif self.sport in ['MLS', 'EPL', 'LA_LIGA', 'BUNDESLIGA', 'SERIE_A', 'LIGUE_1', 'CHAMPIONS']:
                return self._transform_soccer_player(api_player, team_id)
            else:
                self.logger.warning(f"Unknown sport: {self.sport}")
                return None
                
        except Exception as e:
            self.logger.error(f"Transform error for player: {str(e)}")
            return None
    
    def _transform_american_football_player(self, api_player: Dict, team_id: Optional[int]) -> Dict:
        """Transform NFL/NCAAF player data"""
        # API structure: {id, name, age, height, weight, college, group, position, number, salary, experience, image}
        
        return {
            'external_player_id': api_player.get('id'),
            'full_name': api_player.get('name'),
            'position': api_player.get('position'),
            'team_id': team_id,
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
    
    def _transform_nba_player(self, api_player: Dict, team_id: Optional[int]) -> Dict:
        """Transform NBA player data"""
        # API structure: {id, firstname, lastname, birth{date, country}, height{feets, inches, meters}, 
        #                 weight{pounds, kilograms}, college, nba{start, pro}, leagues{standard{jersey, pos}}}
        
        first_name = api_player.get('firstname', '')
        last_name = api_player.get('lastname', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Extract height
        height_data = api_player.get('height', {})
        if height_data:
            feet = height_data.get('feets', '')
            inches = height_data.get('inches', '')
            height = f"{feet}' {inches}\"" if feet and inches else None
        else:
            height = None
        
        # Extract weight
        weight_data = api_player.get('weight', {})
        weight = f"{weight_data.get('pounds')} lbs" if weight_data and weight_data.get('pounds') else None
        
        # Extract position and jersey from standard league
        leagues = api_player.get('leagues', {})
        standard = leagues.get('standard', {})
        
        # Calculate age from birth date
        age = None
        birth_data = api_player.get('birth', {})
        if birth_data and birth_data.get('date'):
            try:
                birth_date = datetime.strptime(birth_data['date'], '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
            except:
                pass
        
        return {
            'external_player_id': api_player.get('id'),
            'full_name': full_name,
            'position': standard.get('pos'),
            'team_id': team_id,
            'jersey_number': standard.get('jersey'),
            'height': height,
            'weight': weight,
            'age': age,
            'college': api_player.get('college'),
            'experience_years': api_player.get('nba', {}).get('pro'),
            'salary': None,  # NBA API doesn't provide salary
            'image_url': None,  # NBA API doesn't provide image URL
            'player_group': None
        }
    
    def _transform_basketball_player(self, api_player: Dict, team_id: Optional[int]) -> Dict:
        """Transform NCAAB player data (Basketball API)"""
        # Similar to NBA but may have different structure
        # For now, use same transformation as NBA
        return self._transform_nba_player(api_player, team_id)
    
    def _transform_soccer_player(self, api_player: Dict, team_id: Optional[int]) -> Dict:
        """Transform Soccer player data"""
        # API structure (from /players): nested under 'player' key
        # {player: {id, name, firstname, lastname, age, birth{date, place, country}, 
        #           nationality, height, weight, number, photo},
        #  statistics: [{team, league, games: {position, ...}, ...}]}
        
        player_data = api_player.get('player', api_player)  # Handle both nested and flat structures
        
        # Position is in statistics[0].games.position, NOT in player.position
        stats = api_player.get('statistics', [])
        position = None
        if stats and len(stats) > 0:
            games = stats[0].get('games', {})
            position = games.get('position')
        
        # Normalize height/weight to include units if missing
        height = player_data.get('height')
        if height and not height.endswith('cm'):
            height = f"{height} cm"
        
        weight = player_data.get('weight')
        if weight and not weight.endswith('kg'):
            weight = f"{weight} kg"
        
        current_team_id = team_id  # Use provided team_id from batch fetch
        
        return {
            'external_player_id': player_data.get('id'),
            'full_name': player_data.get('name'),
            'position': position,  # From statistics[0].games.position
            'team_id': current_team_id,
            'jersey_number': player_data.get('number'),
            'height': height,
            'weight': weight,
            'age': player_data.get('age'),
            'college': None,  # Soccer players don't have college
            'experience_years': None,
            'salary': None,
            'image_url': player_data.get('photo'),
            'player_group': None
        }


# ==================== Database Loader ====================

class PlayerDatabaseLoader:
    """Load player data into database with update detection"""
    
    def __init__(self, sport: str, sport_config: Dict, logger: logging.Logger):
        self.sport = sport
        self.sport_config = sport_config
        self.logger = logger
        self.conn = None
        self.cursor = None
        self.sport_id = None
    
    def connect(self):
        """Connect to database and get sport_id"""
        self.conn = get_conn()
        self.cursor = self.conn.cursor()
        self.sport_id = get_sport_id(self.cursor, self.sport_config['sport_code'])
        self.logger.info(f"Connected to database. sport_id={self.sport_id}")
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            self.cursor.execute("SELECT 1")
        except:
            self.logger.warning("Database connection lost, reconnecting...")
            self.connect()
    
    def get_existing_player_data(self, external_player_id: int) -> Optional[Dict]:
        """Get existing player data from database for update detection"""
        self.cursor.execute("""
            SELECT player_id, full_name, position, team_id, jersey_number, 
                   height, weight, age, college, experience_years, salary,
                   image_url, player_group, updated_at
            FROM player
            WHERE external_player_id = %s AND sport_id = %s
        """, (external_player_id, self.sport_id))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return {
            'player_id': row[0],
            'full_name': row[1],
            'position': row[2],
            'team_id': row[3],
            'jersey_number': row[4],
            'height': row[5],
            'weight': row[6],
            'age': row[7],
            'college': row[8],
            'experience_years': row[9],
            'salary': row[10],
            'image_url': row[11],
            'player_group': row[12],
            'updated_at': row[13]
        }
    
    def _should_update(self, new_data: Dict, existing_data: Dict) -> bool:
        """Determine if player data should be updated based on changes"""
        # Fields to check for updates (excluding player_id and updated_at)
        check_fields = [
            'full_name', 'position', 'team_id', 'jersey_number',
            'height', 'weight', 'age', 'college', 'experience_years',
            'salary', 'image_url', 'player_group'
        ]
        
        for field in check_fields:
            new_val = new_data.get(field)
            existing_val = existing_data.get(field)
            
            # If new data has a value and it's different from existing, update
            if new_val is not None and new_val != existing_val:
                self.logger.debug(f"Update needed: {field} changed from {existing_val} to {new_val}")
                return True
        
        return False
    
    def upsert_players(self, players: List[Dict]) -> Dict:
        """Insert or update players in database"""
        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for idx, player in enumerate(players):
            # Connection health check every 50 players
            if idx > 0 and idx % 50 == 0:
                self._ensure_connection()
                self.logger.info(f"Progress: {idx}/{len(players)} players processed")
            
            try:
                external_player_id = player.get('external_player_id')
                
                if not external_player_id:
                    self.logger.warning(f"Skipping player with no external_player_id: {player.get('full_name')}")
                    stats['skipped'] += 1
                    continue
                
                # Check if player exists
                existing = self.get_existing_player_data(external_player_id)
                
                if existing:
                    # Player exists - check if we need to update
                    if self._should_update(player, existing):
                        self._update_player(existing['player_id'], player)
                        stats['updated'] += 1
                        self.logger.debug(f"Updated: {player.get('full_name')} (#{external_player_id})")
                    else:
                        stats['skipped'] += 1
                        self.logger.debug(f"No changes for: {player.get('full_name')} (#{external_player_id})")
                else:
                    # New player - insert
                    self._insert_player(player)
                    stats['inserted'] += 1
                    self.logger.debug(f"Inserted: {player.get('full_name')} (#{external_player_id})")
                
            except Exception as e:
                self.logger.error(f"Error upserting player {player.get('full_name')}: {str(e)}")
                stats['errors'] += 1
                continue
        
        self.conn.commit()
        return stats
    
    def _insert_player(self, player: Dict):
        """Insert new player"""
        self.cursor.execute("""
            INSERT INTO player (
                external_player_id, sport_id, full_name, position, team_id,
                jersey_number, height, weight, age, college, experience_years,
                salary, image_url, player_group, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            player.get('external_player_id'),
            self.sport_id,
            player.get('full_name'),
            player.get('position'),
            player.get('team_id'),
            player.get('jersey_number'),
            player.get('height'),
            player.get('weight'),
            player.get('age'),
            player.get('college'),
            player.get('experience_years'),
            player.get('salary'),
            player.get('image_url'),
            player.get('player_group')
        ))
    
    def _update_player(self, player_id: int, player: Dict):
        """Update existing player"""
        self.cursor.execute("""
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
            WHERE player_id = %s
        """, (
            player.get('full_name'),
            player.get('position'),
            player.get('team_id'),
            player.get('jersey_number'),
            player.get('height'),
            player.get('weight'),
            player.get('age'),
            player.get('college'),
            player.get('experience_years'),
            player.get('salary'),
            player.get('image_url'),
            player.get('player_group'),
            player_id
        ))
    
    def get_teams_for_sport(self, league_id: Optional[int] = None) -> List[Tuple[int, int]]:
        """Get all teams for this sport from database (returns team_id, external_team_key)"""
        query = """
            SELECT team_id, external_team_key
            FROM team
            WHERE sport_id = %s
        """
        params = [self.sport_id]
        
        if league_id:
            query += " AND league_id = %s"
            params.append(league_id)
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ==================== Main ETL ====================

class PlayerETL:
    """Main ETL orchestrator"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.api_client = SportsAPIClient(
            config.api_key,
            config.api_base_url,
            config.sport,
            config.sport_config,
            self.logger
        )
        self.transformer = PlayerDataTransformer(config.sport, self.logger)
        self.db_loader = PlayerDatabaseLoader(
            config.sport,
            config.sport_config,
            self.logger
        )
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def run(self) -> Dict:
        """Run the ETL pipeline"""
        start_time = datetime.now()
        self.logger.info("="*70)
        self.logger.info(f"{self.config.sport} PLAYER ETL - Starting")
        self.logger.info("="*70)
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            all_players = []
            
            if self.config.player_id:
                # Fetch single player by ID
                self.logger.info(f"Fetching player ID: {self.config.player_id}")
                api_player = self.api_client.get_player_by_id(self.config.player_id)
                if api_player:
                    all_players.append((api_player, None))
            
            elif self.config.team_id:
                # Fetch players for specific team
                self.logger.info(f"Fetching players for team ID: {self.config.team_id}")
                
                # Get internal team_id from database
                db_team_id = self._get_db_team_id(self.config.team_id)
                
                api_players = self.api_client.get_players_by_team(
                    self.config.team_id,
                    self.config.season
                )
                all_players = [(p, db_team_id) for p in api_players]
            
            elif self.config.fetch_all:
                # Fetch all teams and then all players for each team
                self.logger.info(f"Fetching all players for {self.config.sport}")
                
                # Get league_id from database if needed
                db_league_id = self._get_db_league_id() if hasattr(self, '_get_db_league_id') else None
                
                teams = self.db_loader.get_teams_for_sport(db_league_id)
                self.logger.info(f"Found {len(teams)} teams to process")
                
                for idx, (db_team_id, external_team_key) in enumerate(teams):
                    self.logger.info(f"Processing team {idx+1}/{len(teams)}: external_key={external_team_key}")
                    
                    api_players = self.api_client.get_players_by_team(
                        external_team_key,
                        self.config.season
                    )
                    
                    if api_players:
                        self.logger.info(f"  Found {len(api_players)} players for team {external_team_key}")
                        all_players.extend([(p, db_team_id) for p in api_players])
                    else:
                        self.logger.warning(f"  No players found for team {external_team_key}")
            
            if not all_players:
                self.logger.warning("No players found!")
                return {'success': False, 'error': 'No players found'}
            
            self.logger.info(f"Total players fetched: {len(all_players)}")
            
            # Transform: Convert API format to DB format
            transformed_players = []
            skipped_count = 0
            
            for api_player, team_id in all_players:
                result = self.transformer.transform_player(api_player, team_id)
                if result:
                    transformed_players.append(result)
                else:
                    skipped_count += 1
            
            if skipped_count > 0:
                self.logger.info(f"Skipped {skipped_count} invalid players")
            
            self.logger.info(f"Transformed {len(transformed_players)} players")
            
            if not transformed_players:
                self.logger.warning("No valid players after transformation!")
                return {'success': False, 'error': 'No valid players to load'}
            
            # Load: Insert/update in database
            stats = self.db_loader.upsert_players(transformed_players)
            
            # Summary
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info("="*70)
            self.logger.info("ETL Summary:")
            self.logger.info(f"  Sport: {self.config.sport}")
            self.logger.info(f"  Season: {self.config.season}")
            self.logger.info(f"  API Requests Made: {self.api_client.get_request_count()}")
            self.logger.info(f"  Players Fetched: {len(all_players)}")
            self.logger.info(f"  Inserted: {stats['inserted']}")
            self.logger.info(f"  Updated: {stats['updated']}")
            self.logger.info(f"  Skipped (no changes): {stats['skipped']}")
            if stats.get('errors', 0) > 0:
                self.logger.warning(f"  Errors: {stats['errors']}")
            self.logger.info(f"  Duration: {duration:.2f}s")
            self.logger.info("="*70)
            
            return {
                'success': True,
                'sport': self.config.sport,
                'season': self.config.season,
                'api_requests': self.api_client.get_request_count(),
                'players_fetched': len(all_players),
                'inserted': stats['inserted'],
                'updated': stats['updated'],
                'skipped': stats['skipped'],
                'duration': duration
            }
            
        except Exception as e:
            self.logger.error(f"ETL failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
        
        finally:
            self.db_loader.close()
    
    def _get_db_team_id(self, external_team_key: int) -> Optional[int]:
        """Get internal team_id from external_team_key"""
        self.db_loader.cursor.execute("""
            SELECT team_id FROM team
            WHERE external_team_key = %s AND sport_id = %s
        """, (str(external_team_key), self.db_loader.sport_id))
        
        row = self.db_loader.cursor.fetchone()
        return row[0] if row else None
    
    def _get_db_league_id(self) -> Optional[int]:
        """Get league_id from database for this sport"""
        self.db_loader.cursor.execute("""
            SELECT league_id FROM league
            WHERE league_code = %s
        """, (self.config.sport.lower(),))
        
        row = self.db_loader.cursor.fetchone()
        return row[0] if row else None


# ==================== CLI ====================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Multi-Sport Player ETL - Fetch player data from API-SPORTS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Fetch all NFL players for 2024 season
  python player_etl.py --sport NFL --season 2024 --all
  
  # Fetch all NBA players for 2024 season
  python player_etl.py --sport NBA --season 2024 --all
  
  # Fetch players for specific team
  python player_etl.py --sport NFL --season 2024 --team-id 1
  
  # Fetch specific player
  python player_etl.py --sport NFL --season 2024 --player-id 1
  
  # Update existing players (will detect and update only changed data)
  python player_etl.py --sport NFL --season 2024 --all --update

Supported Sports:
  NFL, NCAAF, NBA, NCAAB, MLS, EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, CHAMPIONS
  
  Note: NHL and MLB do not have player endpoints available (placeholders for future)

Environment Variables Required:
  API_SPORTS_KEY - Your API key from api-sports.io
  PGHOST, PGDATABASE, PGUSER, PGPASSWORD - Database credentials
        """
    )
    
    parser.add_argument('--sport', type=str, required=True,
                        choices=list(SPORT_CONFIG.keys()),
                        help='Sport to fetch (NFL, NBA, MLS, etc.)')
    parser.add_argument('--season', type=str, required=True,
                        help='Season year (e.g., 2024)')
    parser.add_argument('--all', action='store_true',
                        help='Fetch all players for the sport')
    parser.add_argument('--team-id', type=int,
                        help='Fetch players for specific team (external team ID)')
    parser.add_argument('--player-id', type=int,
                        help='Fetch specific player by ID')
    parser.add_argument('--league-id', type=int,
                        help='API league ID (optional, uses default for sport)')
    parser.add_argument('--update', action='store_true',
                        help='Update mode - will update existing players with new data')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.team_id and not args.player_id:
        parser.error("Must specify either --all, --team-id, or --player-id")
    
    # Check environment variables
    required_vars = ['API_SPORTS_KEY', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Run ETL
    try:
        config = ETLConfig(args)
        etl = PlayerETL(config)
        result = etl.run()
        
        sys.exit(0 if result.get('success') else 1)
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
