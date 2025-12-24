#!/usr/bin/env python3
"""
Player Name Override Generator
==============================
Analyzes ETL logs from Week 1 and helps generate PLAYER_NAME_OVERRIDES.

Usage:
    # Run Week 1 ETL with debug logging
    python nfl_player_odds_etl.py --season 2023 --debug 2>&1 | tee week1_run.log
    
    # Analyze the log to find unmatched names
    python generate_overrides.py week1_run.log
    
This script will:
1. Extract all "Could not match player name" warnings
2. Search your database for likely matches
3. Generate PLAYER_NAME_OVERRIDES code you can paste into config
"""

import sys
import re
import os
import psycopg2
from collections import Counter
from rapidfuzz import fuzz, process

def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )

def extract_unmatched_names(log_file):
    """Extract all unmatched player names from log file."""
    unmatched = []
    
    pattern = r"Could not match player name: (.+?)$"
    
    with open(log_file, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                player_name = match.group(1).strip()
                unmatched.append(player_name)
    
    return unmatched

def get_all_players(conn):
    """Fetch all players from database."""
    cursor = conn.cursor()
    query = "SELECT player_id, full_name, position FROM player ORDER BY full_name"
    cursor.execute(query)
    
    players = {}
    for player_id, full_name, position in cursor.fetchall():
        players[full_name] = {
            'player_id': player_id,
            'position': position
        }
    
    cursor.close()
    return players

def find_best_match(api_name, db_players, threshold=70):
    """Find best fuzzy match for a player name."""
    result = process.extractOne(
        api_name,
        db_players.keys(),
        scorer=fuzz.ratio,
        score_cutoff=threshold
    )
    
    if result:
        matched_name, score, _ = result
        return matched_name, score
    
    return None, 0

def generate_overrides(log_file):
    """Generate PLAYER_NAME_OVERRIDES from log file."""
    print("=" * 70)
    print("Player Name Override Generator")
    print("=" * 70)
    print()
    
    # Extract unmatched names
    print(f"📖 Reading log file: {log_file}")
    unmatched_names = extract_unmatched_names(log_file)
    
    if not unmatched_names:
        print("✅ No unmatched player names found!")
        return
    
    # Count occurrences
    name_counts = Counter(unmatched_names)
    unique_names = sorted(name_counts.keys())
    
    print(f"📊 Found {len(unique_names)} unique unmatched names")
    print(f"📊 Total occurrences: {len(unmatched_names)}")
    print()
    
    # Connect to database
    print("🔌 Connecting to database...")
    conn = get_conn()
    db_players = get_all_players(conn)
    conn.close()
    print(f"✅ Loaded {len(db_players)} players from database")
    print()
    
    # Find matches
    print("=" * 70)
    print("Suggested Overrides (copy to config/player_odds_config.py)")
    print("=" * 70)
    print()
    print("PLAYER_NAME_OVERRIDES = {")
    print("    # Existing overrides...")
    print()
    
    high_confidence = []
    medium_confidence = []
    low_confidence = []
    no_match = []
    
    for api_name in unique_names:
        count = name_counts[api_name]
        matched_name, score = find_best_match(api_name, db_players)
        
        entry = {
            'api_name': api_name,
            'db_name': matched_name,
            'score': score,
            'count': count
        }
        
        if score >= 90:
            high_confidence.append(entry)
        elif score >= 75:
            medium_confidence.append(entry)
        elif score >= 60:
            low_confidence.append(entry)
        else:
            no_match.append(entry)
    
    # Print high confidence (auto-add these)
    if high_confidence:
        print("    # High confidence matches (>90% - safe to add)")
        for entry in high_confidence:
            print(f"    '{entry['api_name']}': '{entry['db_name']}',  # Score: {entry['score']}, Count: {entry['count']}")
        print()
    
    # Print medium confidence (review these)
    if medium_confidence:
        print("    # Medium confidence matches (75-90% - review before adding)")
        for entry in medium_confidence:
            print(f"    # '{entry['api_name']}': '{entry['db_name']}',  # Score: {entry['score']}, Count: {entry['count']}")
        print()
    
    # Print low confidence (probably wrong)
    if low_confidence:
        print("    # Low confidence matches (60-75% - probably incorrect)")
        for entry in low_confidence:
            print(f"    # '{entry['api_name']}': '{entry['db_name']}',  # Score: {entry['score']}, Count: {entry['count']}")
        print()
    
    print("}")
    print()
    
    # Print no matches for manual investigation
    if no_match:
        print("=" * 70)
        print("⚠️  No good matches found - Manual investigation needed:")
        print("=" * 70)
        print()
        for entry in no_match:
            print(f"'{entry['api_name']}' - Occurred {entry['count']} times")
            print(f"  Best match: '{entry['db_name']}' (score: {entry['score']})")
            print(f"  → Check if this is a nickname, abbreviation, or team defense")
            print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"High confidence: {len(high_confidence)} (safe to add)")
    print(f"Medium confidence: {len(medium_confidence)} (review first)")
    print(f"Low confidence: {len(low_confidence)} (skip these)")
    print(f"No match: {len(no_match)} (investigate manually)")
    print()
    print("💡 Recommendation:")
    print("   1. Add all high confidence matches")
    print("   2. Review medium confidence matches manually")
    print("   3. Skip low confidence matches")
    print("   4. Check database for no match entries:")
    print()
    for entry in no_match[:5]:  # Show first 5
        print(f"      SELECT * FROM player WHERE full_name ILIKE '%{entry['api_name'].split()[0]}%';")
    print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_overrides.py <log_file>")
        print()
        print("Example:")
        print("  python nfl_player_odds_etl.py --season 2023 --debug 2>&1 | tee week1_run.log")
        print("  python generate_overrides.py week1_run.log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    if not os.path.exists(log_file):
        print(f"❌ Error: Log file '{log_file}' not found")
        sys.exit(1)
    
    try:
        generate_overrides(log_file)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
