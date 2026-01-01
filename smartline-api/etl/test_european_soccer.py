#!/usr/bin/env python3
"""
Test script to find European soccer league IDs
"""

import os
import requests
import json
from dotenv import load_dotenv  # Add this import

load_dotenv()

def test_european_soccer_leagues():
    """Test to find Bundesliga, Serie A, Ligue 1, Champions League"""
    
    # Get API key from environment
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("ERROR: API_SPORTS_KEY environment variable not set")
        return
    
    print("=" * 70)
    print("Testing European Soccer Leagues")
    print("=" * 70)
    print()
    
    base_url = "https://v3.football.api-sports.io"
    headers = {'x-apisports-key': api_key}
    
    # Get all leagues
    print("Fetching all soccer leagues...")
    print()
    
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('response'):
                leagues = data['response']
                
                # Search for target leagues
                targets = {
                    'Bundesliga': None,
                    'Serie A': None,
                    'Ligue 1': None,
                    'UEFA Champions League': None
                }
                
                for league_data in leagues:
                    league = league_data.get('league', {})
                    country = league_data.get('country', {})
                    
                    league_name = league.get('name', '')
                    league_id = league.get('id')
                    league_type = league.get('type')
                    country_name = country.get('name') if isinstance(country, dict) else country
                    
                    # Check for Bundesliga (Germany)
                    if 'bundesliga' in league_name.lower() and country_name == 'Germany':
                        if '2' not in league_name:  # Skip Bundesliga 2
                            targets['Bundesliga'] = {
                                'id': league_id,
                                'name': league_name,
                                'country': country_name,
                                'type': league_type
                            }
                    
                    # Check for Serie A (Italy)
                    if 'serie a' in league_name.lower() and country_name == 'Italy':
                        if 'serie b' not in league_name.lower():  # Skip Serie B
                            targets['Serie A'] = {
                                'id': league_id,
                                'name': league_name,
                                'country': country_name,
                                'type': league_type
                            }
                    
                    # Check for Ligue 1 (France)
                    if 'ligue 1' in league_name.lower() and country_name == 'France':
                        if 'ligue 2' not in league_name.lower():  # Skip Ligue 2
                            targets['Ligue 1'] = {
                                'id': league_id,
                                'name': league_name,
                                'country': country_name,
                                'type': league_type
                            }
                    
                    # Check for Champions League
                    if 'champions league' in league_name.lower() and 'uefa' in league_name.lower():
                        targets['UEFA Champions League'] = {
                            'id': league_id,
                            'name': league_name,
                            'country': country_name,
                            'type': league_type
                        }
                
                # Print results
                print("=" * 70)
                print("FOUND LEAGUES:")
                print("=" * 70)
                print()
                
                for target_name, info in targets.items():
                    if info:
                        print(f"✅ {target_name}")
                        print(f"   ID: {info['id']}")
                        print(f"   Name: {info['name']}")
                        print(f"   Country: {info['country']}")
                        print(f"   Type: {info['type']}")
                        print()
                    else:
                        print(f"❌ {target_name} - NOT FOUND")
                        print()
                
                # Now test team counts for found leagues with season 2024
                print("=" * 70)
                print("TESTING TEAM COUNTS (Season 2024):")
                print("=" * 70)
                print()
                
                for target_name, info in targets.items():
                    if info:
                        print(f"Testing {target_name} (ID: {info['id']})...")
                        
                        params = {
                            'league': info['id'],
                            'season': 2024
                        }
                        
                        try:
                            team_response = requests.get(f"{base_url}/teams", headers=headers, params=params, timeout=10)
                            
                            if team_response.status_code == 200:
                                team_data = team_response.json()
                                
                                if team_data.get('response'):
                                    team_count = len(team_data['response'])
                                    print(f"  ✅ {team_count} teams found")
                                    
                                    # Show sample teams
                                    if team_count > 0:
                                        print(f"  Sample teams:")
                                        for i, team_info in enumerate(team_data['response'][:5], 1):
                                            team = team_info.get('team', {})
                                            print(f"    {i}. {team.get('name')}")
                                else:
                                    print(f"  ❌ No teams found")
                            else:
                                print(f"  ❌ API error: {team_response.status_code}")
                        
                        except Exception as e:
                            print(f"  ❌ Error: {str(e)}")
                        
                        print()
                
                print("=" * 70)
                print("SUMMARY - Add to team_etl.py SPORT_CONFIG:")
                print("=" * 70)
                print()
                
                for target_name, info in targets.items():
                    if info:
                        sport_code = {
                            'Bundesliga': 'BUNDESLIGA',
                            'Serie A': 'SERIE_A',
                            'Ligue 1': 'LIGUE_1',
                            'UEFA Champions League': 'CHAMPIONS'
                        }.get(target_name)
                        
                        print(f"'{sport_code}': {{")
                        print(f"    'sport_code': '{sport_code}',")
                        print(f"    'api_url': 'https://v3.football.api-sports.io',")
                        print(f"    'default_league_id': {info['id']},")
                        print(f"    'league_param': 'league',")
                        print(f"    'has_extensions': False,")
                        print(f"    'extension_table': 'soccer_team_data'")
                        print(f"}},")
                        print()
            
            else:
                print("No leagues data in response")
        
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    test_european_soccer_leagues()
