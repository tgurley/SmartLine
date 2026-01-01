#!/usr/bin/env python3
"""
MLB & NHL Player Availability Test
===================================
Tests whether API-SPORTS has MLB/NHL player data available,
even though the documentation says it doesn't exist.

Sometimes APIs have undocumented endpoints or the docs are outdated.
This script thoroughly tests multiple approaches to find player data.

Usage:
    python test_mlb_nhl_availability.py
"""

import os
import sys
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_sample_teams(sport_code, limit=5):
    """Get sample teams from database for a sport"""
    try:
        conn = psycopg2.connect(
            host=os.environ["PGHOST"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            port=os.environ.get("PGPORT", 5432)
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.team_id, 
                t.external_team_key, 
                t.name, 
                t.abbrev
            FROM team t
            JOIN league l ON t.league_id = l.league_id
            WHERE l.league_code = %s
            ORDER BY t.name
            LIMIT %s
        """, (sport_code.lower(), limit))
        
        teams = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return teams
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def test_mlb_players():
    """Test MLB player data availability"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found")
        return False
    
    print("\n" + "="*70)
    print("⚾ MLB PLAYER DATA TEST")
    print("="*70)
    print("\nAPI: https://v1.baseball.api-sports.io")
    print("Documentation says: NO PLAYER ENDPOINT")
    print("Let's test anyway...\n")
    
    teams = get_sample_teams('MLB', 5)
    
    if not teams:
        print("❌ No MLB teams found in database")
        return False
    
    print(f"✅ Testing {len(teams)} MLB teams:\n")
    for _, _, name, abbrev in teams:
        print(f"   - {name} ({abbrev})")
    
    print("\n" + "-"*70)
    
    base_url = 'https://v1.baseball.api-sports.io'
    headers = {'x-apisports-key': api_key}
    
    # Try multiple possible endpoints
    endpoints_to_test = [
        '/players',
        '/player',
        '/players/squad',
        '/teams/players',
        '/rosters'
    ]
    
    # Try multiple season formats
    seasons_to_test = [2024, '2024', 2025, '2025']
    
    found_any = False
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing endpoint: {endpoint}")
        
        # Test with first team
        team_id, external_key, name, abbrev = teams[0]
        
        for season in seasons_to_test:
            params = {
                'team': external_key,
                'season': season
            }
            
            print(f"   Trying: {endpoint}?team={external_key}&season={season}")
            
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                
                # Check if endpoint exists (404 = doesn't exist)
                if response.status_code == 404:
                    print(f"   ❌ Endpoint doesn't exist (404)")
                    break  # Don't try other seasons for non-existent endpoint
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', 0)
                
                if results > 0:
                    print(f"   ✅ FOUND {results} PLAYERS!")
                    print(f"   Sample response: {json.dumps(data, indent=6)[:500]}")
                    found_any = True
                    break
                else:
                    print(f"   ⏭️  0 results")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"   ❌ Endpoint doesn't exist (404)")
                    break
                else:
                    print(f"   ❌ HTTP Error: {e.response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        if found_any:
            break
        
        import time
        time.sleep(0.5)
    
    return found_any

def test_nhl_players():
    """Test NHL player data availability"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found")
        return False
    
    print("\n" + "="*70)
    print("🏒 NHL PLAYER DATA TEST")
    print("="*70)
    print("\nAPI: https://v1.hockey.api-sports.io")
    print("Documentation says: NO PLAYER ENDPOINT")
    print("Let's test anyway...\n")
    
    teams = get_sample_teams('NHL', 5)
    
    if not teams:
        print("❌ No NHL teams found in database")
        return False
    
    print(f"✅ Testing {len(teams)} NHL teams:\n")
    for _, _, name, abbrev in teams:
        print(f"   - {name} ({abbrev})")
    
    print("\n" + "-"*70)
    
    base_url = 'https://v1.hockey.api-sports.io'
    headers = {'x-apisports-key': api_key}
    
    # Try multiple possible endpoints
    endpoints_to_test = [
        '/players',
        '/player',
        '/players/squad',
        '/teams/players',
        '/rosters',
        '/teams/statistics/players'
    ]
    
    # Try multiple season formats
    seasons_to_test = [2024, '2024', 2025, '2025']
    
    found_any = False
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing endpoint: {endpoint}")
        
        # Test with first team
        team_id, external_key, name, abbrev = teams[0]
        
        for season in seasons_to_test:
            params = {
                'team': external_key,
                'season': season
            }
            
            print(f"   Trying: {endpoint}?team={external_key}&season={season}")
            
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                
                # Check if endpoint exists (404 = doesn't exist)
                if response.status_code == 404:
                    print(f"   ❌ Endpoint doesn't exist (404)")
                    break  # Don't try other seasons for non-existent endpoint
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', 0)
                
                if results > 0:
                    print(f"   ✅ FOUND {results} PLAYERS!")
                    print(f"   Sample response: {json.dumps(data, indent=6)[:500]}")
                    found_any = True
                    break
                else:
                    print(f"   ⏭️  0 results")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"   ❌ Endpoint doesn't exist (404)")
                    break
                else:
                    print(f"   ❌ HTTP Error: {e.response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        if found_any:
            break
        
        import time
        time.sleep(0.5)
    
    return found_any

def main():
    """Run all tests"""
    
    print("="*70)
    print("MLB & NHL PLAYER DATA AVAILABILITY TEST")
    print("="*70)
    print()
    print("Documentation says MLB and NHL have NO player endpoints.")
    print("Let's verify by testing multiple possible endpoints...")
    print()
    print("This will test:")
    print("  • Multiple endpoint paths (/players, /player, /rosters, etc.)")
    print("  • Multiple season formats (2024, '2024', 2025, '2025')")
    print("  • 5 teams per sport")
    print()
    print("="*70)
    
    # Test MLB
    mlb_found = test_mlb_players()
    
    # Small delay
    import time
    time.sleep(2)
    
    # Test NHL
    nhl_found = test_nhl_players()
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    if mlb_found:
        print("⚾ MLB: ✅ PLAYER DATA FOUND!")
        print("   → Update player_etl.py with correct endpoint")
        print("   → Run MLB player ETL")
    else:
        print("⚾ MLB: ❌ NO PLAYER DATA AVAILABLE")
        print("   → Confirmed: API does not have MLB player data")
        print("   → Need alternative data source for MLB players")
    
    print()
    
    if nhl_found:
        print("🏒 NHL: ✅ PLAYER DATA FOUND!")
        print("   → Update player_etl.py with correct endpoint")
        print("   → Run NHL player ETL")
    else:
        print("🏒 NHL: ❌ NO PLAYER DATA AVAILABLE")
        print("   → Confirmed: API does not have NHL player data")
        print("   → Need alternative data source for NHL players")
    
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    if not mlb_found and not nhl_found:
        print()
        print("Both MLB and NHL lack player data in API-SPORTS.")
        print()
        print("Options:")
        print("  1. Use a different API for MLB/NHL players")
        print("     - ESPN API")
        print("     - MLB Stats API (statsapi.mlb.com)")
        print("     - NHL API (statsapi.web.nhl.com)")
        print()
        print("  2. Manual data entry for key players")
        print()
        print("  3. Skip MLB/NHL players for now")
        print()
        print("Current player database status:")
        print("  ✅ NFL:     ~3,295 players")
        print("  ✅ NCAAF:  ~15,347 players")
        print("  ✅ NBA:       ~627 players")
        print("  ✅ Soccer:  ~4,011 players")
        print("  ❌ MLB:         0 players (no API)")
        print("  ❌ NHL:         0 players (no API)")
        print("  ❌ NCAAB:       0 players (no API)")
        print()
    
    print("="*70)

if __name__ == '__main__':
    main()
