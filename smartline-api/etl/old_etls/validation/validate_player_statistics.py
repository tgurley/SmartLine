#!/usr/bin/env python3
"""
Player Statistics Validation Script
====================================
Automated validation of player_statistic table after ETL.

Features:
- Color-coded output (red/yellow/green)
- Pass/fail status for each check
- Detailed error reporting
- Summary statistics

Usage:
    python validate_player_statistics.py
    
    # Or with specific season
    python validate_player_statistics.py --season 2023

Environment Variables Required:
    PGHOST, PGDATABASE, PGUSER, PGPASSWORD
"""

import os
import sys
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_pass(text):
    """Print pass message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warn(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_fail(text):
    """Print fail message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432),
        cursor_factory=RealDictCursor
    )

def run_query(conn, query, params=None):
    """Execute query and return results"""
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()

def check_basic_stats(conn, season_year=None):
    """Check basic statistics"""
    print_header("1. BASIC STATISTICS")
    
    query = """
        SELECT 
            COUNT(*) as total_stats,
            COUNT(DISTINCT player_id) as unique_players,
            COUNT(DISTINCT team_id) as unique_teams,
            COUNT(DISTINCT season_id) as unique_seasons,
            COUNT(DISTINCT stat_group) as unique_stat_groups
        FROM player_statistic
    """
    
    if season_year:
        query += """
            WHERE season_id = (SELECT season_id FROM season WHERE year = %s)
        """
        results = run_query(conn, query, (season_year,))
    else:
        results = run_query(conn, query)
    
    stats = results[0]
    
    print(f"Total Statistics: {stats['total_stats']:,}")
    print(f"Unique Players: {stats['unique_players']:,}")
    print(f"Unique Teams: {stats['unique_teams']}")
    print(f"Unique Seasons: {stats['unique_seasons']}")
    print(f"Unique Stat Groups: {stats['unique_stat_groups']}")
    
    # Validation
    passed = True
    if stats['total_stats'] == 0:
        print_fail("No statistics loaded!")
        passed = False
    elif stats['total_stats'] < 50000:
        print_warn(f"Low record count ({stats['total_stats']:,}). Partial load?")
    else:
        print_pass(f"Record count looks good ({stats['total_stats']:,})")
    
    if stats['unique_stat_groups'] < 8:
        print_warn(f"Only {stats['unique_stat_groups']} stat groups found (expected 8)")
    else:
        print_pass(f"All {stats['unique_stat_groups']} stat groups present")
    
    return passed

def check_data_freshness(conn):
    """Check when data was last loaded"""
    print_header("2. DATA FRESHNESS")
    
    query = """
        SELECT 
            MIN(pulled_at_utc) as first_load,
            MAX(pulled_at_utc) as last_load,
            EXTRACT(EPOCH FROM (NOW() - MAX(pulled_at_utc)))/60 as minutes_ago
        FROM player_statistic
    """
    
    results = run_query(conn, query)
    if not results or not results[0]['last_load']:
        print_fail("No load timestamps found")
        return False
    
    data = results[0]
    print(f"First Load: {data['first_load']}")
    print(f"Last Load: {data['last_load']}")
    print(f"Minutes Since Last Load: {data['minutes_ago']:.1f}")
    
    if data['minutes_ago'] < 60:
        print_pass(f"Data is fresh (loaded {data['minutes_ago']:.0f} minutes ago)")
        return True
    elif data['minutes_ago'] < 1440:  # 24 hours
        print_warn(f"Data is {data['minutes_ago']/60:.1f} hours old")
        return True
    else:
        print_warn(f"Data is {data['minutes_ago']/1440:.1f} days old")
        return True

def check_stat_groups(conn):
    """Check stat group distribution"""
    print_header("3. STAT GROUPS BREAKDOWN")
    
    query = """
        SELECT 
            stat_group,
            COUNT(*) as stat_count,
            COUNT(DISTINCT player_id) as players
        FROM player_statistic
        GROUP BY stat_group
        ORDER BY stat_count DESC
    """
    
    results = run_query(conn, query)
    
    expected_groups = ['Passing', 'Rushing', 'Receiving', 'Defense', 
                      'Kicking', 'Punting', 'Returning', 'Scoring']
    
    found_groups = [r['stat_group'] for r in results]
    
    print(f"{'Stat Group':<15} {'Statistics':<12} {'Players'}")
    print("-" * 45)
    for row in results:
        print(f"{row['stat_group']:<15} {row['stat_count']:<12,} {row['players']:,}")
    
    missing = set(expected_groups) - set(found_groups)
    if missing:
        print_warn(f"Missing stat groups: {', '.join(missing)}")
        return False
    else:
        print_pass("All expected stat groups present")
        return True

def check_data_integrity(conn):
    """Check for data integrity issues"""
    print_header("4. DATA INTEGRITY CHECKS")
    
    checks = [
        ("Orphaned Players", """
            SELECT COUNT(*)
            FROM player_statistic ps
            LEFT JOIN player p ON ps.player_id = p.player_id
            WHERE p.player_id IS NULL
        """),
        ("Orphaned Teams", """
            SELECT COUNT(*)
            FROM player_statistic ps
            LEFT JOIN team t ON ps.team_id = t.team_id
            WHERE t.team_id IS NULL
        """),
        ("Invalid Stat Groups", """
            SELECT COUNT(*)
            FROM player_statistic
            WHERE stat_group NOT IN ('Passing', 'Rushing', 'Receiving', 'Defense', 
                                    'Kicking', 'Punting', 'Returning', 'Scoring')
        """),
        ("NULL Player IDs", """
            SELECT COUNT(*) FROM player_statistic WHERE player_id IS NULL
        """),
        ("NULL Team IDs", """
            SELECT COUNT(*) FROM player_statistic WHERE team_id IS NULL
        """),
        ("NULL Stat Groups", """
            SELECT COUNT(*) FROM player_statistic WHERE stat_group IS NULL
        """),
    ]
    
    all_passed = True
    for check_name, query in checks:
        results = run_query(conn, query)
        count = results[0]['count']
        
        if count == 0:
            print_pass(f"{check_name}: None found")
        else:
            print_fail(f"{check_name}: {count} found")
            all_passed = False
    
    return all_passed

