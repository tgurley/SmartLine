#!/usr/bin/env python3
"""
NFL Team ETL
============
Fetches team data from sports-api and loads into database.

Usage:
    python nfl_team_etl.py --all           # Fetch all NFL teams
    python nfl_team_etl.py --team-id 1     # Fetch specific team
    python nfl_team_etl.py --update        # Update existing teams
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import requests


# ==================== Configuration ====================

class ETLConfig:
    """Configuration for Team ETL"""
    
    def __init__(self, args):
        self.api_key = os.environ.get('API_SPORTS_KEY')
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY environment variable not set")
        
        self.api_base_url = "https://v1.american-football.api-sports.io"
        self.league_id = 1  # NFL
        self.season = args.season
        self.team_id = args.team_id
        self.fetch_all = args.all
        self.update_only = args.update
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


# ==================== API Client ====================

class SportsAPIClient:
    """Client for sports-api.io"""
    
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
            time.sleep(1.0)
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return None
    
    def get_team_by_id(self, team_id: int, season: int) -> Optional[Dict]:
        """Get specific team by ID"""
        result = self._make_request('/teams', {'id': team_id, 'season': season})
        
        if result and result.get('response') and len(result['response']) > 0:
            return result['response'][0]
        
        return None
    
    def get_all_nfl_teams(self, season: int) -> List[Dict]:
        """Get all NFL teams for a season (excluding Pro Bowl teams)"""
        self.logger.info(f"Fetching all NFL teams for season {season}")
        
        result = self._make_request('/teams', {'league': 1, 'season': season})
        
        if result and result.get('response'):
            all_teams = result['response']
            self.logger.info(f"API returned {len(all_teams)} total teams")
            
            # Filter out Pro Bowl teams
            filtered_teams = []
            excluded_teams = []
            
            for team in all_teams:
                if self._is_probowl_team(team):
                    excluded_teams.append(team)
                    self.logger.debug(f"Excluding Pro Bowl team: {team.get('name')} ({team.get('code')})")
                else:
                    filtered_teams.append(team)
            
            if excluded_teams:
                self.logger.info(f"Filtered out {len(excluded_teams)} Pro Bowl teams:")
                for team in excluded_teams:
                    self.logger.info(f"  - Excluded: {team.get('name')} ({team.get('code')})")
            
            self.logger.info(f"Keeping {len(filtered_teams)} regular NFL teams")
            return filtered_teams
        
        return []
    
    def _is_probowl_team(self, team: Dict) -> bool:
        """Check if a team is a Pro Bowl team"""
        name = team.get('abbrev', '').lower() if team.get('abbrev') else ''
        code = team.get('code', '').lower() if team.get('code') else ''
        
        # # Pro Bowl team identifiers
        # probowl_keywords = ['pro bowl', 'probowl', 'pro-bowl']
        
        # # Check if team name contains Pro Bowl
        # for keyword in probowl_keywords:
        #     if keyword in name:
        #         return True
        
        # Check for standalone AFC/NFC (these are Pro Bowl teams, not conferences)
        # Regular teams have city names (e.g., "Kansas City Chiefs")
        # Pro Bowl teams are just "AFC" or "NFC"
        if name == 'afc' or name == 'nfc':
            return True
        
        if code == 'afc' or code == 'nfc':
            return True
        
        # Additional check: If abbrev/code is NULL and name is AFC or NFC
        if team.get('code') is None and name in ['afc', 'nfc']:
            return True
        
        return False
    
    def get_request_count(self) -> int:
        """Get total number of API requests made"""
        return self.request_count


# ==================== Data Transformer ====================

class TeamDataTransformer:
    """Transform API team data to database format"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def transform_team(self, api_team: Dict) -> Optional[Dict]:
        """
        Transform API team data to database format
        
        API Format:
        {
            "id": 1,
            "name": "Las Vegas Raiders",
            "code": "LV",
            "city": "Las Vegas",
            "coach": "Antonio Pierce",
            "owner": "Carol and Mark Davis",
            "stadium": "Allegiant Stadium",
            "established": 1960,
            "logo": "https://...",
            "country": {
                "name": "USA",
                "code": "US",
                "flag": "https://..."
            }
        }
        
        DB Format:
        {
            "external_team_key": 1,
            "name": "Las Vegas Raiders",
            "abbrev": "LV",
            "city": "Las Vegas",
            "coach": "Antonio Pierce",
            "owner": "Carol and Mark Davis",
            "stadium": "Allegiant Stadium",
            "established": 1960,
            "logo_url": "https://...",
            "country_name": "USA",
            "country_code": "US",
            "country_flag_url": "https://..."
        }
        
        Returns None if team is invalid (e.g., missing required fields)
        """
        # Validate required fields
        if not api_team.get('name'):
            self.logger.warning(f"Skipping team with no name: {api_team}")
            return None
        
        if not api_team.get('code'):
            self.logger.warning(f"Skipping team with no code/abbrev: {api_team.get('name')}")
            return None
        
        country = api_team.get('country', {})
        
        return {
            'external_team_key': api_team.get('id'),
            'name': api_team.get('name'),
            'abbrev': api_team.get('code'),
            'city': api_team.get('city'),
            'coach': api_team.get('coach'),
            'owner': api_team.get('owner'),
            'stadium': api_team.get('stadium'),
            'established': api_team.get('established'),
            'logo_url': api_team.get('logo'),
            'country_name': country.get('name') if country else None,
            'country_code': country.get('code') if country else None,
            'country_flag_url': country.get('flag') if country else None
        }


