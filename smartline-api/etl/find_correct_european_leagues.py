#!/usr/bin/env python3
"""
Improved search for European soccer leagues - find the correct ones
"""

import os
import requests
from dotenv import load_dotenv  # Add this import

load_dotenv()

def find_correct_european_leagues():
    """Find the actual Bundesliga, Serie A, Champions League (not women/youth)"""
    
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("ERROR: API_SPORTS_KEY environment variable not set")
        return
    
    print("=" * 70)
    print("Searching for CORRECT European Soccer Leagues")
    print("=" * 70)
    print()
    
    base_url = "https://v3.football.api-sports.io"
    headers = {'x-apisports-key': api_key}
    
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('response'):
                leagues = data['response']
                
                print("Searching through all leagues...")
                print()
                
                # More specific search
                bundesliga_options = []
                serie_a_options = []
                champions_options = []
                
                for league_data in leagues:
                    league = league_data.get('league', {})
                    country = league_data.get('country', {})
                    
                    league_name = league.get('name', '')
                    league_id = league.get('id')
                    league_type = league.get('type')
                    country_name = country.get('name') if isinstance(country, dict) else country
                    
                    # Bundesliga - must be Germany, must say "Bundesliga", NOT U19/U17/Women
                    if country_name == 'Germany' and 'bundesliga' in league_name.lower():
                        if not any(x in league_name.lower() for x in ['u19', 'u17', 'women', 'u23', 'youth', '2', '3']):
                            bundesliga_options.append({
                                'id': league_id,
                                'name': league_name,
                                'type': league_type
                            })
                    
                    # Serie A - must be Italy, NOT women/youth/Serie B/C
                    if country_name == 'Italy' and 'serie a' in league_name.lower():
                        if not any(x in league_name.lower() for x in ['women', 'serie b', 'serie c', 'youth', 'primavera', 'cup']):
                            serie_a_options.append({
                                'id': league_id,
                                'name': league_name,
                                'type': league_type
                            })
                    
                    # Champions League - must be UEFA, must be Champions League, NOT women
                    if 'uefa' in league_name.lower() and 'champions' in league_name.lower():
                        if not any(x in league_name.lower() for x in ['women', 'youth', 'u19']):
                            champions_options.append({
                                'id': league_id,
                                'name': league_name,
                                'type': league_type
                            })
                
                # Display options
                print("=" * 70)
                print("BUNDESLIGA OPTIONS:")
                print("=" * 70)
                for i, opt in enumerate(bundesliga_options, 1):
                    print(f"{i}. ID: {opt['id']} - {opt['name']} ({opt['type']})")
                print()
                
                print("=" * 70)
                print("SERIE A OPTIONS:")
                print("=" * 70)
                for i, opt in enumerate(serie_a_options, 1):
                    print(f"{i}. ID: {opt['id']} - {opt['name']} ({opt['type']})")
                print()
                
                print("=" * 70)
                print("CHAMPIONS LEAGUE OPTIONS:")
                print("=" * 70)
                for i, opt in enumerate(champions_options, 1):
                    print(f"{i}. ID: {opt['id']} - {opt['name']} ({opt['type']})")
                print()
                
                # Test the most likely candidates
                print("=" * 70)
                print("TESTING TOP CANDIDATES WITH SEASON 2024:")
                print("=" * 70)
                print()
                
                # Test first Bundesliga option
                if bundesliga_options:
                    test_league("Bundesliga", bundesliga_options[0]['id'], base_url, headers)
                
                # Test first Serie A option
                if serie_a_options:
                    test_league("Serie A", serie_a_options[0]['id'], base_url, headers)
                
                # Ligue 1 we already know: ID 61
                test_league("Ligue 1", 61, base_url, headers)
                
                # Test first Champions League option
                if champions_options:
                    test_league("Champions League", champions_options[0]['id'], base_url, headers)
                
        else:
            print(f"Error: {response.status_code}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

def test_league(name, league_id, base_url, headers):
    """Test a league to see team count"""
    print(f"Testing {name} (ID: {league_id})...")
    
    params = {
        'league': league_id,
        'season': 2024
    }
    
    try:
        response = requests.get(f"{base_url}/teams", headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('response'):
                teams = data['response']
                team_count = len(teams)
                print(f"  ✅ {team_count} teams found")
                
                if team_count > 0:
                    print(f"  Sample teams:")
                    for i, team_info in enumerate(teams[:5], 1):
                        team = team_info.get('team', {})
                        print(f"    {i}. {team.get('name')}")
                
                # Check if these look like the right teams
                if team_count in [18, 19, 20]:  # Expected for top leagues
                    print(f"  ✅ Team count looks right for top league!")
                elif team_count > 30:
                    print(f"  ⚠️  Too many teams - might be wrong league")
            else:
                print(f"  ❌ No teams found")
        else:
            print(f"  ❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()

if __name__ == '__main__':
    find_correct_european_leagues()
