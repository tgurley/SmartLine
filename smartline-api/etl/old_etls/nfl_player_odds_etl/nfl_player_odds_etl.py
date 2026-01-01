#!/usr/bin/env python3
"""
SmartLine Player Odds ETL
==========================
Fetches historical player prop betting odds from The Odds API for the 2023 NFL season.

Usage:
    python nfl_player_odds_etl.py --season 2023 [--dry-run] [--games GAME_IDS]
    
Examples:
    # Dry run to see cost estimate
    python nfl_player_odds_etl.py --season 2023 --dry-run
    
    # Process full season
    python nfl_player_odds_etl.py --season 2023
    
    # Process specific games
    python nfl_player_odds_etl.py --season 2023 --games 1119,1120,1121
    
Cost Estimate: ~50 credits per game × 285 games = 14,250 credits for full season

Author: SmartLine ETL Team
Date: 2024-12-23
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import psycopg2
from psycopg2.extras import execute_batch
from rapidfuzz import fuzz, process

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
import player_odds_config as config

# =========================================================
# LOGGING SETUP
# =========================================================

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )

# =========================================================
# ENVIRONMENT VALIDATION
# =========================================================

def validate_environment():
    """Ensure all required environment variables are set."""
    missing_vars = []
    
    for var in config.REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set the following environment variables:")
        for var in missing_vars:
            logger.error(f"  export {var}='your_value'")
        sys.exit(1)
    
    logger.info("All required environment variables present")

# =========================================================
# DATA FETCHING FUNCTIONS
# =========================================================

def fetch_games_for_season(conn, season: int, game_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    Fetch all games for a given season from the database.
    
    Args:
        conn: Database connection
        season: Season year (e.g., 2023)
        game_ids: Optional list of specific game IDs to fetch
    
    Returns:
        List of game dictionaries with game_id, datetime, home_team, away_team
    """
    cursor = conn.cursor()
    
    if game_ids:
        placeholders = ','.join(['%s'] * len(game_ids))
        query = f"""
            SELECT 
                g.game_id,
                g.game_datetime_utc,
                g.home_team_id,
                g.away_team_id,
                ht.name as home_team_name,
                at.name as away_team_name
            FROM game g
            INNER JOIN season s ON g.season_id = s.season_id
            INNER JOIN team ht ON g.home_team_id = ht.team_id
            INNER JOIN team at ON g.away_team_id = at.team_id
            WHERE s.year = %s
              AND g.game_id IN ({placeholders})
            ORDER BY g.game_datetime_utc
        """
        cursor.execute(query, [season] + game_ids)
    else:
        query = """
            SELECT 
                g.game_id,
                g.game_datetime_utc,
                g.home_team_id,
                g.away_team_id,
                ht.name as home_team_name,
                at.name as away_team_name
            FROM game g
            INNER JOIN season s ON g.season_id = s.season_id
            INNER JOIN team ht ON g.home_team_id = ht.team_id
            INNER JOIN team at ON g.away_team_id = at.team_id
            WHERE s.year = %s
            ORDER BY g.game_datetime_utc
        """
        cursor.execute(query, (season,))
    
    games = []
    for row in cursor.fetchall():
        games.append({
            'game_id': row[0],
            'game_datetime_utc': row[1],
            'home_team_id': row[2],
            'away_team_id': row[3],
            'home_team_name': row[4],
            'away_team_name': row[5],
        })
    
    cursor.close()
    logger.info(f"Fetched {len(games)} games for season {season}")
    return games

