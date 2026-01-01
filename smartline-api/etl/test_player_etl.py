#!/usr/bin/env python3
"""
Player ETL Test Script
======================
Validates the player ETL setup and configuration.
Tests API connectivity, database schema, and basic functionality.

Usage:
    python test_player_etl.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("\n" + "="*70)
    print("TEST 1: Environment Variables")
    print("="*70)
    
    required = ['API_SPORTS_KEY', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = []
    
    for var in required:
        if os.environ.get(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: MISSING")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Missing variables: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All environment variables configured!")
        return True

def test_database_connection():
    """Test database connectivity and schema"""
    print("\n" + "="*70)
    print("TEST 2: Database Connection & Schema")
    print("="*70)
    
    try:
        conn = psycopg2.connect(
            host=os.environ["PGHOST"],
            dbname=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            port=os.environ.get("PGPORT", 5432)
        )
        print("✅ Database connection successful!")
        
        cursor = conn.cursor()
        
        # Check player table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'player'
        """)
        if cursor.fetchone()[0] == 1:
            print("✅ player table exists")
        else:
            print("❌ player table NOT FOUND")
            return False
        
        # Check player table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'player'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print(f"✅ player table has {len(columns)} columns:")
        for col_name, col_type in columns[:5]:  # Show first 5
            print(f"   - {col_name}: {col_type}")
        print("   - ...")
        
        # Check sport_type table
        cursor.execute("SELECT sport_code, sport_id FROM sport_type ORDER BY sport_code")
        sports = cursor.fetchall()
        print(f"\n✅ Found {len(sports)} sports configured:")
        for sport_code, sport_id in sports:
            print(f"   - {sport_code} (ID: {sport_id})")
        
        # Check existing players
        cursor.execute("""
            SELECT 
                st.sport_code,
                COUNT(p.player_id) as player_count
            FROM sport_type st
            LEFT JOIN player p ON st.sport_id = p.sport_id
            GROUP BY st.sport_code
            ORDER BY player_count DESC
        """)
        player_counts = cursor.fetchall()
        print(f"\n✅ Current player counts by sport:")
        for sport_code, count in player_counts:
            if count > 0:
                print(f"   - {sport_code}: {count:,} players")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_api_configuration():
    """Test API configuration"""
    print("\n" + "="*70)
    print("TEST 3: API Configuration")
    print("="*70)
    
    from etl.player_etl import SPORT_CONFIG
    
    print("\nSupported Sports:")
    for sport, config in SPORT_CONFIG.items():
        has_endpoint = bool(config.get('api_url') and config.get('player_endpoint'))
        status = "✅ Ready" if has_endpoint else "⏸️  No Endpoint"
        print(f"  {status} {sport:12} - {config.get('api_url', 'N/A')[:50]}")
    
    return True

def test_import():
    """Test that player_etl.py can be imported"""
    print("\n" + "="*70)
    print("TEST 4: Module Import")
    print("="*70)
    
    try:
        import etl.player_etl as player_etl
        print("✅ player_etl.py imported successfully")
        
        # Check key classes exist
        assert hasattr(player_etl, 'PlayerETL')
        print("✅ PlayerETL class found")
        
        assert hasattr(player_etl, 'SportsAPIClient')
        print("✅ SportsAPIClient class found")
        
        assert hasattr(player_etl, 'PlayerDataTransformer')
        print("✅ PlayerDataTransformer class found")
        
        assert hasattr(player_etl, 'PlayerDatabaseLoader')
        print("✅ PlayerDatabaseLoader class found")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🏃 PLAYER ETL TEST SUITE ".center(70, "="))
    
    tests = [
        test_environment_variables,
        test_database_connection,
        test_api_configuration,
        test_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All {total} tests PASSED!")
        print("\n🚀 Player ETL is ready to use!")
        print("\nTry running:")
        print("  python player_etl.py --sport NFL --season 2024 --team-id 6")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed, {total - passed} failed")
        print("\n❌ Please fix issues before running ETL")
        return 1

if __name__ == '__main__':
    sys.exit(main())
