#!/usr/bin/env python3
"""
Test script to verify parlay endpoints are available
Run this to check if the backend has the parlay routes
"""

import requests
import json

API_BASE = "https://smartline-production.up.railway.app"

def test_endpoint(method, endpoint, data=None):
    """Test an endpoint and return the result"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        status = response.status_code
        
        if status == 404:
            return f"❌ NOT FOUND - Endpoint doesn't exist"
        elif status == 500:
            return f"⚠️  SERVER ERROR - Endpoint exists but has issues"
        elif status == 400:
            return f"✅ EXISTS - Bad request (expected, endpoint is there)"
        elif status == 200:
            return f"✅ EXISTS - Working perfectly"
        else:
            return f"⚠️  Status {status} - Check manually"
            
    except requests.exceptions.Timeout:
        return "⏱️  TIMEOUT - Server not responding"
    except Exception as e:
        return f"❌ ERROR - {str(e)}"

print("=" * 60)
print("🔍 TESTING SMARTLINE PARLAY ENDPOINTS")
print("=" * 60)
print()

# Test 1: Check if bankroll endpoints exist
print("1️⃣  Testing Base Bankroll Endpoints...")
print("-" * 60)
result = test_endpoint("GET", "/bankroll/accounts?user_id=1")
print(f"   GET /bankroll/accounts: {result}")

result = test_endpoint("GET", "/bankroll/bets?user_id=1")
print(f"   GET /bankroll/bets: {result}")
print()

# Test 2: Check if parlay endpoints exist
print("2️⃣  Testing Parlay Endpoints...")
print("-" * 60)

# GET parlays
result = test_endpoint("GET", "/bankroll/parlays?user_id=1")
print(f"   GET /bankroll/parlays: {result}")

# GET single parlay (will fail but tells us if route exists)
result = test_endpoint("GET", "/bankroll/parlays/1")
print(f"   GET /bankroll/parlays/1: {result}")

# POST parlay (will fail without valid data but tells us if route exists)
test_data = {
    "account_id": 1,
    "stake_amount": 100,
    "legs": [
        {
            "bet_type": "player_prop",
            "sport": "NFL",
            "market_key": "player_pass_yds",
            "bet_side": "over",
            "line_value": 275.5,
            "odds_american": -110
        },
        {
            "bet_type": "player_prop",
            "sport": "NFL",
            "market_key": "player_rec_yds",
            "bet_side": "over",
            "line_value": 85.5,
            "odds_american": -110
        }
    ]
}
result = test_endpoint("POST", "/bankroll/parlays?user_id=1", test_data)
print(f"   POST /bankroll/parlays: {result}")
print()

# Test 3: Check if multi-sport analytics exist
print("3️⃣  Testing Multi-Sport Analytics Endpoints...")
print("-" * 60)

result = test_endpoint("GET", "/bankroll/analytics/by-sport?user_id=1&days=30")
print(f"   GET /analytics/by-sport: {result}")

result = test_endpoint("GET", "/bankroll/analytics/parlay-stats?user_id=1&days=30")
print(f"   GET /analytics/parlay-stats: {result}")
print()

# Summary
print("=" * 60)
print("📊 SUMMARY")
print("=" * 60)
print()
print("If you see ❌ NOT FOUND errors above, the parlay endpoints")
print("haven't been added to your backend yet.")
print()
print("Next steps:")
print("1. Add parlay_endpoints.py code to your backend")
print("2. Add multisport_analytics.py code to your backend")
print("3. Create the parlays table in your database")
print("4. Redeploy to Railway")
print()
print("Files needed:")
print("  - parlay_endpoints.py (add to bankroll_endpoints.py)")
print("  - Database migration (create parlays table)")
print()