def check_existing_odds(conn, game_id: int) -> bool:
    """
    Check if odds data already exists for a game.
    
    Args:
        conn: Database connection
        game_id: Game ID to check
    
    Returns:
        True if odds data exists, False otherwise
    """
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM player_odds WHERE game_id = %s"
    cursor.execute(query, (game_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0

def fetch_player_map(conn) -> Dict[str, List[Dict]]:
    """
    Fetch all players from database and create name -> player info mapping.
    Changed to support multiple players with the same name.
    
    Returns:
        Dictionary mapping full_name to list of player dicts
        Each player dict contains: player_id, full_name, team_id, position
    """
    cursor = conn.cursor()
    query = """
        SELECT 
            player_id, 
            full_name, 
            team_id, 
            position
        FROM player
        WHERE position IS NOT NULL
        ORDER BY full_name
    """
    cursor.execute(query)
    
    player_map = {}
    total_players = 0
    
    for player_id, full_name, team_id, position in cursor.fetchall():
        if full_name not in player_map:
            player_map[full_name] = []
        
        player_map[full_name].append({
            'player_id': player_id,
            'full_name': full_name,
            'team_id': team_id,
            'position': position
        })
        total_players += 1
    
    cursor.close()
    
    # Log duplicate names for awareness
    duplicates = {name: players for name, players in player_map.items() if len(players) > 1}
    if duplicates:
        logger.info(f"Found {len(duplicates)} names with multiple players (will use context to disambiguate):")
        for name, players in list(duplicates.items())[:5]:  # Show first 5
            positions = ', '.join([f"{p['position']}/{p['team_id']}" for p in players])
            logger.debug(f"  {name}: {positions}")
        if len(duplicates) > 5:
            logger.debug(f"  ... and {len(duplicates) - 5} more")
    
    logger.info(f"Loaded {total_players} players ({len(player_map)} unique names)")
    return player_map

def fetch_book_map(conn) -> Dict[str, int]:
    """
    Fetch all bookmakers from database and create name -> ID mapping.
    
    Returns:
        Dictionary mapping book name to book_id
    """
    cursor = conn.cursor()
    query = "SELECT book_id, name FROM book"
    cursor.execute(query)
    
    book_map = {}
    for book_id, name in cursor.fetchall():
        book_map[name.lower()] = book_id
    
    cursor.close()
    logger.info(f"Loaded {len(book_map)} bookmakers from database")
    return book_map

def match_player_name(
    api_name: str, 
    player_map: Dict[str, List[Dict]], 
    game_teams: Tuple[int, int],
    market_key: str
) -> Optional[int]:
    """
    Match API player name to database player_id using fuzzy matching with context.
    Uses game teams and market type to disambiguate players with same name.
    
    Args:
        api_name: Player name from The Odds API
        player_map: Dictionary mapping player names to list of player dicts
        game_teams: Tuple of (home_team_id, away_team_id) for this game
        market_key: Market type (e.g., 'player_pass_yds') for position filtering
    
    Returns:
        player_id if match found, None otherwise
    """
    # Apply name overrides first
    lookup_name = config.PLAYER_NAME_OVERRIDES.get(api_name, api_name)
    
    # Try exact match first
    candidates = player_map.get(lookup_name)
    
    # If no exact match, try fuzzy matching
    if not candidates:
        result = process.extractOne(
            lookup_name, 
            player_map.keys(), 
            scorer=fuzz.ratio,
            score_cutoff=config.FUZZY_MATCH_THRESHOLD
        )
        
        if result:
            matched_name, score, _ = result
            logger.debug(f"Fuzzy matched '{api_name}' -> '{matched_name}' (score: {score})")
            candidates = player_map[matched_name]
        else:
            logger.warning(f"Could not match player name: {api_name}")
            return None
    
    # If only one candidate, return it
    if len(candidates) == 1:
        player = candidates[0]
        
        # Validate position makes sense for this market
        if not is_valid_position_for_market(player['position'], market_key):
            logger.warning(
                f"Position mismatch: {player['full_name']} ({player['position']}) "
                f"for market {market_key} - skipping"
            )
            return None
        
        return player['player_id']
    
    # Multiple candidates - use context to disambiguate
    logger.debug(f"Multiple players named '{lookup_name}': {len(candidates)} found")
    
    # Filter by team (players from teams in this game)
    team_matches = [p for p in candidates if p['team_id'] in game_teams]
    
    if not team_matches:
        # No team match - this could be a free agent or retired player
        logger.debug(f"No team match for '{api_name}' in this game's teams")
        team_matches = candidates  # Fall back to all candidates
    
    # Filter by position (based on market type)
    position_matches = [p for p in team_matches if is_valid_position_for_market(p['position'], market_key)]
    
    if len(position_matches) == 1:
        player = position_matches[0]
        logger.debug(
            f"Matched '{api_name}' to {player['full_name']} "
            f"({player['position']}, team {player['team_id']}) by context"
        )
        return player['player_id']
    
    if len(position_matches) > 1:
        # Still ambiguous - pick the first team match
        player = position_matches[0]
        logger.warning(
            f"Ambiguous match for '{api_name}': {len(position_matches)} candidates remain. "
            f"Using {player['full_name']} ({player['position']}, team {player['team_id']})"
        )
        return player['player_id']
    
    # No valid position matches
    if team_matches:
        positions = ', '.join([f"{p['position']}" for p in team_matches])
        logger.warning(
            f"No valid position for '{api_name}' in market '{market_key}'. "
            f"Candidates: {positions}"
        )
    
    return None


def is_valid_position_for_market(position: str, market_key: str) -> bool:
    """
    Check if a player's position makes sense for a given market.
    
    Args:
        position: Player position (QB, RB, WR, etc.)
        market_key: Market type (player_pass_yds, etc.)
    
    Returns:
        True if valid combination, False otherwise
    """
    # Define valid positions for each market
    valid_positions = {
        'player_pass_yds': ['QB'],
        'player_pass_tds': ['QB'],
        'player_pass_completions': ['QB'],
        'player_pass_attempts': ['QB'],
        'player_pass_interceptions': ['QB'],
        'player_pass_longest_completion': ['QB'],
        
        # QBs can rush! Important for mobile QBs like Josh Allen, Lamar Jackson
        'player_rush_yds': ['RB', 'FB', 'QB', 'WR'],  
        'player_rush_attempts': ['RB', 'FB', 'QB', 'WR'],
        'player_rush_longest': ['RB', 'FB', 'QB', 'WR'],
        
        # RBs can catch
        'player_reception_yds': ['WR', 'TE', 'RB', 'FB'],
        'player_receptions': ['WR', 'TE', 'RB', 'FB'],
        'player_reception_longest': ['WR', 'TE', 'RB', 'FB'],
        
        # Any offensive player can score TDs
        'player_anytime_td': ['QB', 'RB', 'FB', 'WR', 'TE'],
        'player_first_td': ['QB', 'RB', 'FB', 'WR', 'TE'],
        'player_last_td': ['QB', 'RB', 'FB', 'WR', 'TE'],
        
        # Kicking props
        'player_field_goals': ['K'],
        'player_kicking_points': ['K'],
    }
    
    allowed_positions = valid_positions.get(market_key, [])
    
    if not allowed_positions:
        # Unknown market - allow it
        return True
    
    # Check if position is in allowed list
    return position in allowed_positions

def get_or_create_book(conn, book_name: str, book_map: Dict[str, int]) -> int:
    """
    Get book_id for a bookmaker, creating it if it doesn't exist.
    
    Args:
        conn: Database connection
        book_name: Name of the bookmaker
        book_map: Dictionary mapping book names to IDs
    
    Returns:
        book_id
    """
    book_key = book_name.lower()
    
    if book_key in book_map:
        return book_map[book_key]
    
    # Create new book
    cursor = conn.cursor()
    query = "INSERT INTO book (name) VALUES (%s) RETURNING book_id"
    cursor.execute(query, (book_name,))
    book_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    book_map[book_key] = book_id
    logger.info(f"Created new bookmaker: {book_name} (ID: {book_id})")
    return book_id

# =========================================================
# THE ODDS API FUNCTIONS
# =========================================================

def fetch_historical_event_ids(api_key: str, date: datetime) -> List[Dict]:
    """
    Fetch historical event IDs for a given date.
    
    Args:
        api_key: The Odds API key
        date: Date to fetch events for
    
    Returns:
        List of event dictionaries with id, home_team, away_team
    """
    url = f"{config.ODDS_API_BASE_URL}/historical/sports/{config.SPORT_KEY}/events"
    
    params = {
        'apiKey': api_key,
        'date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'dateFormat': 'iso'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        events = data.get('data', [])
        
        logger.debug(f"Fetched {len(events)} events for {date.strftime('%Y-%m-%d')}")
        return events
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch historical events: {e}")
        return []

def find_event_id_for_game(api_key: str, game: Dict) -> Optional[str]:
    """
    Find The Odds API event ID for a SmartLine game.
    
    Args:
        api_key: The Odds API key
        game: Game dictionary with game_datetime_utc, home_team_name, away_team_name
    
    Returns:
        Event ID string if found, None otherwise
    """
    # Fetch events from game date
    events = fetch_historical_event_ids(api_key, game['game_datetime_utc'])
    
    # Match by team names
    home_team = game['home_team_name']
    away_team = game['away_team_name']
    
    for event in events:
        if event.get('home_team') == home_team and event.get('away_team') == away_team:
            logger.debug(f"Matched game {game['game_id']} to event {event['id']}")
            return event['id']
    
    logger.warning(f"Could not find event ID for game {game['game_id']}: {away_team} @ {home_team}")
    return None

def fetch_historical_player_odds(
    api_key: str, 
    event_id: str, 
    game_datetime: datetime,
    markets: List[str]
) -> Dict:
    """
    Fetch historical player prop odds for a specific event.
    
    Args:
        api_key: The Odds API key
        event_id: The Odds API event ID
        game_datetime: Game start time
        markets: List of market keys to fetch (e.g., ['player_pass_yds', 'player_pass_tds'])
    
    Returns:
        Dictionary with odds data
    """
    # Calculate timestamp (N hours before game start)
    odds_timestamp = game_datetime - timedelta(hours=config.HISTORICAL_OFFSET_HOURS)
    
    url = f"{config.ODDS_API_BASE_URL}/historical/sports/{config.SPORT_KEY}/events/{event_id}/odds"
    
    params = {
        'apiKey': api_key,
        'regions': ','.join(config.REGIONS),
        'markets': ','.join(markets),
        'oddsFormat': config.ODDS_FORMAT,
        'date': odds_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'dateFormat': 'iso'
    }
    
    # Add bookmakers if specified
    if config.BOOKMAKERS:
        params['bookmakers'] = ','.join(config.BOOKMAKERS)
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Fetched odds for event {event_id}")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch odds for event {event_id}: {e}")
        return {}

# =========================================================
# DATA PARSING FUNCTIONS
# =========================================================

def parse_player_odds(
    odds_data: Dict, 
    game_id: int,
    player_map: Dict[str, List[Dict]],
    book_map: Dict[str, int],
    game_teams: Tuple[int, int]
) -> List[Tuple]:
    """
    Parse player odds data from The Odds API response.
    
    Args:
        odds_data: Raw response from The Odds API
        game_id: SmartLine game_id
        player_map: Dictionary mapping player names to list of player dicts
        book_map: Dictionary mapping book names to IDs
        game_teams: Tuple of (home_team_id, away_team_id) for context matching
    
    Returns:
        List of tuples ready for database insertion
    """
    records = []
    
    # Extract the actual data (may be wrapped in 'data' key for historical endpoint)
    data = odds_data.get('data', odds_data)
    
    if not isinstance(data, dict):
        logger.warning(f"Unexpected odds data format for game {game_id}")
        return records
    
    pulled_at = odds_data.get('timestamp')
    if pulled_at:
        pulled_at = datetime.fromisoformat(pulled_at.replace('Z', '+00:00'))
    else:
        pulled_at = datetime.utcnow()
    
    bookmakers = data.get('bookmakers', [])
    
    for bookmaker in bookmakers:
        book_name = bookmaker.get('title', bookmaker.get('key', 'Unknown'))
        markets = bookmaker.get('markets', [])
        
        for market in markets:
            market_key = market.get('key')
            outcomes = market.get('outcomes', [])
            
            for outcome in outcomes:
                # Player name is in the 'description' field for player props
                player_name = outcome.get('description')
                
                if not player_name:
                    continue
                
                # Skip non-player entries
                if should_skip_player(player_name):
                    continue
                
                # Clean player name (remove team suffixes, etc.)
                player_name = clean_player_name(player_name)
                
                # Match player to database with game context
                player_id = match_player_name(player_name, player_map, game_teams, market_key)
                
                if not player_id:
                    continue
                
                bet_type = outcome.get('name', '').lower()  # 'over', 'under', 'yes', 'no'
                line_value = outcome.get('point')
                odds_american = outcome.get('price')
                
                # Validate required fields
                if not bet_type or not odds_american:
                    logger.warning(f"Missing bet_type or odds for {player_name} in {market_key}")
                    continue
                
                # For anytime_td and similar markets, line_value may be None
                # These are Yes/No props, not over/under with a line
                if market_key in ['player_anytime_td', 'player_first_td', 'player_last_td']:
                    # For TD props, use a default line of 0.5 (over 0.5 = Yes, under 0.5 = No)
                    if line_value is None:
                        line_value = 0.5
                    
                    # Convert yes/no to over/under to match database constraint
                    if bet_type == 'yes':
                        bet_type = 'over'
                    elif bet_type == 'no':
                        bet_type = 'under'
                    
                elif line_value is None:
                    # For other props, line_value is required
                    logger.warning(f"Missing line_value for {player_name} in {market_key}")
                    continue
                
                # Final validation: bet_type must be 'over' or 'under'
                if bet_type not in ['over', 'under']:
                    logger.warning(f"Invalid bet_type '{bet_type}' for {player_name} in {market_key}, skipping")
                    continue
                
                # Store as tuple (we'll resolve book_id in bulk later)
                records.append((
                    game_id,
                    player_id,
                    book_name,  # Will resolve to book_id later
                    market_key,
                    bet_type,
                    float(line_value),
                    odds_american,
                    pulled_at,
                    'the-odds-api'
                ))
    
    logger.debug(f"Parsed {len(records)} player odds records for game {game_id}")
    return records


def should_skip_player(player_name: str) -> bool:
    """
    Check if a 'player' name should be skipped (not actually a player).
    
    Args:
        player_name: Player name from API
    
    Returns:
        True if should skip, False otherwise
    """
    skip_patterns = [
        'defense',
        'special teams',
        'no touchdown',
        'no td',
        'no goal',
        'no scorer',
    ]
    
    name_lower = player_name.lower()
    
    for pattern in skip_patterns:
        if pattern in name_lower:
            return True
    
    return False


def clean_player_name(player_name: str) -> str:
    """
    Clean player name from API to improve matching.
    
    Removes:
    - Team suffixes like " (BAL)"
    - Extra whitespace
    
    Args:
        player_name: Raw player name from API
    
    Returns:
        Cleaned player name
    """
    import re
    
    # Remove team suffix like " (BAL)"
    player_name = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', player_name)
    
    # Remove extra whitespace
    player_name = ' '.join(player_name.split())
    
    return player_name.strip()

# =========================================================
# DATABASE INSERTION
# =========================================================

def insert_player_odds_batch(conn, records: List[Tuple], book_map: Dict[str, int]):
    """
    Insert player odds records into database in batches.
    
    Args:
        conn: Database connection
        records: List of tuples with odds data (book_name not yet resolved to book_id)
        book_map: Dictionary mapping book names to IDs
    """
    if not records:
        return
    
    # Resolve book names to book_ids
    resolved_records = []
    for record in records:
        game_id, player_id, book_name, market_key, bet_type, line_value, odds_american, pulled_at, source = record
        
        # Get or create book_id
        book_id = get_or_create_book(conn, book_name, book_map)
        
        resolved_records.append((
            game_id,
            player_id,
            book_id,
            market_key,
            bet_type,
            line_value,
            odds_american,
            pulled_at,
            source
        ))
    
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO player_odds (
            game_id, player_id, book_id, market_key, bet_type,
            line_value, odds_american, pulled_at_utc, source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (game_id, player_id, book_id, market_key, bet_type, pulled_at_utc)
        DO NOTHING
    """
    
    execute_batch(cursor, insert_query, resolved_records, page_size=config.BATCH_SIZE)
    conn.commit()
    cursor.close()
    
    logger.info(f"Inserted {len(resolved_records)} player odds records")

# =========================================================
# MAIN ETL LOGIC
# =========================================================

def process_game(
    game: Dict,
    api_key: str,
    conn,
    player_map: Dict[str, List[Dict]],
    book_map: Dict[str, int],
    dry_run: bool = False
) -> Dict:
    """
    Process a single game: fetch odds and insert into database.
    
    Args:
        game: Game dictionary
        api_key: The Odds API key
        conn: Database connection
        player_map: Player name to list of player dicts mapping
        book_map: Book name to ID mapping
        dry_run: If True, don't make API calls or insert data
    
    Returns:
        Dictionary with processing stats
    """
    game_id = game['game_id']
    game_datetime = game['game_datetime_utc']
    home_team_id = game['home_team_id']
    away_team_id = game['away_team_id']
    game_teams = (home_team_id, away_team_id)
    
    stats = {
        'game_id': game_id,
        'success': False,
        'records_inserted': 0,
        'credits_used': 0,
        'skipped': False,
        'error': None
    }
    
    # Check if already processed
    if config.SKIP_EXISTING and check_existing_odds(conn, game_id):
        logger.info(f"Game {game_id} already has odds data, skipping")
        stats['skipped'] = True
        stats['success'] = True
        return stats
    
    if dry_run:
        # Just calculate cost, don't fetch
        stats['credits_used'] = config.estimate_cost_per_game()
        stats['success'] = True
        return stats
    
    # Find event ID
    event_id = find_event_id_for_game(api_key, game)
    
    if not event_id:
        stats['error'] = "Could not find event ID"
        return stats
    
    # Fetch odds for all markets
    odds_data = fetch_historical_player_odds(
        api_key,
        event_id,
        game_datetime,
        config.ALL_MARKETS
    )
    
    if not odds_data:
        stats['error'] = "Failed to fetch odds data"
        return stats
    
    # Parse odds with game context
    records = parse_player_odds(odds_data, game_id, player_map, book_map, game_teams)
    
    # Insert into database
    if records:
        insert_player_odds_batch(conn, records, book_map)
        stats['records_inserted'] = len(records)
    
    stats['credits_used'] = config.estimate_cost_per_game()
    stats['success'] = True
    
    return stats

def run_etl(season: int, game_ids: Optional[List[int]] = None, dry_run: bool = False):
    """
    Main ETL orchestration function.
    
    Args:
        season: Season year to process
        game_ids: Optional list of specific game IDs
        dry_run: If True, calculate costs but don't fetch/insert data
    """
    logger.info("=" * 60)
    logger.info(f"Starting Player Odds ETL for {season} season")
    if dry_run:
        logger.info("DRY RUN MODE - No API calls or database writes")
    logger.info("=" * 60)
    
    # Validate environment
    validate_environment()
    
    # Get API key
    api_key = os.environ.get('ODDS_API_KEY')
    
    # Connect to database
    conn = get_conn()
    logger.info("Database connection established")
    
    try:
        # Fetch games
        games = fetch_games_for_season(conn, season, game_ids)
        
        if not games:
            logger.warning(f"No games found for season {season}")
            return
        
        # Load player and book mappings
        player_map = fetch_player_map(conn)
        book_map = fetch_book_map(conn)
        
        # Process each game
        total_stats = {
            'games_processed': 0,
            'games_skipped': 0,
            'games_failed': 0,
            'total_records': 0,
            'total_credits': 0
        }
        
        for i, game in enumerate(games, 1):
            logger.info(f"Processing game {i}/{len(games)}: {game['away_team_name']} @ {game['home_team_name']}")
            
            stats = process_game(game, api_key, conn, player_map, book_map, dry_run)
            
            total_stats['games_processed'] += 1
            total_stats['total_records'] += stats['records_inserted']
            total_stats['total_credits'] += stats['credits_used']
            
            if stats['skipped']:
                total_stats['games_skipped'] += 1
            elif not stats['success']:
                total_stats['games_failed'] += 1
                logger.warning(f"Failed to process game {game['game_id']}: {stats['error']}")
            
            # Rate limiting
            if not dry_run and i < len(games):
                time.sleep(config.RATE_LIMIT_DELAY)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("ETL COMPLETE - Summary:")
        logger.info("=" * 60)
        logger.info(f"Total games: {len(games)}")
        logger.info(f"Games processed: {total_stats['games_processed']}")
        logger.info(f"Games skipped: {total_stats['games_skipped']}")
        logger.info(f"Games failed: {total_stats['games_failed']}")
        logger.info(f"Total records inserted: {total_stats['total_records']}")
        logger.info(f"Total API credits used: {total_stats['total_credits']}")
        logger.info("=" * 60)
        
    finally:
        conn.close()
        logger.info("Database connection closed")

# =========================================================
# CLI INTERFACE
# =========================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='SmartLine Player Odds ETL - Fetch historical player prop odds',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to estimate costs
  python nfl_player_odds_etl.py --season 2023 --dry-run
  
  # Process full 2023 season
  python nfl_player_odds_etl.py --season 2023
  
  # Process specific games
  python nfl_player_odds_etl.py --season 2023 --games 1119,1120,1121
  
  # Process single game with debug logging
  python nfl_player_odds_etl.py --season 2023 --games 1119 --debug
        """
    )
    
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help='Season year to process (e.g., 2023)'
    )
    
    parser.add_argument(
        '--games',
        type=str,
        help='Comma-separated list of game IDs to process (optional)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Calculate costs without making API calls or database writes'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse game IDs if provided
    game_ids = None
    if args.games:
        try:
            game_ids = [int(gid.strip()) for gid in args.games.split(',')]
        except ValueError:
            logger.error("Invalid game IDs format. Use comma-separated integers (e.g., 1119,1120)")
            sys.exit(1)
    
    # Run ETL
    try:
        run_etl(args.season, game_ids, args.dry_run)
    except KeyboardInterrupt:
        logger.info("\nETL interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"ETL failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()