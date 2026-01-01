#!/usr/bin/env python3
"""
Multi-Sport Team ETL
====================
Fetches team data from API-SPORTS and loads into database.
Supports: NFL, NCAAF, NBA, NCAAB, MLB, NHL, MLS, Soccer leagues

Usage:
    python team_etl.py --sport NFL --season 2024 --all
    python team_etl.py --sport NBA --season 2024 --all
    python team_etl.py --sport MLB --season 2024 --league-id 1
    python team_etl.py --sport NHL --season 2024 --all
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
from dotenv import load_dotenv  # Add this import

load_dotenv()


# ==================== Sport Configuration ====================

SPORT_CONFIG = {
    'NFL': {
        'sport_code': 'NFL',
        'api_url': 'https://v1.american-football.api-sports.io',
        'default_league_id': 1,
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'nfl_team_data'
    },
    'NCAAF': {
        'sport_code': 'NCAAF',
        'api_url': 'https://v1.american-football.api-sports.io',
        'default_league_id': 2,
        'league_param': 'league',
        'has_extensions': False,
        'extension_table': None
    },
    'NBA': {
        'sport_code': 'NBA',
        'api_url': 'https://v2.nba.api-sports.io',
        'default_league_id': 'standard',  # NBA uses "standard" league
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'nba_team_data'
    },
    'NCAAB': {
        'sport_code': 'NCAAB',
        'api_url': 'https://v1.basketball.api-sports.io',
        'default_league_id': 116,  # NCAA Men's Basketball
        'league_param': 'league',
        'season_param': 'season',  # Basketball API requires season
        'has_extensions': False,
        'extension_table': None
    },
    'MLB': {
        'sport_code': 'MLB',
        'api_url': 'https://v1.baseball.api-sports.io',
        'default_league_id': 1,
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'mlb_team_data'
    },
    'NHL': {
        'sport_code': 'NHL',
        'api_url': 'https://v1.hockey.api-sports.io',
        'default_league_id': 57,  # NHL league ID
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'nhl_team_data'
    },
    'MLS': {
        'sport_code': 'MLS',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 253,  # MLS league ID
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'EPL': {
        'sport_code': 'EPL',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 39,  # Premier League
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'LA_LIGA': {
        'sport_code': 'LA_LIGA',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 140,  # La Liga
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'BUNDESLIGA': {
        'sport_code': 'BUNDESLIGA',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 78,  # Bundesliga (Germany)
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'SERIE_A': {
        'sport_code': 'SERIE_A',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 135,  # Serie A (Italy)
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'LIGUE_1': {
        'sport_code': 'LIGUE_1',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 61,  # Ligue 1 (France)
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    },
    'CHAMPIONS': {
        'sport_code': 'CHAMPIONS',
        'api_url': 'https://v3.football.api-sports.io',
        'default_league_id': 2,  # UEFA Champions League
        'league_param': 'league',
        'has_extensions': True,
        'extension_table': 'soccer_team_data'
    }
}


# ==================== Configuration ====================

class ETLConfig:
    """Configuration for Team ETL"""
    
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
        self.fetch_all = args.all
        self.update_only = args.update
        self.delay_between_requests = 1.0


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


def get_league_id(cursor, sport_code: str) -> Optional[int]:
    """Get league_id from database for this sport"""
    cursor.execute(
        "SELECT league_id FROM league WHERE league_code = %s",
        (sport_code.lower(),)
    )
    result = cursor.fetchone()
    return result[0] if result else None


# ==================== API Client ====================

class SportsAPIClient:
    """Unified client for all API-SPORTS endpoints"""
    
    def __init__(self, api_key: str, base_url: str, sport: str, logger: logging.Logger):
        self.api_key = api_key
        self.base_url = base_url
        self.sport = sport
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
    
    def get_teams(self, league_id: Optional[int], season: int, team_id: Optional[int] = None) -> List[Dict]:
        """Get teams (works for all sports)"""
        params = {}
        
        if team_id:
            params['id'] = team_id
        
        if league_id and SPORT_CONFIG[self.sport]['league_param']:
            params[SPORT_CONFIG[self.sport]['league_param']] = league_id
        
        # Only add season for sports that support it (not NBA, which doesn't need it)
        # Basketball API (NCAAB) requires season, but NBA API doesn't
        if season and self.sport != 'NBA':
            params['season'] = season
        
        self.logger.info(f"Fetching {self.sport} teams with params: {params}")
        
        result = self._make_request('/teams', params)
        
        if result and result.get('response'):
            teams = result['response']
            self.logger.info(f"API returned {len(teams)} teams")
            
            # Filter out special teams (Pro Bowl for NFL, All-Star for NBA, etc.)
            filtered = self._filter_special_teams(teams)
            self.logger.info(f"Keeping {len(filtered)} regular teams after filtering")
            
            return filtered
        
        return []
    
    def _filter_special_teams(self, teams: List[Dict]) -> List[Dict]:
        """Filter out All-Star, Pro Bowl, and other special teams"""
        filtered = []
        
        for team in teams:
            if self.sport in ['NFL', 'NCAAF']:
                # Filter Pro Bowl teams (AFC, NFC standalone)
                code = team.get('code', '').upper() if team.get('code') else ''
                name = team.get('name', '').lower()
                
                if code in ['AFC', 'NFC'] or 'pro bowl' in name:
                    self.logger.debug(f"Filtered: {team.get('name')} (Pro Bowl team)")
                    continue
                
                # NCAAF-specific: Filter out NAIA and Junior College teams
                if self.sport == 'NCAAF':
                    # Filter by keywords that indicate NAIA or junior colleges
                    filter_keywords = [
                        'community college', 'junior college', 'jc',
                        'naia', 'junior', 'juco', 'cc'
                    ]
                    
                    # Check if team name contains any filter keywords
                    if any(keyword in name for keyword in filter_keywords):
                        self.logger.debug(f"Filtered: {team.get('name')} (NAIA/Junior College)")
                        continue
                    
                    # Also check if team is explicitly marked with a division/type field
                    # (API might have a 'type' or 'division' field)
                    team_type = team.get('type', '').lower()
                    if 'naia' in team_type or 'junior' in team_type or 'juco' in team_type:
                        self.logger.debug(f"Filtered: {team.get('name')} (NAIA/Junior College by type)")
                        continue
            
            elif self.sport == 'NBA':
                # Filter All-Star teams
                if team.get('allStar'):
                    self.logger.debug(f"Filtered: {team.get('name')} (All-Star team)")
                    continue
                
                # Filter non-NBA teams (only keep teams with valid NBA conference)
                # NBA teams MUST have a conference (East or West)
                standard_league = team.get('leagues', {}).get('standard', {})
                conference = standard_league.get('conference')
                
                if not conference or conference not in ['East', 'West']:
                    self.logger.debug(f"Filtered: {team.get('name')} (Non-NBA team - no valid conference)")
                    continue
                
                # Also filter out non-NBA franchises
                if not team.get('nbaFranchise', False):
                    self.logger.debug(f"Filtered: {team.get('name')} (Not an NBA franchise)")
                    continue
            
            elif self.sport == 'NCAAB':
                # NCAAB teams don't need special filtering
                # All teams from NCAA league 116 are valid college teams
                pass
            
            elif self.sport == 'MLB':
                # Filter out league entries (not actual teams)
                name = team.get('name', '')
                if 'league' in name.lower():
                    self.logger.debug(f"Filtered: {team.get('name')} (League, not a team)")
                    continue
            
            elif self.sport == 'NHL':
                # Filter All-Star teams (if applicable)
                name = team.get('name', '').lower()
                if 'all-star' in name or 'all star' in name:
                    self.logger.debug(f"Filtered: {team.get('name')} (All-Star team)")
                    continue
            
            filtered.append(team)
        
        return filtered
    
    def get_request_count(self) -> int:
        """Get total number of API requests made"""
        return self.request_count


# ==================== Data Transformer ====================

class TeamDataTransformer:
    """Transform API team data to database format (sport-agnostic)"""
    
    def __init__(self, sport: str, logger: logging.Logger):
        self.sport = sport
        self.logger = logger
    
    def transform_team(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """
        Transform API team data to database format
        
        Returns: (core_team_data, extension_data, venue_data) or None
        """
        if self.sport in ['NFL', 'NCAAF']:
            return self._transform_football(api_team)
        elif self.sport in ['NBA', 'NCAAB']:
            return self._transform_basketball(api_team)
        elif self.sport == 'MLB':
            return self._transform_baseball(api_team)
        elif self.sport == 'NHL':
            return self._transform_hockey(api_team)
        elif self.sport in ['MLS', 'EPL', 'LA_LIGA', 'BUNDESLIGA', 'SERIE_A', 'LIGUE_1', 'CHAMPIONS']:
            return self._transform_soccer(api_team)
        
        return None
    
    def _transform_football(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Transform NFL/NCAAF team data"""
        if not api_team.get('name'):
            return None
        
        # Generate abbreviation if not provided
        # NCAAF teams often don't have 'code' field
        name = api_team.get('name')
        
        if api_team.get('code'):
            # NFL teams have codes, use them
            abbrev = api_team.get('code')
        else:
            # Generate 4-char abbreviation for NCAAF
            # Strategy: First 2 chars of first word + first 2 chars of last word
            # Conflicts will be resolved by adding numeric suffix (BCER, BCR1, BCR2, etc.)
            name_parts = name.split()
            
            if len(name_parts) >= 2:
                # First 2 chars of first word + first 2 chars of last word
                first_part = name_parts[0][:2]
                last_part = name_parts[-1][:2]
                abbrev = (first_part + last_part).upper()
            else:
                # Fallback for single-word names (rare)
                abbrev = name[:4].upper()
        
        self.logger.debug(f"Football team: '{name}' -> base abbrev: '{abbrev}'")
        
        # Core team data
        core = {
            'external_team_key': api_team.get('id'),
            'name': api_team.get('name'),
            'abbrev': abbrev,
            'city': api_team.get('city'),
            'established': api_team.get('established'),
            'logo_url': api_team.get('logo'),
            'country_name': api_team.get('country', {}).get('name'),
            'country_code': api_team.get('country', {}).get('code'),
            'country_flag_url': api_team.get('country', {}).get('flag'),
            'stadium': api_team.get('stadium')  # Will migrate to venue later
        }
        
        # NFL-specific extensions
        extensions = {
            'head_coach': api_team.get('coach'),
            'team_owner': api_team.get('owner')
        }
        
        # Venue data
        venue = {
            'name': api_team.get('stadium'),
            'city': api_team.get('city'),
            'country_name': api_team.get('country', {}).get('name'),
            'country_code': api_team.get('country', {}).get('code')
        } if api_team.get('stadium') else None
        
        return (core, extensions, venue)
    
    def _transform_basketball(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Transform NBA/NCAAB team data"""
        if not api_team.get('name'):
            return None
        
        # Generate abbreviation if not provided
        # NCAAB teams might not have 'code' field
        name = api_team.get('name')
        
        if api_team.get('code'):
            # NBA teams have codes, use them
            abbrev = api_team.get('code')
        else:
            # Generate 4-char abbreviation for NCAAB
            # Strategy: First 2 chars of first word + first 2 chars of last word
            # Conflicts will be resolved by adding numeric suffix
            name_parts = name.split()
            
            if len(name_parts) >= 2:
                # First 2 chars of first word + first 2 chars of last word
                first_part = name_parts[0][:2]
                last_part = name_parts[-1][:2]
                abbrev = (first_part + last_part).upper()
            else:
                # Fallback for single-word names
                abbrev = name[:4].upper()
        
        self.logger.debug(f"Basketball team: '{name}' -> base abbrev: '{abbrev}'")
        
        # Core team data
        core = {
            'external_team_key': api_team.get('id'),
            'name': api_team.get('name'),
            'abbrev': abbrev,
            'city': api_team.get('city'),
            'logo_url': api_team.get('logo'),
            'country_name': 'USA',  # NBA teams are US-based (mostly)
            'country_code': 'US'
        }
        
        # NBA-specific extensions
        standard_league = api_team.get('leagues', {}).get('standard', {})
        extensions = {
            'nickname': api_team.get('nickname'),
            'conference': standard_league.get('conference'),
            'division': standard_league.get('division'),
            'all_star': api_team.get('allStar', False),
            'nba_franchise': api_team.get('nbaFranchise', True)
        }
        
        return (core, extensions, None)
    
    def _transform_baseball(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Transform MLB team data"""
        if not api_team.get('name'):
            return None
        
        # Generate 4-character abbreviation from team name
        # Strategy: City initial + first 3 chars of team name
        # Examples:
        #   "Boston Red Sox" -> "B" + "Sox" -> "BSOX"
        #   "Chicago White Sox" -> "C" + "Sox" -> "CSOX"
        #   "Texas Rangers" -> "T" + "Ran" -> "TRAN"
        #   "Tampa Bay Rays" -> "T" + "Ray" -> "TRAY"
        name = api_team.get('name')
        name_parts = name.split()
        
        if len(name_parts) >= 2:
            # City initial + first 3 chars of last word (4 chars total)
            city_initial = name_parts[0][0]  # First char of first word
            team_name = name_parts[-1]  # Last word
            abbrev = (city_initial + team_name[:3]).upper()
        else:
            # Fallback for single-word names
            abbrev = name[:4].upper()
        
        self.logger.debug(f"MLB team: '{name}' -> abbrev: '{abbrev}'")
        
        # Core team data
        core = {
            'external_team_key': api_team.get('id'),
            'name': api_team.get('name'),
            'abbrev': abbrev,
            'logo_url': api_team.get('logo'),
            'country_name': api_team.get('country', {}).get('name'),
            'country_code': api_team.get('country', {}).get('code'),
            'country_flag_url': api_team.get('country', {}).get('flag')
        }
        
        # MLB extensions (league/division would come from separate API call)
        extensions = {}
        
        return (core, extensions, None)
    
    def _transform_hockey(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Transform NHL team data"""
        if not api_team.get('name'):
            return None
        
        # Generate 4-character abbreviation from team name
        # Strategy: City initial + first 3 chars of team name
        # Examples:
        #   "Colorado Avalanche" -> "C" + "Ava" -> "CAVA"
        #   "Columbus Blue Jackets" -> "C" + "Blu" -> "CBLU"
        #   "Tampa Bay Lightning" -> "T" + "Lig" -> "TLIG"
        name = api_team.get('name')
        name_parts = name.split()
        
        if len(name_parts) >= 2:
            # City initial + first 3 chars of last word (4 chars total)
            city_initial = name_parts[0][0]  # First char of first word
            team_name = name_parts[-1]  # Last word
            abbrev = (city_initial + team_name[:3]).upper()
        else:
            # Fallback for single-word names
            abbrev = name[:4].upper()
        
        self.logger.debug(f"NHL team: '{name}' -> abbrev: '{abbrev}'")
        
        # Core team data
        core = {
            'external_team_key': api_team.get('id'),
            'name': api_team.get('name'),
            'abbrev': abbrev,
            'established': api_team.get('founded'),
            'logo_url': api_team.get('logo'),
            'country_name': api_team.get('country', {}).get('name'),
            'country_code': api_team.get('country', {}).get('code'),
            'country_flag_url': api_team.get('country', {}).get('flag')
        }
        
        # NHL-specific extensions
        extensions = {
            'colors': api_team.get('colors')
        }
        
        # Venue data
        arena = api_team.get('arena', {})
        venue = {
            'name': arena.get('name'),
            'capacity': arena.get('capacity'),
            'city': arena.get('location')  # Format: "City, Country"
        } if arena.get('name') else None
        
        return (core, extensions, venue)
    
    def _transform_soccer(self, api_team: Dict) -> Optional[Tuple[Dict, Dict, Dict]]:
        """Transform Soccer team data"""
        # Soccer API nests team data
        team_data = api_team.get('team', api_team)  # Handle both formats
        venue_data = api_team.get('venue')
        
        if not team_data.get('name'):
            return None
        
        # Generate 4-character abbreviation
        # Strategy: First 2 chars of city + first 2 chars of team name
        # Examples:
        #   "Colorado Rapids" -> "CO" + "RA" -> "CORA"
        #   "Columbus Crew" -> "CO" + "CR" -> "COCR"
        #   "St. Louis City" -> "ST" + "CI" -> "STCI"
        #   "LA Galaxy" -> "LA" + "GA" -> "LAGA"
        name = team_data.get('name')
        name_parts = name.split()
        
        if len(name_parts) >= 2:
            # First 2 chars of first word + first 2 chars of last word
            city_part = name_parts[0][:2]
            team_part = name_parts[-1][:2]
            abbrev = (city_part + team_part).upper()
        else:
            # Fallback for single-word names
            abbrev = name[:4].upper()
        
        self.logger.debug(f"Soccer team: '{name}' -> abbrev: '{abbrev}'")
        
        # Core team data
        core = {
            'external_team_key': team_data.get('id'),
            'name': team_data.get('name'),
            'abbrev': abbrev,
            'established': team_data.get('founded'),
            'logo_url': team_data.get('logo'),
            'country_name': team_data.get('country'),
            'country_code': team_data.get('country')[:2].upper() if team_data.get('country') else None
        }
        
        # Soccer-specific extensions
        extensions = {
            'is_national': team_data.get('national', False)
        }
        
        # Venue data
        venue = {
            'name': venue_data.get('name'),
            'address': venue_data.get('address'),
            'city': venue_data.get('city'),
            'capacity': venue_data.get('capacity'),
            'surface_type': venue_data.get('surface'),
            'image_url': venue_data.get('image'),
            'external_venue_id': venue_data.get('id')
        } if venue_data else None
        
        return (core, extensions, venue)


# ==================== Database Loader ====================

class TeamDatabaseLoader:
    """Load team data into database"""
    
    def __init__(self, sport: str, sport_config: Dict, logger: logging.Logger):
        self.sport = sport
        self.sport_config = sport_config
        self.logger = logger
        self.conn = None
        self.cursor = None
        self.abbrev_tracker = {}  # Track used abbreviations in this session
    
    def connect(self):
        """Connect to database and get sport/league IDs"""
        self.conn = get_conn()
        self.cursor = self.conn.cursor()
        
        # Get sport_id
        self.sport_id = get_sport_id(self.cursor, self.sport_config['sport_code'])
        self.logger.info(f"Sport ID for {self.sport}: {self.sport_id}")
        
        # Get league_id
        self.league_id = get_league_id(self.cursor, self.sport_config['sport_code'])
        if not self.league_id:
            self.logger.warning(f"No league found for {self.sport} - you may need to create it manually")
        else:
            self.logger.info(f"League ID for {self.sport}: {self.league_id}")
        
        # Load existing abbreviations for this league to avoid conflicts
        self.cursor.execute(
            "SELECT abbrev FROM team WHERE league_id = %s",
            (self.league_id,)
        )
        for row in self.cursor.fetchall():
            self.abbrev_tracker[row[0]] = True
    
    def _get_unique_abbrev(self, base_abbrev: str, team_name: str) -> str:
        """
        Get a unique abbreviation by adding numeric suffix if needed
        
        Examples:
        - BCER -> BCER (if available)
        - BCER -> BCR1 (if BCER taken)
        - BCER -> BCR2 (if BCER and BCR1 taken)
        """
        # Try base abbreviation first
        if base_abbrev not in self.abbrev_tracker:
            self.abbrev_tracker[base_abbrev] = True
            return base_abbrev
        
        # Base is taken, try with numeric suffixes
        # Shorten to 3 chars to make room for number
        base_short = base_abbrev[:3]
        
        for i in range(1, 100):  # Try up to 99
            candidate = f"{base_short}{i}"
            if candidate not in self.abbrev_tracker:
                self.abbrev_tracker[candidate] = True
                self.logger.debug(f"Abbreviation conflict resolved: '{team_name}' -> '{base_abbrev}' changed to '{candidate}'")
                return candidate
        
        # If we somehow exhausted all options (unlikely), use hash
        import hashlib
        hash_suffix = hashlib.md5(team_name.encode()).hexdigest()[:2].upper()
        fallback = f"{base_abbrev[:2]}{hash_suffix}"
        self.abbrev_tracker[fallback] = True
        self.logger.warning(f"Used hash fallback for '{team_name}': {fallback}")
        return fallback
    
    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        try:
            # Test connection
            self.cursor.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self.logger.warning("Database connection lost, reconnecting...")
            try:
                if self.cursor:
                    self.cursor.close()
                if self.conn:
                    self.conn.close()
            except:
                pass
            
            # Reconnect
            self.connect()
            self.logger.info("Reconnected to database")
    
    def upsert_teams(self, teams_data: List[Tuple[Dict, Dict, Dict]]) -> Dict:
        """Insert or update teams"""
        inserted = 0
        updated = 0
        errors = 0
        
        for i, (core, extensions, venue) in enumerate(teams_data, 1):
            try:
                # Check connection health every 10 teams
                if i % 10 == 0:
                    self._ensure_connection()
                
                # Resolve abbreviation conflicts BEFORE inserting
                core['abbrev'] = self._get_unique_abbrev(core['abbrev'], core['name'])
                
                # Handle venue first if present
                venue_id = None
                if venue and venue.get('name'):
                    # Use team city as fallback if venue doesn't have city
                    if not venue.get('city'):
                        venue['city'] = core.get('city', 'Unknown')
                        self.logger.debug(f"Using team city for venue: {venue['name']}")
                    
                    venue_id = self._upsert_venue(venue)
                
                # Check if team exists
                self.cursor.execute(
                    "SELECT team_id FROM team WHERE external_team_key = %s AND league_id = %s",
                    (core['external_team_key'], self.league_id)
                )
                existing = self.cursor.fetchone()
                
                if existing:
                    # Update
                    team_id = existing[0]
                    self._update_team(team_id, core, venue_id)
                    
                    # Update extensions if applicable
                    if self.sport_config['has_extensions'] and extensions:
                        self._upsert_extensions(team_id, extensions)
                    
                    updated += 1
                    self.logger.debug(f"Updated: {core['name']}")
                else:
                    # Insert
                    team_id = self._insert_team(core, venue_id)
                    
                    # Insert extensions if applicable
                    if self.sport_config['has_extensions'] and extensions:
                        self._upsert_extensions(team_id, extensions)
                    
                    inserted += 1
                    self.logger.debug(f"Inserted: {core['name']}")
                    
            except Exception as e:
                errors += 1
                self.logger.error(f"Error processing team '{core.get('name')}': {str(e)}")
                # Continue with next team
                continue
        
        self.conn.commit()
        
        return {'inserted': inserted, 'updated': updated, 'errors': errors}
    
    def _upsert_venue(self, venue: Dict) -> Optional[int]:
        """Insert or update venue, return venue_id"""
        try:
            # Validate required fields
            if not venue.get('name'):
                self.logger.warning("Skipping venue - missing name")
                return None
            
            # City is guaranteed by caller (uses team city as fallback)
            # But double-check just in case
            if not venue.get('city'):
                venue['city'] = 'Unknown'
            
            # Check if venue exists by name
            self.cursor.execute(
                "SELECT venue_id FROM venue WHERE name = %s",
                (venue['name'],)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Insert new venue
            self.cursor.execute("""
                INSERT INTO venue (
                    name, city, state_province, address, capacity, surface_type, 
                    image_url, external_venue_id, country_name, country_code
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING venue_id
            """, (
                venue.get('name'),
                venue.get('city'),
                venue.get('state_province'),  # Now included
                venue.get('address'),
                venue.get('capacity'),
                venue.get('surface_type'),
                venue.get('image_url'),
                venue.get('external_venue_id'),
                venue.get('country_name'),
                venue.get('country_code')
            ))
            
            venue_id = self.cursor.fetchone()[0]
            self.logger.debug(f"Created venue: {venue.get('name')} (ID: {venue_id})")
            return venue_id
            
        except Exception as e:
            self.logger.error(f"Error upserting venue '{venue.get('name')}': {str(e)}")
            # Return None - team can still be inserted without venue_id
            return None
    
    def _insert_team(self, core: Dict, venue_id: Optional[int]) -> int:
        """Insert new team"""
        self.cursor.execute("""
            INSERT INTO team (
                league_id, sport_id, external_team_key, name, abbrev, city,
                established, logo_url, country_name, country_code, country_flag_url,
                stadium, venue_id, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            RETURNING team_id
        """, (
            self.league_id,
            self.sport_id,
            core['external_team_key'],
            core['name'],
            core['abbrev'],
            core.get('city'),
            core.get('established'),
            core.get('logo_url'),
            core.get('country_name'),
            core.get('country_code'),
            core.get('country_flag_url'),
            core.get('stadium'),
            venue_id
        ))
        
        return self.cursor.fetchone()[0]
    
    def _update_team(self, team_id: int, core: Dict, venue_id: Optional[int]):
        """Update existing team"""
        self.cursor.execute("""
            UPDATE team SET
                name = %s,
                abbrev = %s,
                city = %s,
                established = %s,
                logo_url = %s,
                country_name = %s,
                country_code = %s,
                country_flag_url = %s,
                stadium = %s,
                venue_id = %s,
                updated_at = NOW()
            WHERE team_id = %s
        """, (
            core['name'],
            core['abbrev'],
            core.get('city'),
            core.get('established'),
            core.get('logo_url'),
            core.get('country_name'),
            core.get('country_code'),
            core.get('country_flag_url'),
            core.get('stadium'),
            venue_id,
            team_id
        ))
    
    def _upsert_extensions(self, team_id: int, extensions: Dict):
        """Insert or update sport-specific extensions"""
        table = self.sport_config['extension_table']
        if not table:
            return
        
        if self.sport in ['NFL', 'NCAAF']:
            self._upsert_nfl_data(team_id, extensions)
        elif self.sport in ['NBA', 'NCAAB']:
            self._upsert_nba_data(team_id, extensions)
        elif self.sport == 'MLB':
            self._upsert_mlb_data(team_id, extensions)
        elif self.sport == 'NHL':
            self._upsert_nhl_data(team_id, extensions)
        elif 'soccer' in table.lower():
            self._upsert_soccer_data(team_id, extensions)
    
    def _upsert_nfl_data(self, team_id: int, ext: Dict):
        """Upsert NFL-specific data"""
        self.cursor.execute("""
            INSERT INTO nfl_team_data (team_id, head_coach, team_owner, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                head_coach = EXCLUDED.head_coach,
                team_owner = EXCLUDED.team_owner,
                updated_at = NOW()
        """, (team_id, ext.get('head_coach'), ext.get('team_owner')))
    
    def _upsert_nba_data(self, team_id: int, ext: Dict):
        """Upsert NBA-specific data"""
        # Validate conference - must be East or West for NBA teams
        conference = ext.get('conference')
        if not conference or conference not in ['East', 'West']:
            self.logger.warning(f"Skipping NBA extension for team_id {team_id} - invalid conference: {conference}")
            return
        
        self.cursor.execute("""
            INSERT INTO nba_team_data (
                team_id, nickname, conference, division, 
                all_star, nba_franchise, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                nickname = EXCLUDED.nickname,
                conference = EXCLUDED.conference,
                division = EXCLUDED.division,
                all_star = EXCLUDED.all_star,
                nba_franchise = EXCLUDED.nba_franchise,
                updated_at = NOW()
        """, (
            team_id,
            ext.get('nickname'),
            ext.get('conference'),
            ext.get('division'),
            ext.get('all_star'),
            ext.get('nba_franchise')
        ))
    
    def _upsert_mlb_data(self, team_id: int, ext: Dict):
        """Upsert MLB-specific data"""
        if not ext:
            return
        
        self.cursor.execute("""
            INSERT INTO mlb_team_data (team_id, league, division, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                league = EXCLUDED.league,
                division = EXCLUDED.division,
                updated_at = NOW()
        """, (team_id, ext.get('league'), ext.get('division')))
    
    def _upsert_nhl_data(self, team_id: int, ext: Dict):
        """Upsert NHL-specific data"""
        self.cursor.execute("""
            INSERT INTO nhl_team_data (team_id, colors, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                colors = EXCLUDED.colors,
                updated_at = NOW()
        """, (team_id, ext.get('colors')))
    
    def _upsert_soccer_data(self, team_id: int, ext: Dict):
        """Upsert Soccer-specific data"""
        self.cursor.execute("""
            INSERT INTO soccer_team_data (team_id, is_national, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (team_id) DO UPDATE SET
                is_national = EXCLUDED.is_national,
                updated_at = NOW()
        """, (team_id, ext.get('is_national', False)))
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ==================== Main ETL ====================

class TeamETL:
    """Main ETL orchestrator"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.api_client = SportsAPIClient(
            config.api_key,
            config.api_base_url,
            config.sport,
            self.logger
        )
        self.transformer = TeamDataTransformer(config.sport, self.logger)
        self.db_loader = TeamDatabaseLoader(
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
        self.logger.info(f"{self.config.sport} TEAM ETL - Starting")
        self.logger.info("="*70)
        
        try:
            # Connect to database
            self.db_loader.connect()
            
            # Extract: Fetch teams from API
            if self.config.team_id:
                api_teams = self.api_client.get_teams(
                    self.config.api_league_id,
                    self.config.season,
                    self.config.team_id
                )
            else:
                api_teams = self.api_client.get_teams(
                    self.config.api_league_id,
                    self.config.season
                )
            
            if not api_teams:
                self.logger.warning("No teams found!")
                return {'success': False, 'error': 'No teams found'}
            
            self.logger.info(f"Fetched {len(api_teams)} teams from API")
            
            # Transform: Convert API format to DB format
            transformed_teams = []
            skipped_count = 0
            
            for api_team in api_teams:
                result = self.transformer.transform_team(api_team)
                if result:
                    transformed_teams.append(result)
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
            self.logger.info(f"  Sport: {self.config.sport}")
            self.logger.info(f"  API Requests Made: {self.api_client.get_request_count()}")
            self.logger.info(f"  Teams Processed: {len(api_teams)}")
            self.logger.info(f"  Inserted: {stats['inserted']}")
            self.logger.info(f"  Updated: {stats['updated']}")
            if stats.get('errors', 0) > 0:
                self.logger.warning(f"  Errors: {stats['errors']}")
            self.logger.info(f"  Duration: {duration:.2f}s")
            self.logger.info("="*70)
            
            return {
                'success': True,
                'sport': self.config.sport,
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
        description='Multi-Sport Team ETL - Fetch team data from API-SPORTS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Fetch all NFL teams for 2024
  python team_etl.py --sport NFL --season 2024 --all
  
  # Fetch all NBA teams for 2024
  python team_etl.py --sport NBA --season 2024 --all
  
  # Fetch specific team
  python team_etl.py --sport NFL --season 2024 --team-id 1
  
  # Fetch MLB teams
  python team_etl.py --sport MLB --season 2024 --all --league-id 1

Supported Sports:
  {', '.join(SPORT_CONFIG.keys())}

Environment Variables Required:
  API_SPORTS_KEY - Your API key from api-sports.io
  PGHOST, PGDATABASE, PGUSER, PGPASSWORD - Database credentials
        """
    )
    
    parser.add_argument('--sport', type=str, required=True,
                        choices=list(SPORT_CONFIG.keys()),
                        help='Sport to fetch (NFL, NBA, MLB, NHL, etc.)')
    parser.add_argument('--season', type=str, required=True,
                        help='Season year (e.g., 2024, 2024-2025 for NCAAB)')
    parser.add_argument('--all', action='store_true',
                        help='Fetch all teams for the sport')
    parser.add_argument('--team-id', type=int,
                        help='Fetch specific team by ID')
    parser.add_argument('--league-id', type=int,
                        help='API league ID (optional, uses default for sport)')
    parser.add_argument('--update', action='store_true',
                        help='Update existing teams')
    
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