# ==================== Database Loader ====================

class TeamDatabaseLoader:
    """Load team data into PostgreSQL database"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database"""
        self.conn = get_conn()
        self.cursor = self.conn.cursor()
        self.logger.info("Connected to database")
    
    def ensure_team_table_exists(self):
        """Ensure team table has all required columns"""
        self.logger.info("Checking team table structure...")
        
        # Add new columns if they don't exist
        alter_statements = [
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS coach TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS owner TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS stadium TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS established INTEGER",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS logo_url TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS country_name TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS country_code TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS country_flag_url TEXT",
            "ALTER TABLE team ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
        ]
        
        for statement in alter_statements:
            try:
                self.cursor.execute(statement)
                self.conn.commit()
            except Exception as e:
                self.logger.warning(f"Column might already exist: {str(e)}")
                self.conn.rollback()
        
        self.logger.info("Team table structure verified")
    
    def get_league_id(self) -> int:
        """Get or create NFL league"""
        self.cursor.execute("SELECT league_id FROM league WHERE name = 'NFL'")
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create NFL league
        self.cursor.execute("INSERT INTO league (name) VALUES ('NFL') RETURNING league_id")
        league_id = self.cursor.fetchone()[0]
        self.conn.commit()
        self.logger.info(f"Created NFL league with ID: {league_id}")
        return league_id
    
    def upsert_teams(self, teams: List[Dict]) -> Dict[str, int]:
        """
        Insert or update teams in database
        
        Returns statistics about the operation
        """
        if not teams:
            return {'inserted': 0, 'updated': 0}
        
        league_id = self.get_league_id()
        
        inserted = 0
        updated = 0
        
        for team in teams:
            # Check if team exists
            self.cursor.execute(
                "SELECT team_id FROM team WHERE external_team_key = %s",
                (team['external_team_key'],)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing team
                update_query = """
                    UPDATE team SET
                        name = %s,
                        abbrev = %s,
                        city = %s,
                        coach = %s,
                        owner = %s,
                        stadium = %s,
                        established = %s,
                        logo_url = %s,
                        country_name = %s,
                        country_code = %s,
                        country_flag_url = %s,
                        updated_at = NOW()
                    WHERE external_team_key = %s
                """
                
                self.cursor.execute(update_query, (
                    team['name'],
                    team['abbrev'],
                    team['city'],
                    team['coach'],
                    team['owner'],
                    team['stadium'],
                    team['established'],
                    team['logo_url'],
                    team['country_name'],
                    team['country_code'],
                    team['country_flag_url'],
                    team['external_team_key']
                ))
                updated += 1
                self.logger.debug(f"Updated: {team['name']}")
            else:
                # Insert new team
                insert_query = """
                    INSERT INTO team (
                        league_id, external_team_key, name, abbrev, city,
                        coach, owner, stadium, established, logo_url,
                        country_name, country_code, country_flag_url, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                """
                
                self.cursor.execute(insert_query, (
                    league_id,
                    team['external_team_key'],
                    team['name'],
                    team['abbrev'],
                    team['city'],
                    team['coach'],
                    team['owner'],
                    team['stadium'],
                    team['established'],
                    team['logo_url'],
                    team['country_name'],
                    team['country_code'],
                    team['country_flag_url']
                ))
                inserted += 1
                self.logger.debug(f"Inserted: {team['name']}")
        
        self.conn.commit()
        
        return {
            'inserted': inserted,
            'updated': updated
        }
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("Database connection closed")


# ==================== Main ETL ====================

class TeamETL:
    """Main ETL orchestrator"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.api_client = SportsAPIClient(
            config.api_key,
            config.api_base_url,
            self.logger
        )
        self.transformer = TeamDataTransformer(self.logger)
        self.db_loader = TeamDatabaseLoader(self.logger)
    
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
        self.logger.info("NFL TEAM ETL - Starting")
        self.logger.info("="*70)
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            # Ensure table structure
            self.db_loader.ensure_team_table_exists()
            
            # Extract: Fetch teams from API
            if self.config.team_id:
                self.logger.info(f"Fetching team ID: {self.config.team_id} for season {self.config.season}")
                api_team = self.api_client.get_team_by_id(self.config.team_id, self.config.season)
                api_teams = [api_team] if api_team else []
            else:
                self.logger.info(f"Fetching all NFL teams for season {self.config.season}")
                api_teams = self.api_client.get_all_nfl_teams(self.config.season)
            
            if not api_teams:
                self.logger.warning("No teams found!")
                return {'success': False, 'error': 'No teams found'}
            
            self.logger.info(f"Fetched {len(api_teams)} teams from API")
            
            # Transform: Convert API format to DB format
            transformed_teams = []
            skipped_count = 0
            for api_team in api_teams:
                transformed = self.transformer.transform_team(api_team)
                if transformed is not None:
                    transformed_teams.append(transformed)
                else:
                    skipped_count += 1
            
            if skipped_count > 0:
                self.logger.info(f"Skipped {skipped_count} invalid teams")
            
            self.logger.info(f"Transformed {len(transformed_teams)} teams")
            
            if not transformed_teams:
                self.logger.warning("No valid teams after transformation!")
                return {'success': False, 'error': 'No valid teams to load'}
            
            # Load: Insert/update in database
            stats = self.db_loader.upsert_teams(transformed_teams)
            
            # Summary
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info("="*70)
            self.logger.info("ETL Summary:")
            self.logger.info(f"  API Requests Made: {self.api_client.get_request_count()}")
            self.logger.info(f"  Teams Processed: {len(api_teams)}")
            self.logger.info(f"  Inserted: {stats['inserted']}")
            self.logger.info(f"  Updated: {stats['updated']}")
            self.logger.info(f"  Duration: {duration:.2f}s")
            self.logger.info("="*70)
            
            return {
                'success': True,
                'api_requests': self.api_client.get_request_count(),
                'teams_processed': len(api_teams),
                'inserted': stats['inserted'],
                'updated': stats['updated'],
                'duration': duration
            }
            
        except Exception as e:
            self.logger.error(f"ETL failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
        
        finally:
            self.db_loader.close()


# ==================== CLI ====================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NFL Team ETL - Fetch team data from sports-api',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all NFL teams for 2023 season
  python nfl_team_etl.py --season 2023 --all
  
  # Fetch specific team
  python nfl_team_etl.py --season 2023 --team-id 1
  
  # Update existing teams
  python nfl_team_etl.py --season 2024 --all --update

Environment Variables Required:
  SPORTS_API_KEY - Your API key from api-sports.io
  PGHOST, PGDATABASE, PGUSER, PGPASSWORD - Database credentials
        """
    )
    
    parser.add_argument('--season', type=int, required=True,
                        help='Season year (e.g., 2023, 2024)')
    parser.add_argument('--all', action='store_true',
                        help='Fetch all NFL teams')
    parser.add_argument('--team-id', type=int,
                        help='Fetch specific team by ID')
    parser.add_argument('--update', action='store_true',
                        help='Update existing teams (with --all)')
    
    args = parser.parse_args()
    
    # Validate arguments
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
        etl = TeamETL(config)
        result = etl.run()
        
        sys.exit(0 if result.get('success') else 1)
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
    
#NFC