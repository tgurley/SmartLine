import os
import requests
from datetime import datetime, timedelta
from etl.db import get_conn
import time
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# ==========================================================
# CONFIG
# ==========================================================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    raise RuntimeError("ODDS_API_KEY environment variable is not set")

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "americanfootball_nfl"
SEASON_YEAR = 2023

REGIONS = "us"
ODDS_FORMAT = "american"

MARKETS_MAP = {
    "h2h": "moneyline",
    "spreads": "spread",
    "totals": "total"
}

# ==========================================================
# SNAPSHOT SELECTOR - Post-Processing Logic
# ==========================================================

class SmartSnapshotSelector:
    """Select best opening and closing from all available snapshots"""
    
    def __init__(self):
        self.stats = {
            'perfect_opening': 0,      # 5-14 days before
            'fallback_opening': 0,     # Outside ideal window
            'perfect_closing': 0,      # 0-6 hours before
            'fallback_closing': 0,     # Outside ideal window
            'same_snapshot': 0,        # Only 1 snapshot available
            'no_snapshots': 0          # No data at all
        }
    
    def select_snapshots(self, game, all_snapshots_for_game):
        """
        Given all snapshots for a game, select the best opening and closing.
        
        Returns: {
            'opening': (timestamp, event_data, label),
            'closing': (timestamp, event_data, label),
            'same': bool  # True if opening == closing
        }
        """
        kickoff = game['kickoff']
        
        # Filter to only snapshots BEFORE kickoff
        valid_snapshots = []
        for snapshot_time, event_data in all_snapshots_for_game:
            if snapshot_time < kickoff:
                hours_before = (kickoff - snapshot_time).total_seconds() / 3600
                valid_snapshots.append((snapshot_time, event_data, hours_before))
        
        if not valid_snapshots:
            self.stats['no_snapshots'] += 1
            return {'opening': None, 'closing': None, 'same': False}
        
        # Sort by time: earliest first
        valid_snapshots.sort(key=lambda x: x[0])
        
        # SELECT OPENING: Earliest snapshot (prefer 5-14 days before)
        opening = self._select_opening(valid_snapshots, kickoff)
        
        # SELECT CLOSING: Latest snapshot (prefer 0-6 hours before)
        closing = self._select_closing(valid_snapshots, kickoff)
        
        # Check if they're the same
        same = opening[0] == closing[0] if opening and closing else False
        if same:
            self.stats['same_snapshot'] += 1
        
        return {
            'opening': opening,
            'closing': closing,
            'same': same
        }
    
    def _select_opening(self, snapshots, kickoff):
        """Select best opening line (earliest snapshot, prefer 5-14 days)"""
        # Ideal range: 5-14 days (120-336 hours)
        ideal_candidates = []
        for snap_time, event, hours_before in snapshots:
            if 120 <= hours_before <= 336:  # 5-14 days
                ideal_candidates.append((snap_time, event, hours_before))
        
        if ideal_candidates:
            # Pick earliest in ideal range
            best = max(ideal_candidates, key=lambda x: x[2])
            days = best[2] / 24
            self.stats['perfect_opening'] += 1
            return (best[0], best[1], f"{days:.1f} days")
        
        # Fallback: use earliest available
        best = max(snapshots, key=lambda x: x[2])  # Max hours = earliest
        days = best[2] / 24
        self.stats['fallback_opening'] += 1
        return (best[0], best[1], f"{days:.1f} days (early)")
    
    def _select_closing(self, snapshots, kickoff):
        """Select best closing line (latest snapshot, prefer 0-6 hours)"""
        # Ideal range: 0-6 hours
        ideal_candidates = []
        for snap_time, event, hours_before in snapshots:
            if 0 <= hours_before <= 6:
                ideal_candidates.append((snap_time, event, hours_before))
        
        if ideal_candidates:
            # Pick latest in ideal range
            best = min(ideal_candidates, key=lambda x: x[2])
            self.stats['perfect_closing'] += 1
            return (best[0], best[1], f"{best[2]:.1f} hours")
        
        # Fallback: use latest available
        best = min(snapshots, key=lambda x: x[2])  # Min hours = latest
        hours = best[2]
        days = hours / 24
        self.stats['fallback_closing'] += 1
        
        if days >= 1:
            return (best[0], best[1], f"{days:.1f} days (late)")
        else:
            return (best[0], best[1], f"{hours:.1f} hours")

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def get_game_weeks(conn):
    """Get all weeks"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            g.week,
            MIN(g.game_datetime_utc) AS earliest_kickoff,
            MAX(g.game_datetime_utc) AS latest_kickoff,
            COUNT(*) AS num_games
        FROM game g
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = %s
        )
        GROUP BY g.week
        ORDER BY g.week;
    """, (SEASON_YEAR,))
    
    weeks = cur.fetchall()
    cur.close()
    return weeks

