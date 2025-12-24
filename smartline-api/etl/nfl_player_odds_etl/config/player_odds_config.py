"""
SmartLine Player Odds ETL - Configuration
==========================================
Defines which MARKETS to fetch for the 2023 NFL season.

Strategy: Market-Based Approach
- Fetch ALL markets we care about
- The API returns whatever players bookmakers are offering props for
- We match those players to our database and insert everything

Key Insight: We don't pre-define players - we get whoever the bookmakers
are offering props for, which automatically includes:
- Starting players
- Backup QBs who play
- Emerging rookies
- Hot-streak players
- Anyone bookmakers think bettors want

Estimated Cost: 50-80 credits per game depending on markets selected
"""

# =========================================================
# MARKET CONFIGURATION
# =========================================================
# Define which betting markets to fetch from The Odds API
# The API will return ALL players that have props available
# for these markets from the bookmakers
# =========================================================

# =========================================================
# QUARTERBACK MARKETS
# =========================================================
QB_MARKETS = [
    'player_pass_yds',                    # Passing yards
    'player_pass_tds',                    # Passing touchdowns
    # Optional additional markets (uncomment to enable):
    # 'player_pass_completions',          # Completions
    # 'player_pass_attempts',             # Pass attempts  
    # 'player_pass_interceptions',        # Interceptions
    # 'player_pass_longest_completion',   # Longest completion
]

# =========================================================
# RUNNING BACK MARKETS
# =========================================================
RB_MARKETS = [
    'player_rush_yds',                    # Rushing yards
    'player_anytime_td',                  # Anytime touchdown scorer
    # Optional additional markets:
    # 'player_rush_attempts',             # Rush attempts
    # 'player_rush_longest',              # Longest rush
]

# =========================================================
# WIDE RECEIVER / TIGHT END MARKETS
# =========================================================
RECEIVER_MARKETS = [
    'player_reception_yds',               # Receiving yards
    # Note: player_anytime_td is already in RB_MARKETS
    # Optional additional markets:
    # 'player_receptions',                # Total receptions
    # 'player_reception_longest',         # Longest reception
]

# =========================================================
# KICKER MARKETS (Optional)
# =========================================================
KICKER_MARKETS = [
    # Uncomment if you want kicker props:
    # 'player_field_goals',               # Field goals made
    # 'player_kicking_points',            # Total kicking points
]

# =========================================================
# ALL MARKETS COMBINED
# =========================================================
# Combine all enabled markets into one list
# This is what gets sent to The Odds API
ALL_MARKETS = list(set(
    QB_MARKETS +
    RB_MARKETS +
    RECEIVER_MARKETS +
    KICKER_MARKETS
))

# =========================================================
# API CONFIGURATION
# =========================================================

# The Odds API settings
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'
SPORT_KEY = 'americanfootball_nfl'

# Regions to fetch (usually just US for NFL)
REGIONS = ['us']

# Bookmakers to fetch (leave empty for all, or specify favorites)
# Empty list = all available bookmakers
# Specified list = only those bookmakers (saves credits if fewer bookmakers)
BOOKMAKERS = ['draftkings', 'fanduel', 'betmgm']  # [] means all bookmakers

# Odds format
ODDS_FORMAT = 'american'  # American odds format (-110, +150, etc.)

# =========================================================
# TIMING CONFIGURATION
# =========================================================

# How many hours before game start to pull odds
# 1 hour = "closing lines" (most accurate, widely referenced)
# 24 hours = "opening lines" (more volatile)
HISTORICAL_OFFSET_HOURS = 1

# Rate limiting (requests per second)
RATE_LIMIT_DELAY = 1.0  # seconds between API calls

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

# These will be read from environment variables in the ETL script
# Listed here for documentation purposes
REQUIRED_ENV_VARS = [
    'ODDS_API_KEY',      # Your The Odds API key
    'PGHOST',            # PostgreSQL host
    'PGDATABASE',        # Database name
    'PGUSER',            # Database user
    'PGPASSWORD',        # Database password
    'PGPORT',            # Database port (usually 5432)
]

# =========================================================
# ETL BEHAVIOR CONFIGURATION
# =========================================================

# Season to process
TARGET_SEASON = 2023

# Whether to skip games that already have odds data
SKIP_EXISTING = True

# Batch size for database inserts
BATCH_SIZE = 100

# Logging configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =========================================================
# COST ESTIMATION
# =========================================================

# Cost per game calculation
# Formula: 10 × [number of markets] × [number of regions]

def estimate_cost_per_game():
    """
    Calculate estimated API credits per game.
    
    Cost is based on unique markets, NOT number of players.
    The API returns all available players for each market.
    
    Example with current config:
    - QB markets: player_pass_yds, player_pass_tds (2)
    - RB markets: player_rush_yds, player_anytime_td (2) 
    - Receiver markets: player_reception_yds (1)
    - Total unique: 5 markets (player_anytime_td shared between RB/WR)
    
    Cost = 10 × 5 markets × 1 region = 50 credits/game
    
    Each market may return 5-50+ players depending on:
    - How many players bookmakers are offering props for
    - The specific market (passing yards = fewer players, anytime TD = many)
    - The game (primetime games = more props available)
    """
    unique_markets = len(ALL_MARKETS)
    num_regions = len(REGIONS)
    cost_per_game = 10 * unique_markets * num_regions
    return cost_per_game

def estimate_season_cost(num_games=285):
    """
    Estimate total cost for full season.
    
    2023 NFL Season:
    - Regular season: 272 games
    - Playoffs: ~13 games
    - Total: ~285 games
    """
    return estimate_cost_per_game() * num_games

