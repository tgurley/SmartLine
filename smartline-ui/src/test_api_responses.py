#!/usr/bin/env python3
"""
Test script to fetch actual API responses for player 1349
This will help us understand the exact structure of the data
"""

import requests
import json

BASE_URL = "https://smartline-production.up.railway.app"
PLAYER_ID = 1349
SEASON = 2023

def test_endpoint(name, url):
    """Test an endpoint and print the response"""
    print(f"\n{'='*80}")
    print(f"ENDPOINT: {name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nJSON Response:")
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"Error Response:")
            print(response.text)
    except Exception as e:
        print(f"Exception: {e}")
    
    print(f"\n{'='*80}\n")


# Test all relevant endpoints
print("TESTING API ENDPOINTS FOR PLAYER 1349")
print("="*80)

# 1. Player Details
test_endpoint(
    "Player Details",
    f"{BASE_URL}/players/{PLAYER_ID}"
)

# 2. Player Game Log
test_endpoint(
    "Player Game Log (Passing)",
    f"{BASE_URL}/statistics/players/{PLAYER_ID}/games?season={SEASON}&stat_group=Passing&limit=10"
)

# 3. Player Game Log (All stats)
test_endpoint(
    "Player Game Log (All Groups)",
    f"{BASE_URL}/statistics/players/{PLAYER_ID}/games?season={SEASON}&limit=10"
)

# # 4. Statistical Leaders - Passing Yards
# test_endpoint(
#     "Leaders - Passing Yards",
#     f"{BASE_URL}/statistics/players/leaders/Passing/yards?season={SEASON}&limit=10"
# )

# # 5. Statistical Leaders - Passing Touchdowns
# test_endpoint(
#     "Leaders - Passing Touchdowns",
#     f"{BASE_URL}/statistics/players/leaders/Passing/passing touch downs?season={SEASON}&limit=10"
# )

# # 6. Statistical Leaders - Rating
# test_endpoint(
#     "Leaders - Passing Rating",
#     f"{BASE_URL}/statistics/players/leaders/Passing/rating?season={SEASON}&limit=10"
# )

# # 7. Player Summary
# test_endpoint(
#     "Player Summary",
#     f"{BASE_URL}/statistics/players/{PLAYER_ID}/summary?season={SEASON}"
# )

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