def get_all_games(conn):
    """Get all games organized by week"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            g.game_id,
            g.game_datetime_utc,
            g.week,
            ht.name AS home_team_name,
            at.name AS away_team_name
        FROM game g
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = %s
        )
        ORDER BY g.week, g.game_datetime_utc;
    """, (SEASON_YEAR,))
    
    games = cur.fetchall()
    cur.close()
    
    games_dict = {}
    for game_id, kickoff, week, home, away in games:
        games_dict[game_id] = {
            'game_id': game_id,
            'kickoff': kickoff,
            'week': week,
            'home_team': home,
            'away_team': away
        }
    
    return games_dict

def get_book_map(conn):
    """Get book name -> book_id mapping"""
    cur = conn.cursor()
    cur.execute("SELECT book_id, name FROM book;")
    book_map = {row[1]: row[0] for row in cur.fetchall()}
    cur.close()
    return book_map

def normalize_team_name(name):
    """Normalize team name for matching"""
    return name.strip().lower()

def fetch_historical_odds_batch(snapshot_date):
    """Fetch historical odds batch"""
    url = f"{BASE_URL}/historical/sports/{SPORT}/odds"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": "h2h,spreads,totals",
        "oddsFormat": ODDS_FORMAT,
        "date": snapshot_date
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        
        remaining = resp.headers.get("x-requests-remaining")
        used = resp.headers.get("x-requests-used")
        if remaining:
            print(f"    API quota: {used} used, {remaining} remaining")
        
        return resp.json()
    except Exception as e:
        print(f"    ERROR: {str(e)}")
        return None

def match_event_to_game(event, all_games):
    """Match API event to database game by team names"""
    api_home = normalize_team_name(event.get("home_team", ""))
    api_away = normalize_team_name(event.get("away_team", ""))
    
    for game_id, game in all_games.items():
        db_home = normalize_team_name(game['home_team'])
        db_away = normalize_team_name(game['away_team'])
        
        if api_home == db_home and api_away == db_away:
            return game_id
    
    return None