def estimate_records_per_game():
    """
    Rough estimate of database records per game.
    
    Actual numbers vary by game, but typical ranges:
    - player_pass_yds: 4-8 QBs × 2 bet types × 5 books = 40-80 records
    - player_rush_yds: 10-20 RBs × 2 bet types × 5 books = 100-200 records
    - player_anytime_td: 30-50 players × 2 bet types × 5 books = 300-500 records
    - player_reception_yds: 15-30 receivers × 2 bet types × 5 books = 150-300 records
    
    Total per game: ~600-1,000 records
    Full season: ~180,000-285,000 records
    """
    # Conservative estimate
    return 750

def estimate_season_records(num_games=285):
    """Total records for full season."""
    return estimate_records_per_game() * num_games

# =========================================================
# PLAYER NAME MATCHING CONFIGURATION
# =========================================================

# Threshold for fuzzy matching player names (0-100)
# 85 = pretty strict, 70 = more lenient
FUZZY_MATCH_THRESHOLD = 85

# Known name variations to handle
# Maps API name -> Database name
PLAYER_NAME_OVERRIDES = {
    'Patrick Mahomes II': 'Patrick Mahomes',
    'CeeDee Lamb': "CeeDee Lamb",
    'AJ Brown': 'AJ Brown',
    'Ja\'Marr Chase': "Ja'Marr Chase",
    'Odell Beckham Jr.': 'Odell Beckham Jr',
    'Odell Beckham': 'Odell Beckham Jr',
    'Marvin Jones Jr.': 'Marvin Jones',
    'Marvin Jones': 'Marvin Jones',
    'Irv Smith Jr.': 'Irv Smith Jr',
    'Irv Smith': 'Irv Smith Jr',
    'Pierre Strong Jr.': 'Pierre Strong Jr',
    'Pierre Strong': 'Pierre Strong Jr',
    'Richie James Jr.': 'Richie James',
    'Tank Dell': 'Nathaniel Dell',  # Tank is nickname for Nathaniel
    'CJ Stroud': 'C.J. Stroud',
    # Add more as discovered during ETL runs
}

# =========================================================
# USAGE INSTRUCTIONS
# =========================================================

"""
To modify this configuration:

1. **Add/remove markets** from QB_MARKETS, RB_MARKETS, etc.
   - More markets = more data but higher cost
   - Cost = 10 × number of unique markets × regions

2. **Adjust timing** with HISTORICAL_OFFSET_HOURS
   - 1 hour = closing lines (most accurate)
   - 24 hours = opening lines (more volatile)

3. **Filter bookmakers** with BOOKMAKERS list
   - Empty list = all bookmakers (recommended)
   - Specific list = only those books (may miss data)

4. **Cost calculation** is automatic based on unique markets
   - player_anytime_td appears in both RB and receiver lists
   - But only counted once in cost calculation
   
Example configurations:

MINIMAL (lowest cost):
    QB_MARKETS = ['player_pass_yds']
    RB_MARKETS = ['player_rush_yds']  
    RECEIVER_MARKETS = []
    Cost: 20 credits/game

RECOMMENDED (good balance):
    QB_MARKETS = ['player_pass_yds', 'player_pass_tds']
    RB_MARKETS = ['player_rush_yds', 'player_anytime_td']
    RECEIVER_MARKETS = ['player_reception_yds']
    Cost: 50 credits/game

COMPREHENSIVE (all major props):
    QB_MARKETS = ['player_pass_yds', 'player_pass_tds', 'player_pass_interceptions']
    RB_MARKETS = ['player_rush_yds', 'player_rush_attempts', 'player_anytime_td']
    RECEIVER_MARKETS = ['player_reception_yds', 'player_receptions']
    Cost: 70 credits/game
"""

# =========================================================
# PRINT CONFIGURATION SUMMARY
# =========================================================

if __name__ == '__main__':
    print("=" * 60)
    print("SmartLine Player Odds ETL - Configuration Summary")
    print("=" * 60)
    print(f"\n📊 MARKETS CONFIGURED:")
    print(f"\nQuarterback Markets ({len(QB_MARKETS)}):")
    for market in QB_MARKETS:
        print(f"  • {market}")
    print(f"\nRunning Back Markets ({len(RB_MARKETS)}):")
    for market in RB_MARKETS:
        print(f"  • {market}")
    print(f"\nReceiver Markets ({len(RECEIVER_MARKETS)}):")
    for market in RECEIVER_MARKETS:
        print(f"  • {market}")
    if KICKER_MARKETS:
        print(f"\nKicker Markets ({len(KICKER_MARKETS)}):")
        for market in KICKER_MARKETS:
            print(f"  • {market}")
    
    print(f"\n🎯 TOTAL UNIQUE MARKETS: {len(ALL_MARKETS)}")
    print(f"Markets: {', '.join(ALL_MARKETS)}")
    
    print(f"\n💰 COST ESTIMATE:")
    print(f"  Formula: 10 × [markets] × [regions]")
    print(f"  Markets: {len(ALL_MARKETS)}")
    print(f"  Regions: {len(REGIONS)}")
    print(f"  Per Game: {estimate_cost_per_game()} credits")
    print(f"  Full Season (285 games): {estimate_season_cost():,} credits")
    
    print(f"\n📊 DATA VOLUME ESTIMATE:")
    print(f"  Records per game: ~{estimate_records_per_game():,}")
    print(f"  Full season: ~{estimate_season_records():,} records")
    print(f"\n  Note: API returns ALL players with available props")
    print(f"        No need to pre-define player lists!")
    print("=" * 60)