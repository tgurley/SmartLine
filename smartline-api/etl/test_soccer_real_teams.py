#!/usr/bin/env python3
"""
Soccer API Test with Real Team IDs
===================================
Uses actual team IDs from your database to test the Soccer API
"""

import os
import sys
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_sample_soccer_teams():
    """Get sample team IDs from database"""
    try:
        conn = psycopg2.connect(
            host=os.environ["PGHOST"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            port=os.environ.get("PGPORT", 5432)
        )
        cursor = conn.cursor()
        
        # Get 3 sample teams from MLS with their external team keys
        cursor.execute("""
            SELECT t.team_id, t.external_team_key, t.name, t.abbrev
            FROM team t
            JOIN league l ON t.league_id = l.league_id
            WHERE l.league_code = 'mls'
            LIMIT 3
        """)
        
        teams = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return teams
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def test_soccer_api_with_real_teams():
    """Test Soccer API with actual team IDs from database"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found")
        return
    
    print("="*70)
    print("SOCCER API TEST WITH REAL TEAM IDs")
    print("="*70)
    
    teams = get_sample_soccer_teams()
    
    if not teams:
        print("❌ No teams found in database")
        return
    
    print(f"\n✅ Found {len(teams)} MLS teams in database\n")
    
    base_url = 'https://v3.football.api-sports.io'
    headers = {'x-apisports-key': api_key}
    
    for team_id, external_key, name, abbrev in teams:
        print("="*70)
        print(f"🔍 Testing: {name} ({abbrev})")
        print(f"   DB team_id: {team_id}")
        print(f"   External key: {external_key}")
        print("="*70)
        
        # Test 1: /players endpoint with team and season
        print("\n📋 TEST: /players?team={external_key}&season=2024")
        endpoint = '/players'
        params = {
            'team': external_key,
            'season': 2024
        }
        
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', 0)
            print(f"   Results: {results}")
            
            if results > 0:
                # Show first player structure
                player = data['response'][0]
                print(f"\n   ✅ FOUND PLAYERS! Sample structure:")
                print(json.dumps(player, indent=4, ensure_ascii=False)[:1000])
                print("   ...")
                
                # Check if position exists
                if 'player' in player:
                    pos = player['player'].get('position')
                    print(f"\n   Position field: {pos}")
                if 'statistics' in player:
                    print(f"   Has statistics: Yes ({len(player['statistics'])} entries)")
                    if len(player['statistics']) > 0:
                        stat_pos = player['statistics'][0].get('games', {}).get('position')
                        print(f"   Position in stats: {stat_pos}")
            else:
                print(f"   ⚠️  No results returned")
                print(f"   Response: {json.dumps(data, indent=4)[:500]}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "-"*70 + "\n")
        
        # Small delay between requests
        import time
        time.sleep(1.5)
    
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == '__main__':
    test_soccer_api_with_real_teams()
