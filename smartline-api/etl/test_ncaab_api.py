#!/usr/bin/env python3
"""
Test script to check if NCAAB is available in basketball API
"""

import os
import requests
import json

def test_basketball_api():
    """Test basketball API endpoints to find NCAAB"""
    
    # Get API key from environment
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("ERROR: API_SPORTS_KEY environment variable not set")
        return
    
    print("=" * 70)
    print("Testing Basketball API for NCAAB")
    print("=" * 70)
    print()
    
    # Test different basketball API endpoints
    apis_to_test = [
        {
            'name': 'Basketball v1 (American)',
            'url': 'https://v1.basketball.api-sports.io/leagues',
            'headers': {'x-apisports-key': api_key}
        },
        {
            'name': 'NBA API v2',
            'url': 'https://v2.nba.api-sports.io/leagues',
            'headers': {'x-apisports-key': api_key}
        }
    ]
    
    for api in apis_to_test:
        print(f"\n{'='*70}")
        print(f"Testing: {api['name']}")
        print(f"URL: {api['url']}")
        print('='*70)
        
        try:
            response = requests.get(api['url'], headers=api['headers'], timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Print basic info
                print(f"Results: {data.get('results', 0)}")
                print()
                
                # Look for NCAAB or college basketball
                if 'response' in data and data['response']:
                    print("Searching for NCAAB/College Basketball leagues:")
                    print()
                    
                    ncaab_found = False
                    college_leagues = []
                    
                    for league in data['response']:
                        league_name = league.get('name', '').lower()
                        league_type = league.get('type', '').lower()
                        league_id = league.get('id')
                        
                        # Check if it's college/NCAA related
                        if any(keyword in league_name for keyword in ['ncaa', 'college', 'university', 'amateur']):
                            college_leagues.append({
                                'id': league_id,
                                'name': league.get('name'),
                                'type': league.get('type'),
                                'country': league.get('country', {}).get('name') if isinstance(league.get('country'), dict) else league.get('country')
                            })
                            
                            if 'ncaa' in league_name:
                                ncaab_found = True
                    
                    if college_leagues:
                        print(f"Found {len(college_leagues)} college/NCAA leagues:")
                        for lg in college_leagues:
                            print(f"  - ID: {lg['id']}")
                            print(f"    Name: {lg['name']}")
                            print(f"    Type: {lg['type']}")
                            print(f"    Country: {lg['country']}")
                            print()
                    else:
                        print("No college/NCAA leagues found in this API")
                        print()
                        print("Sample leagues available:")
                        for i, league in enumerate(data['response'][:10], 1):
                            print(f"  {i}. {league.get('name')} (ID: {league.get('id')})")
                    
                    if ncaab_found:
                        print("\n✅ NCAAB FOUND in this API!")
                    else:
                        print("\n❌ NCAAB NOT found in this API")
                
                else:
                    print("No leagues data in response")
                    print(f"Response: {json.dumps(data, indent=2)[:500]}")
            
            else:
                print(f"Error response: {response.text[:500]}")
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\n" + "="*70)
    print("Testing Complete")
    print("="*70)
    print()
    print("SUMMARY:")
    print("If NCAAB was found, note the:")
    print("  - API URL")
    print("  - League ID")
    print("  - League name")
    print()
    print("Then update SPORT_CONFIG in team_etl.py accordingly.")
    print()

if __name__ == '__main__':
    test_basketball_api()
