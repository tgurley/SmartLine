#!/usr/bin/env python3
"""
Soccer API Response Structure Test
===================================
Tests the actual API response for soccer players to determine 
how to properly extract position data.

Usage:
    python test_soccer_api_structure.py
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_soccer_player_api():
    """Test Soccer API to see actual response structure"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ API_SPORTS_KEY not found in environment")
        return
    
    base_url = 'https://v3.football.api-sports.io'
    headers = {'x-apisports-key': api_key}
    
    print("="*70)
    print("SOCCER API RESPONSE STRUCTURE TEST")
    print("="*70)
    
    # Test 1: Get players for a specific team
    print("\n📋 TEST 1: Get players for a specific MLS team")
    print("-" * 70)
    
    # Inter Miami (team_id from your database - external_team_key should work)
    # Let's try team 1478 (Inter Miami) with season 2024
    team_id = 1478  # Inter Miami
    season = 2024
    
    endpoint = '/players'
    params = {
        'team': team_id,
        'season': season
    }
    
    print(f"Endpoint: {base_url}{endpoint}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ API Response received")
        print(f"Status: {response.status_code}")
        print(f"Results: {data.get('results', 0)}")
        print()
        
        if data.get('response') and len(data['response']) > 0:
            # Get first 3 players to examine structure
            sample_size = min(3, len(data['response']))
            print(f"📊 Examining {sample_size} sample players:")
            print("="*70)
            
            for i in range(sample_size):
                player = data['response'][i]
                print(f"\n🔍 PLAYER {i+1} - FULL STRUCTURE:")
                print(json.dumps(player, indent=2, ensure_ascii=False))
                print("-"*70)
                
                # Extract key fields
                print(f"\n📌 KEY FIELDS FOR PLAYER {i+1}:")
                
                # Check if 'player' key exists
                if 'player' in player:
                    player_info = player['player']
                    print(f"  Player Name: {player_info.get('name')}")
                    print(f"  Player ID: {player_info.get('id')}")
                    print(f"  Position: {player_info.get('position')}")
                    print(f"  Age: {player_info.get('age')}")
                    print(f"  Height: {player_info.get('height')}")
                    print(f"  Weight: {player_info.get('weight')}")
                    print(f"  Number: {player_info.get('number')}")
                
                # Check if 'statistics' key exists
                if 'statistics' in player:
                    stats = player['statistics']
                    print(f"\n  Statistics Array Length: {len(stats)}")
                    
                    if len(stats) > 0:
                        stat = stats[0]
                        print(f"  Statistics[0] Structure:")
                        print(f"    Team: {stat.get('team', {}).get('name')}")
                        
                        # Check for position in games
                        games = stat.get('games', {})
                        print(f"    Games: {json.dumps(games, indent=6)}")
                        
                        # Check for position directly in statistics
                        if 'position' in stat:
                            print(f"    Position (in stats): {stat.get('position')}")
                
                print("="*70)
        
        else:
            print("⚠️  No player data returned")
            print(f"Full response: {json.dumps(data, indent=2)}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")
        return
    
    # Test 2: Get a single player by ID (if we know a famous player ID)
    print("\n\n📋 TEST 2: Get single player by ID")
    print("-" * 70)
    
    # Try Messi's ID (276) if he's in the database
    player_id = 276
    endpoint = '/players/profiles'
    params = {'player': player_id}
    
    print(f"Endpoint: {base_url}{endpoint}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ API Response received")
        print(f"Status: {response.status_code}")
        print(f"Results: {data.get('results', 0)}")
        print()
        
        if data.get('response') and len(data['response']) > 0:
            player = data['response'][0]
            print(f"🔍 PLAYER PROFILE STRUCTURE:")
            print(json.dumps(player, indent=2, ensure_ascii=False))
            print()
            
            # Extract key fields
            if 'player' in player:
                player_info = player['player']
                print(f"\n📌 KEY FIELDS:")
                print(f"  Player Name: {player_info.get('name')}")
                print(f"  Player ID: {player_info.get('id')}")
                print(f"  Position: {player_info.get('position')}")
                print(f"  Age: {player_info.get('age')}")
                print(f"  Height: {player_info.get('height')}")
                print(f"  Weight: {player_info.get('weight')}")
        else:
            print("⚠️  No player data returned")
            print(f"Full response: {json.dumps(data, indent=2)}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\n💡 KEY FINDINGS:")
    print("Look at the JSON structure above to determine:")
    print("1. Where is the 'position' field located?")
    print("2. Is it in player.position?")
    print("3. Is it in statistics[0].games.position?")
    print("4. Is it in statistics[0].position?")
    print("5. What are the position values? (Goalkeeper, Defender, etc.)")


if __name__ == '__main__':
    test_soccer_player_api()
