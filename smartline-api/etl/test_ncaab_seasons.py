#!/usr/bin/env python3
"""
Test script to check available NCAAB seasons
"""

import os
import requests

def test_ncaab_seasons():
    """Test different seasons to find which one has NCAAB data"""
    
    # Get API key from environment
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("ERROR: API_SPORTS_KEY environment variable not set")
        return
    
    print("=" * 70)
    print("Testing NCAAB Seasons")
    print("=" * 70)
    print()
    
    base_url = "https://v1.basketball.api-sports.io"
    headers = {'x-apisports-key': api_key}
    
    # Test seasons from 2024 back to 2020
    seasons_to_test = [2024, 2023, 2022, 2021, 2020, '2024-2025', '2023-2024']
    
    for season in seasons_to_test:
        print(f"\nTesting season: {season}")
        print("-" * 70)
        
        params = {
            'league': 116,  # NCAA
            'season': season
        }
        
        try:
            response = requests.get(f"{base_url}/teams", headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('errors') and len(data['errors']) > 0:
                    print(f"  ❌ Errors: {data['errors']}")
                elif data.get('response'):
                    team_count = len(data['response'])
                    print(f"  ✅ SUCCESS! Found {team_count} teams")
                    
                    if team_count > 0:
                        # Show sample teams
                        print(f"\n  Sample teams:")
                        for i, team in enumerate(data['response'][:5], 1):
                            print(f"    {i}. {team.get('name')} (ID: {team.get('id')})")
                        
                        print(f"\n  🎯 USE SEASON: {season}")
                        return season
                else:
                    print(f"  ❌ No teams found")
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("No working season found!")
    print("=" * 70)
    print()
    print("Try checking the API documentation for NCAAB season format.")
    print()

if __name__ == '__main__':
    test_ncaab_seasons()
