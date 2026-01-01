#!/usr/bin/env python3
"""
Debug script to see what Champions League API returns
"""

import os
import requests
import json
from dotenv import load_dotenv  # Add this import

load_dotenv()

api_key = os.environ.get('API_SPORTS_KEY')
if not api_key:
    print("ERROR: API_SPORTS_KEY not set")
    exit(1)

base_url = "https://v3.football.api-sports.io"
headers = {'x-apisports-key': api_key}

params = {
    'league': 2,
    'season': '2024'
}

print("Fetching Champions League teams...")
print()

response = requests.get(f"{base_url}/teams", headers=headers, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    if data.get('response'):
        teams = data['response']
        print(f"Got {len(teams)} teams")
        print()
        
        # Show first team structure
        print("=" * 70)
        print("FIRST TEAM STRUCTURE:")
        print("=" * 70)
        print(json.dumps(teams[0], indent=2))
        print()
        
        # Check if 'team' key exists
        if 'team' in teams[0]:
            print("✅ Has 'team' key")
            print(f"Team name: {teams[0]['team'].get('name')}")
        else:
            print("❌ No 'team' key")
            if 'name' in teams[0]:
                print(f"Direct name: {teams[0].get('name')}")
        
        print()
        
        # Show a few team names
        print("=" * 70)
        print("SAMPLE TEAM NAMES:")
        print("=" * 70)
        for i, team_data in enumerate(teams[:10], 1):
            if 'team' in team_data:
                name = team_data['team'].get('name')
            else:
                name = team_data.get('name')
            print(f"{i}. {name}")
    
    else:
        print("No teams in response")
        print(data)

else:
    print(f"Error: {response.status_code}")
    print(response.text)
