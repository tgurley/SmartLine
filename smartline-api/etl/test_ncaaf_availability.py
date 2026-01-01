#!/usr/bin/env python3
"""
NCAAF Player Availability Test
===============================
Tests whether API-SPORTS has NCAAF player data available.

NCAAF is tricky because:
1. 706 teams in the database
2. ~50,000 potential players
3. API may not have all teams/players

This script tests a sample of teams to see what's available.

Usage:
    python test_ncaaf_availability.py
"""

import os
import sys
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_sample_ncaaf_teams():
    """Get sample NCAAF teams from database"""
    try:
        conn = psycopg2.connect(
            host=os.environ["PGHOST"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            port=os.environ.get("PGPORT", 5432)
        )
        cursor = conn.cursor()
        
        # Get 10 sample teams from different divisions
        # Focus on major teams (Alabama, Ohio State, etc.)
        cursor.execute("""
            SELECT 
                t.team_id, 
                t.external_team_key, 
                t.name, 
                t.abbrev,
                t.city
            FROM team t
            JOIN league l ON t.league_id = l.league_id
            WHERE l.league_code = 'ncaaf'
            ORDER BY 
                CASE 
                    WHEN t.name ILIKE '%Alabama%' THEN 1
                    WHEN t.name ILIKE '%Ohio State%' THEN 2
                    WHEN t.name ILIKE '%Georgia%' THEN 3
                    WHEN t.name ILIKE '%Michigan%' THEN 4
                    WHEN t.name ILIKE '%Texas%' THEN 5
                    WHEN t.name ILIKE '%USC%' THEN 6
                    WHEN t.name ILIKE '%Notre Dame%' THEN 7
                    ELSE 999
                END,
                t.name
            LIMIT 10
        """)
        
        teams = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return teams
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []

def test_ncaaf_player_availability():
    """Test NCAAF player data availability"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found")
        return
    
    print("="*70)
    print("NCAAF PLAYER DATA AVAILABILITY TEST")
    print("="*70)
    print()
    print("Testing whether API-SPORTS has NCAAF player data...")
    print("This will test 10 sample teams from your database.")
    print()
    
    teams = get_sample_ncaaf_teams()
    
    if not teams:
        print("❌ No NCAAF teams found in database")
        return
    
    print(f"✅ Found {len(teams)} NCAAF teams to test\n")
    print("="*70)
    
    base_url = 'https://v1.american-football.api-sports.io'
    headers = {'x-apisports-key': api_key}
    endpoint = '/players'
    
    results_summary = {
        'teams_tested': 0,
        'teams_with_players': 0,
        'teams_without_players': 0,
        'total_players_found': 0
    }
    
    for team_id, external_key, name, abbrev, city in teams:
        results_summary['teams_tested'] += 1
        
        print(f"\n🏈 Testing: {name} ({abbrev})")
        print(f"   City: {city}")
        print(f"   DB team_id: {team_id}")
        print(f"   External key: {external_key}")
        print("-" * 70)
        
        # Test with season 2024
        params = {
            'team': external_key,
            'season': 2024
        }
        
        print(f"   API Call: {endpoint}?team={external_key}&season=2024")
        
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
            
            if results > 0:
                print(f"   ✅ FOUND {results} PLAYERS!")
                results_summary['teams_with_players'] += 1
                results_summary['total_players_found'] += results
                
                # Show first player as sample
                player = data['response'][0]
                print(f"\n   📋 Sample Player:")
                print(f"      Name: {player.get('name')}")
                print(f"      Position: {player.get('position')}")
                print(f"      Number: {player.get('number')}")
                print(f"      Age: {player.get('age')}")
                print(f"      College: {player.get('college')}")
                
            else:
                print(f"   ⚠️  NO PLAYERS FOUND (0 results)")
                results_summary['teams_without_players'] += 1
                
                # Show the response to understand why
                print(f"   Response: {json.dumps(data, indent=6)[:300]}")
        
        except Exception as e:
            print(f"   ❌ API Error: {e}")
            results_summary['teams_without_players'] += 1
        
        # Small delay between requests
        import time
        time.sleep(1.2)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Teams Tested:        {results_summary['teams_tested']}")
    print(f"Teams WITH Players:  {results_summary['teams_with_players']}")
    print(f"Teams NO Players:    {results_summary['teams_without_players']}")
    print(f"Total Players Found: {results_summary['total_players_found']}")
    
    if results_summary['total_players_found'] > 0:
        avg_players = results_summary['total_players_found'] / results_summary['teams_with_players']
        print(f"Avg Players/Team:    {avg_players:.1f}")
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if results_summary['teams_with_players'] == 0:
        print("❌ NO NCAAF PLAYER DATA AVAILABLE")
        print("\nAPI-SPORTS does not appear to have NCAAF player data.")
        print("This is similar to NHL/MLB - the endpoint exists but returns no data.")
        print("\nRecommendation: Skip NCAAF player ETL for now.")
        
    elif results_summary['teams_with_players'] < results_summary['teams_tested'] / 2:
        print("⚠️  LIMITED NCAAF PLAYER DATA")
        print(f"\nOnly {results_summary['teams_with_players']}/{results_summary['teams_tested']} teams have player data.")
        print("Coverage appears incomplete.")
        print("\nRecommendation: May want to skip NCAAF or only load teams with data.")
        
    else:
        print("✅ NCAAF PLAYER DATA AVAILABLE!")
        print(f"\n{results_summary['teams_with_players']}/{results_summary['teams_tested']} teams have player data.")
        print(f"Total of {results_summary['total_players_found']} players found across sample.")
        
        if results_summary['teams_with_players'] == results_summary['teams_tested']:
            print("\n🎉 FULL COVERAGE! All tested teams have players.")
            print("\nRecommendation: Safe to run full NCAAF ETL.")
            print("Warning: This will be ~706 API calls for all teams.")
            print("         Expected ~50,000 players total.")
            print("         Will take 15-20 minutes to complete.")
        else:
            print("\nRecommendation: Safe to run NCAAF ETL with caveats.")
            print("Some teams may not have player data available.")
    
    print("="*70)

if __name__ == '__main__':
    test_ncaaf_player_availability()