def check_top_players(conn):
    """Check top players by category"""
    print_header("5. TOP PLAYERS VALIDATION")
    
    categories = [
        ("Passing Yards", "Passing", "yards"),
        ("Rushing Yards", "Rushing", "yards"),
        ("Receiving Yards", "Receiving", "yards"),
    ]
    
    for category_name, stat_group, metric_name in categories:
        query = """
            SELECT 
                p.full_name,
                t.abbrev as team,
                ps.metric_value as value
            FROM player_statistic ps
            JOIN player p ON ps.player_id = p.player_id
            JOIN team t ON ps.team_id = t.team_id
            WHERE ps.stat_group = %s
              AND ps.metric_name = %s
              AND ps.metric_value ~ '^[0-9]+$'
            ORDER BY CAST(ps.metric_value AS INTEGER) DESC
            LIMIT 5
        """
        
        results = run_query(conn, query, (stat_group, metric_name))
        
        if results:
            print(f"\n{category_name}:")
            for i, row in enumerate(results, 1):
                print(f"  {i}. {row['full_name']} ({row['team']}): {int(row['value']):,}")
            print_pass(f"{category_name} leaders found")
        else:
            print_fail(f"No {category_name} data found")

def check_materialized_view(conn):
    """Check materialized view"""
    print_header("6. MATERIALIZED VIEW CHECK")
    
    # Check if view exists and has data
    query = """
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT player_id) as players,
            MAX(last_updated) as last_updated
        FROM player_season_summary
    """
    
    try:
        results = run_query(conn, query)
        data = results[0]
        
        if data['total'] == 0:
            print_fail("Materialized view is empty")
            return False
        
        print(f"View Records: {data['total']:,}")
        print(f"View Players: {data['players']:,}")
        print(f"Last Updated: {data['last_updated']}")
        
        # Compare with raw table
        raw_query = """
            SELECT COUNT(DISTINCT player_id) as players
            FROM player_statistic
        """
        raw_results = run_query(conn, raw_query)
        raw_players = raw_results[0]['players']
        
        if data['players'] == raw_players:
            print_pass(f"View player count matches raw table ({raw_players:,})")
            return True
        else:
            print_warn(f"View has {data['players']:,} players, raw table has {raw_players:,}")
            print_warn("Consider running: python nfl_player_statistics_etl.py --refresh-view")
            return False
            
    except Exception as e:
        print_fail(f"View check failed: {e}")
        return False

def check_teams(conn):
    """Check team coverage"""
    print_header("7. TEAM COVERAGE")
    
    query = """
        SELECT 
            t.abbrev,
            COUNT(DISTINCT ps.player_id) as players
        FROM team t
        LEFT JOIN player_statistic ps ON t.team_id = ps.team_id
        WHERE t.external_team_key IS NOT NULL
        GROUP BY t.abbrev
        ORDER BY players DESC
    """
    
    results = run_query(conn, query)
    
    teams_with_stats = sum(1 for r in results if r['players'] > 0)
    teams_without_stats = sum(1 for r in results if r['players'] == 0)
    
    print(f"Teams with statistics: {teams_with_stats}")
    print(f"Teams without statistics: {teams_without_stats}")
    
    if teams_without_stats > 0:
        print(f"\nTeams missing statistics:")
        for row in results:
            if row['players'] == 0:
                print(f"  - {row['abbrev']}")
        
        if teams_with_stats == 1 and teams_without_stats == 31:
            print_warn("Only 1 team loaded (single team mode)")
            return True
        else:
            print_warn(f"{teams_without_stats} teams missing statistics")
            return False
    else:
        print_pass("All 32 teams have statistics")
        return True

def main():
    """Main validation routine"""
    parser = argparse.ArgumentParser(description='Validate player statistics data')
    parser.add_argument('--season', type=int, help='Season year to validate')
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}Player Statistics Validation{Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.season:
        print(f"Season: {args.season}")
    
    # Check environment variables
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print_fail(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = get_conn()
        print_pass("Database connection established")
    except Exception as e:
        print_fail(f"Database connection failed: {e}")
        sys.exit(1)
    
    # Run checks
    results = {
        'basic_stats': check_basic_stats(conn, args.season),
        'freshness': check_data_freshness(conn),
        'stat_groups': check_stat_groups(conn),
        'integrity': check_data_integrity(conn),
        'top_players': True,  # Always returns None, just displays
        'view': check_materialized_view(conn),
        'teams': check_teams(conn),
    }
    
    check_top_players(conn)  # Display top players
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    total = len([k for k in results.keys() if k != 'top_players'])
    
    print(f"Checks Passed: {passed}/{total}")
    
    if passed == total:
        print_pass("All validation checks passed! ✓")
        exit_code = 0
    elif passed >= total * 0.8:
        print_warn(f"Most checks passed ({passed}/{total}). Review warnings above.")
        exit_code = 0
    else:
        print_fail(f"Multiple checks failed ({total - passed} failures). Review errors above.")
        exit_code = 1
    
    conn.close()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