def insert_odds_line(conn, game_id, book_id, market, side, line_value, price_american, pulled_at_utc):
    """Insert a single odds line"""
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO odds_line (
            game_id, book_id, market, side, line_value, 
            price_american, pulled_at_utc, source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'odds-api')
        ON CONFLICT (game_id, book_id, market, side, pulled_at_utc) DO NOTHING;
    """, (game_id, book_id, market, side, line_value, price_american, pulled_at_utc))
    
    inserted = cur.rowcount
    cur.close()
    return inserted

def process_event_odds(event, game_id, book_map, conn, snapshot_time):
    """Insert all odds from an event"""
    inserted = 0
    
    for bookmaker in event.get("bookmakers", []):
        book_id = book_map.get(bookmaker.get("title"))
        if not book_id:
            continue
        
        for market in bookmaker.get("markets", []):
            market_db = MARKETS_MAP.get(market.get("key"))
            if not market_db:
                continue
            
            for outcome in market.get("outcomes", []):
                price = outcome.get("price")
                if not price or abs(price) > 10000:
                    continue
                
                # Determine side and line_value based on market type
                team_name = outcome.get("name", "")
                point = outcome.get("point")
                
                if market.get("key") == "h2h":
                    # Moneyline - determine home/away by team name matching
                    # For simplicity, we'll use a heuristic or skip complex matching
                    side = "home" if "home" in team_name.lower() else "away"
                    line_value = None
                elif market.get("key") == "spreads":
                    side = "home" if "home" in team_name.lower() else "away"
                    line_value = point
                elif market.get("key") == "totals":
                    side = "over" if team_name == "Over" else "under"
                    line_value = point
                else:
                    continue
                
                inserted += insert_odds_line(
                    conn, game_id, book_id, market_db, side,
                    line_value, price, snapshot_time
                )
    
    return inserted

# ==========================================================
# MAIN ETL
# ==========================================================

def load_odds_hybrid(dry_run=True):
    """
    Hybrid approach: Fetch all data, then intelligently select opening + closing.
    """
    conn = get_conn()
    
    weeks = get_game_weeks(conn)
    all_games = get_all_games(conn)
    book_map = get_book_map(conn)
    
    selector = SmartSnapshotSelector()
    
    print(f"\n{'='*70}")
    print(f"HYBRID ODDS ETL: Fetch All, Then Filter")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*70}")
    print(f"Total games: {len(all_games)}")
    print(f"Total weeks: {len(weeks)}")
    print(f"{'='*70}\n")
    
    # PHASE 1: FETCH ALL SNAPSHOTS
    print("PHASE 1: Fetching all available snapshots...")
    print("="*70)
    
    # Store all snapshots: game_id -> [(timestamp, event_data), ...]
    game_snapshots = defaultdict(list)
    api_calls = 0
    
    for week_num, earliest_kickoff, latest_kickoff, num_games in weeks:
        print(f"\nWeek {week_num}: Fetching batches...")
        
        # Fetch opening batch (7 days before first game)
        opening_time = earliest_kickoff - timedelta(days=7)
        opening_str = opening_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        print(f"  [OPENING] {opening_str}")
        opening_batch = fetch_historical_odds_batch(opening_str)
        api_calls += 1
        
        if opening_batch:
            actual_time = datetime.fromisoformat(
                opening_batch.get("timestamp", opening_str).replace('Z', '+00:00')
            )
            for event in opening_batch.get("data", []):
                game_id = match_event_to_game(event, all_games)
                if game_id:
                    game_snapshots[game_id].append((actual_time, event))
        
        time.sleep(1)
        
        # Fetch closing batch (2 hours before last game)
        closing_time = latest_kickoff - timedelta(hours=2)
        closing_str = closing_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        print(f"  [CLOSING] {closing_str}")
        closing_batch = fetch_historical_odds_batch(closing_str)
        api_calls += 1
        
        if closing_batch:
            actual_time = datetime.fromisoformat(
                closing_batch.get("timestamp", closing_str).replace('Z', '+00:00')
            )
            for event in closing_batch.get("data", []):
                game_id = match_event_to_game(event, all_games)
                if game_id:
                    game_snapshots[game_id].append((actual_time, event))
        
        time.sleep(1)
    
    print(f"\n{'='*70}")
    print(f"Fetching complete! API calls: {api_calls}")
    print(f"Games with data: {len(game_snapshots)}/{len(all_games)}")
    print(f"{'='*70}\n")
    
    # PHASE 2: SELECT BEST SNAPSHOTS
    print("PHASE 2: Selecting best opening + closing for each game...")
    print("="*70)
    
    selected_snapshots = {}
    
    for game_id, game in all_games.items():
        snapshots = game_snapshots.get(game_id, [])
        selection = selector.select_snapshots(game, snapshots)
        selected_snapshots[game_id] = selection
    
    # PHASE 3: REPORT OR INSERT
    if dry_run:
        print("\nDRY RUN RESULTS:")
        print("="*70)
        
        for game_id in sorted(all_games.keys(), key=lambda gid: (all_games[gid]['week'], all_games[gid]['kickoff'])):
            game = all_games[game_id]
            selection = selected_snapshots[game_id]
            
            opening = selection['opening']
            closing = selection['closing']
            same = selection['same']
            
            print(f"\n{game['away_team']} @ {game['home_team']} (Week {game['week']})")
            
            if opening:
                print(f"  Opening: {opening[0]} ({opening[2]})")
            else:
                print(f"  Opening: NOT FOUND")
            
            if closing:
                if same:
                    print(f"  Closing: SAME AS OPENING")
                else:
                    print(f"  Closing: {closing[0]} ({closing[2]})")
            else:
                print(f"  Closing: NOT FOUND")
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Perfect opening (5-14 days): {selector.stats['perfect_opening']}")
        print(f"Fallback opening: {selector.stats['fallback_opening']}")
        print(f"Perfect closing (0-6 hours): {selector.stats['perfect_closing']}")
        print(f"Fallback closing: {selector.stats['fallback_closing']}")
        print(f"Same snapshot used: {selector.stats['same_snapshot']}")
        print(f"No snapshots: {selector.stats['no_snapshots']}")
        
        games_with_2 = sum(1 for s in selected_snapshots.values() 
                          if s['opening'] and s['closing'] and not s['same'])
        games_with_1 = sum(1 for s in selected_snapshots.values() 
                          if (s['opening'] or s['closing']) and 
                          (not s['opening'] or not s['closing'] or s['same']))
        games_with_0 = selector.stats['no_snapshots']
        
        print(f"\nGames with 2 different snapshots: {games_with_2}")
        print(f"Games with 1 snapshot: {games_with_1}")
        print(f"Games with 0 snapshots: {games_with_0}")
        print(f"{'='*70}\n")
        
        print("To run live: python -m etl.odds_hybrid --live")
    
    else:
        # LIVE MODE: Actually insert
        print("\nLIVE MODE: Inserting odds...")
        total_inserted = 0
        
        for game_id, selection in selected_snapshots.items():
            opening = selection['opening']
            closing = selection['closing']
            same = selection['same']
            
            # Insert opening
            if opening and not same:
                inserted = process_event_odds(opening[1], game_id, book_map, conn, opening[0])
                total_inserted += inserted
            
            # Insert closing
            if closing:
                inserted = process_event_odds(closing[1], game_id, book_map, conn, closing[0])
                total_inserted += inserted
        
        conn.commit()
        conn.close()
        
        print(f"\n{'='*70}")
        print("COMPLETE!")
        print(f"{'='*70}")
        print(f"Total odds lines inserted: {total_inserted:,}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    import sys
    
    if "--live" in sys.argv:
        print("\n⚠️  LIVE MODE - Data will be inserted!")
        response = input("Continue? (yes/no): ")
        if response.lower() == 'yes':
            load_odds_hybrid(dry_run=False)
    else:
        load_odds_hybrid(dry_run=True)