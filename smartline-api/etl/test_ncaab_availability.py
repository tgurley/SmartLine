#!/usr/bin/env python3
"""
NCAAB Player Availability Test
===============================
Tests whether API-SPORTS has NCAAB (NCAA Basketball) player data available.

NCAAB is tricky because:
1. 696 teams in the database
2. ~10,000 potential players
3. Different API (v1.basketball.api-sports.io) than NBA
4. Season format is "2024-2025" not just "2024"

This script tests a sample of teams to see what's available.

Usage:
    python test_ncaab_availability.py
"""

import os
import sys
import json
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_sample_ncaab_teams():
    """Get sample NCAAB teams from database"""
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
        # Focus on major basketball programs (Duke, UNC, Kansas, etc.)
        cursor.execute("""
            SELECT 
                t.team_id, 
                t.external_team_key, 
                t.name, 
                t.abbrev,
                t.city
            FROM team t
            JOIN league l ON t.league_id = l.league_id
            WHERE l.league_code = 'ncaab'
            ORDER BY 
                CASE 
                    WHEN t.name ILIKE '%Duke%' THEN 1
                    WHEN t.name ILIKE '%North Carolina%' THEN 2
                    WHEN t.name ILIKE '%Kansas%' THEN 3
                    WHEN t.name ILIKE '%Kentucky%' THEN 4
                    WHEN t.name ILIKE '%Gonzaga%' THEN 5
                    WHEN t.name ILIKE '%UCLA%' THEN 6
                    WHEN t.name ILIKE '%Villanova%' THEN 7
                    WHEN t.name ILIKE '%Michigan%' THEN 8
                    WHEN t.name ILIKE '%Connecticut%' THEN 9
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

def test_ncaab_player_availability():
    """Test NCAAB player data availability"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found")
        return
    
    print("="*70)
    print("NCAAB PLAYER DATA AVAILABILITY TEST")
    print("="*70)
    print()
    print("Testing whether API-SPORTS has NCAAB player data...")
    print("This will test 10 sample teams from your database.")
    print()
    print("⚠️  NOTE: NCAAB uses Basketball API (v1.basketball.api-sports.io)")
    print("         Different from NBA API (v2.nba.api-sports.io)")
    print()
    
    teams = get_sample_ncaab_teams()
    
    if not teams:
        print("❌ No NCAAB teams found in database")
        return
    
    print(f"✅ Found {len(teams)} NCAAB teams to test\n")
    print("="*70)
    
    base_url = 'https://v1.basketball.api-sports.io'
    headers = {'x-apisports-key': api_key}
    endpoint = '/players'
    
    results_summary = {
        'teams_tested': 0,
        'teams_with_players': 0,
        'teams_without_players': 0,
        'total_players_found': 0
    }
    
    # Test different season formats
    season_formats = ['2024-2025', '2024', 2025]
    
    for team_id, external_key, name, abbrev, city in teams:
        results_summary['teams_tested'] += 1
        
        print(f"\n🏀 Testing: {name} ({abbrev})")
        print(f"   City: {city or 'Unknown'}")
        print(f"   DB team_id: {team_id}")
        print(f"   External key: {external_key}")
        print("-" * 70)
        
        found_data = False
        
        # Try different season formats
        for season_format in season_formats:
            params = {
                'team': external_key,
                'season': season_format
            }
            
            print(f"   API Call: {endpoint}?team={external_key}&season={season_format}")
            
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
                    print(f"   ✅ FOUND {results} PLAYERS with season={season_format}!")
                    results_summary['teams_with_players'] += 1
                    results_summary['total_players_found'] += results
                    found_data = True
                    
                    # Show first player as sample
                    player = data['response'][0]
                    print(f"\n   📋 Sample Player:")
                    print(f"      ID: {player.get('id')}")
                    print(f"      Name: {player.get('firstname')} {player.get('lastname')}")
                    
                    # Check structure
                    if 'firstname' in player and 'lastname' in player:
                        print(f"      Structure: firstname/lastname (like NBA API)")
                    elif 'name' in player:
                        print(f"      Structure: name only")
                    
                    # Break after finding data
                    break
                else:
                    print(f"   ⏭️  No players with season={season_format}")
            
            except Exception as e:
                print(f"   ❌ API Error with season={season_format}: {e}")
        
        if not found_data:
            print(f"\n   ⚠️  NO PLAYERS FOUND with any season format")
            results_summary['teams_without_players'] += 1
        
        # Small delay between requests
        import time
        time.sleep(1.5)
    
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
        print("❌ NO NCAAB PLAYER DATA AVAILABLE")
        print("\nAPI-SPORTS does not appear to have NCAAB player data.")
        print("The Basketball API may only support professional leagues.")
        print("\nRecommendation: Skip NCAAB player ETL for now.")
        
    elif results_summary['teams_with_players'] < results_summary['teams_tested'] / 2:
        print("⚠️  LIMITED NCAAB PLAYER DATA")
        print(f"\nOnly {results_summary['teams_with_players']}/{results_summary['teams_tested']} teams have player data.")
        print("Coverage appears incomplete.")
        print("\nRecommendation: May want to skip NCAAB or only load teams with data.")
        
    else:
        print("✅ NCAAB PLAYER DATA AVAILABLE!")
        print(f"\n{results_summary['teams_with_players']}/{results_summary['teams_tested']} teams have player data.")
        print(f"Total of {results_summary['total_players_found']} players found across sample.")
        
        if results_summary['teams_with_players'] == results_summary['teams_tested']:
            print("\n🎉 FULL COVERAGE! All tested teams have players.")
            print("\nRecommendation: Safe to run full NCAAB ETL.")
            print("Warning: This will be ~696 API calls for all teams.")
            print("         Expected ~10,000 players total.")
            print("         Will take 12-15 minutes to complete.")
        else:
            print("\nRecommendation: Safe to run NCAAB ETL with caveats.")
            print("Some teams may not have player data available.")
    
    print("\n" + "="*70)
    print("NOTES:")
    print("="*70)
    print("• NCAAB uses Basketball API (v1.basketball.api-sports.io)")
    print("• Season format may need to be '2024-2025' not '2024'")
    print("• Player structure may be different from NBA API")
    print("• Check the ETL's _transform_basketball_player() method")
    print("="*70)

if __name__ == '__main__':
    test_ncaab_player_availability()
