#!/usr/bin/env python3
"""
ETL Verification & Testing Script
==================================
Quick verification script to test the ETL components without running full ingestion.
"""

import os
import sys
import psycopg2
from nfl_player_etl import (
    ETLConfig,
    SportsAPIClient,
    PlayerDataTransformer,
    setup_logging,
    get_conn
)


def test_api_connection(config: ETLConfig):
    """Test API connectivity and data retrieval"""
    logger = setup_logging(config)
    client = SportsAPIClient(config.api_key, logger, config.api_delay)
    
    print("\n" + "="*70)
    print("Testing API Connection")
    print("="*70)
    
    # Test 1: Fetch a single player by ID
    print("\n1. Fetching single player (ID=1)...")
    player = client.get_player_by_id(1)
    
    if player:
        print("✅ Successfully retrieved player:")
        print(f"   Name: {player.get('name')}")
        print(f"   Position: {player.get('position')}")
        print(f"   Team: {player.get('team', {}).get('name', 'N/A')}")
    else:
        print("❌ Failed to retrieve player")
        return False
    
    # Test 2: Fetch players for season (limit to first request)
    print(f"\n2. Testing season endpoint (Season {config.season})...")
    players = client.get_players_by_season(config.season)
    
    if players:
        print(f"✅ Successfully retrieved {len(players)} players")
        if len(players) > 0:
            print(f"   First player: {players[0].get('name')} ({players[0].get('position')})")
    else:
        print("⚠️  No players retrieved (API may not have data for this season)")
    
    return True


def test_database_connection(config: ETLConfig):
    """Test database connectivity and schema"""
    logger = setup_logging(config)
    
    print("\n" + "="*70)
    print("Testing Database Connection")
    print("="*70)
    
    try:
        # Test connection
        print("\n1. Connecting to database...")
        conn = get_conn()
        cursor = conn.cursor()
        print("✅ Database connection successful")
        
        # Test player table exists
        print("\n2. Checking player table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'player'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ Player table exists")
        else:
            print("❌ Player table does not exist")
            return False
        
        # Test team table for foreign key
        print("\n3. Checking team table...")
        cursor.execute("""
            SELECT COUNT(*) FROM team;
        """)
        team_count = cursor.fetchone()[0]
        print(f"✅ Team table has {team_count} teams")
        
        # Test player table columns
        print("\n4. Checking player table schema...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'player'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"✅ Player table has {len(columns)} columns:")
        for col_name, col_type in columns:
            print(f"   - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False


def test_data_transformation():
    """Test data transformation logic"""
    print("\n" + "="*70)
    print("Testing Data Transformation")
    print("="*70)
    
    # Mock API player data
    api_player = {
        "id": 1,
        "name": "Patrick Mahomes",
        "age": 28,
        "height": "6' 3\"",
        "weight": "230 lbs",
        "college": "Texas Tech",
        "group": "Offense",
        "position": "QB",
        "number": 15,
        "salary": "$45,000,000",
        "experience": 7,
        "image": "https://media.api-sports.io/american-football/players/1.png"
    }
    
    # Create a minimal logger
    import logging
    logger = logging.getLogger('test')
    logger.addHandler(logging.NullHandler())
    
    transformer = PlayerDataTransformer(logger)
    
    print("\n1. Transforming sample player data...")
    transformed = transformer.transform_player(api_player, team_id=1)
    
    print("✅ Transformation successful:")
    print(f"   External ID: {transformed['external_player_id']}")
    print(f"   Name: {transformed['full_name']}")
    print(f"   Position: {transformed['position']}")
    print(f"   Team ID: {transformed['team_id']}")
    print(f"   Jersey: #{transformed['jersey_number']}")
    print(f"   College: {transformed['college']}")
    print(f"   Experience: {transformed['experience_years']} years")
    
    return True


def test_environment():
    """Test environment configuration"""
    print("\n" + "="*70)
    print("Testing Environment Configuration")
    print("="*70)
    
    required_vars = ['SPORTS_API_KEY', 'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    optional_vars = ['PGPORT', 'ETL_BATCH_SIZE', 'API_DELAY', 'LOG_LEVEL']
    
    print("\n1. Checking required environment variables...")
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_required.append(var)
    
    print("\n2. Checking optional environment variables...")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ℹ️  {var}: Using default")
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        return False
    
    print("\n✅ All required environment variables are set")
    return True


def run_all_tests(season: int = 2023):
    """Run all verification tests"""
    print("\n" + "="*70)
    print("NFL PLAYER ETL VERIFICATION")
    print("="*70)
    
    results = {}
    
    # Test 1: Environment
    results['environment'] = test_environment()
    
    if not results['environment']:
        print("\n⚠️  Skipping remaining tests due to missing configuration")
        return results
    
    # Create config
    config = ETLConfig.from_env(season)
    
    # Test 2: Database
    results['database'] = test_database_connection(config)
    
    # Test 3: API
    results['api'] = test_api_connection(config)
    
    # Test 4: Transformation
    results['transformation'] = test_data_transformation()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✅ All tests passed! ETL is ready to run.")
        print(f"\nTo run the ETL for season {season}:")
        print(f"   python nfl_player_etl.py --season {season}")
        return True
    else:
        print("\n❌ Some tests failed. Please fix the issues before running ETL.")
        return False


def main():
    """CLI for verification script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify NFL Player ETL Setup')
    parser.add_argument('--season', type=int, default=2023, help='Season to test (default: 2023)')
    parser.add_argument('--test', choices=['env', 'db', 'api', 'transform', 'all'], 
                       default='all', help='Specific test to run')
    
    args = parser.parse_args()
    
    if args.test == 'all':
        success = run_all_tests(args.season)
    else:
        config = ETLConfig.from_env(args.season)
        
        if args.test == 'env':
            success = test_environment()
        elif args.test == 'db':
            success = test_database_connection(config)
        elif args.test == 'api':
            success = test_api_connection(config)
        elif args.test == 'transform':
            success = test_data_transformation()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
