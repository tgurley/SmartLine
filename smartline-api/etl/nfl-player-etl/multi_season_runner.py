#!/usr/bin/env python3
"""
Multi-Season Player ETL Runner
==============================
Utility script to run the player ETL across multiple NFL seasons.
Useful for initial data loads or backfilling historical data.
"""

import sys
from datetime import datetime
from nfl_player_etl import ETLConfig, PlayerETL


def run_multi_season_etl(start_season: int, end_season: int):
    """
    Run player ETL for multiple consecutive seasons
    
    Args:
        start_season: First season to process (e.g., 2020)
        end_season: Last season to process (e.g., 2023)
    """
    print("="*70)
    print(f"Multi-Season Player ETL: {start_season} - {end_season}")
    print("="*70)
    
    overall_stats = {
        'total_players': 0,
        'total_inserted': 0,
        'total_updated': 0,
        'total_failed': 0,
        'total_api_requests': 0,
        'seasons_processed': 0,
        'seasons_failed': 0
    }
    
    start_time = datetime.now()
    
    for season in range(start_season, end_season + 1):
        print(f"\n{'='*70}")
        print(f"Processing Season: {season}")
        print(f"{'='*70}\n")
        
        try:
            # Create configuration for this season
            config = ETLConfig.from_env(season)
            
            # Run ETL
            etl = PlayerETL(config)
            result = etl.run()
            
            # Aggregate stats
            if result.get('status') == 'success':
                overall_stats['total_players'] += result.get('players_processed', 0)
                overall_stats['total_inserted'] += result.get('inserted', 0)
                overall_stats['total_updated'] += result.get('updated', 0)
                overall_stats['total_failed'] += result.get('failed', 0)
                overall_stats['total_api_requests'] += result.get('api_requests', 0)
                overall_stats['seasons_processed'] += 1
            else:
                overall_stats['seasons_failed'] += 1
                print(f"❌ Season {season} failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Critical error processing season {season}: {str(e)}")
            overall_stats['seasons_failed'] += 1
    
    # Calculate total duration
    total_duration = (datetime.now() - start_time).total_seconds()
    
    # Print overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print(f"Seasons Requested: {end_season - start_season + 1}")
    print(f"Seasons Processed: {overall_stats['seasons_processed']}")
    print(f"Seasons Failed: {overall_stats['seasons_failed']}")
    print(f"Total API Requests: {overall_stats['total_api_requests']}")
    print(f"Total Players: {overall_stats['total_players']}")
    print(f"Total Inserted: {overall_stats['total_inserted']}")
    print(f"Total Updated: {overall_stats['total_updated']}")
    print(f"Total Failed: {overall_stats['total_failed']}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Average per Season: {total_duration / (end_season - start_season + 1):.2f}s")
    print(f"Avg API Requests/Season: {overall_stats['total_api_requests'] / max(overall_stats['seasons_processed'], 1):.1f}")
    print("="*70)
    
    return overall_stats


def run_all_teams_for_season(season: int, team_keys: list):
    """
    Run player ETL for all teams in a season individually
    Useful when the full season endpoint is rate-limited
    
    Args:
        season: Season year
        team_keys: List of external_team_key values
    """
    print("="*70)
    print(f"All Teams ETL for Season {season}")
    print(f"Processing {len(team_keys)} teams")
    print("="*70)
    
    overall_stats = {
        'total_players': 0,
        'total_inserted': 0,
        'total_updated': 0,
        'total_failed': 0,
        'total_api_requests': 0,
        'teams_processed': 0,
        'teams_failed': 0
    }
    
    start_time = datetime.now()
    config = ETLConfig.from_env(season)
    
    for team_key in team_keys:
        print(f"\nProcessing Team: {team_key}")
        
        try:
            etl = PlayerETL(config)
            result = etl.run_for_team(team_key)
            
            if result.get('status') == 'success':
                overall_stats['total_players'] += result.get('players_processed', 0)
                overall_stats['total_inserted'] += result.get('inserted', 0)
                overall_stats['total_updated'] += result.get('updated', 0)
                overall_stats['total_failed'] += result.get('failed', 0)
                overall_stats['total_api_requests'] += result.get('api_requests', 0)
                overall_stats['teams_processed'] += 1
                print(f"✅ {result.get('players_processed', 0)} players processed")
            else:
                overall_stats['teams_failed'] += 1
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Critical error: {str(e)}")
            overall_stats['teams_failed'] += 1
    
    total_duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("TEAM ETL SUMMARY")
    print("="*70)
    print(f"Teams Requested: {len(team_keys)}")
    print(f"Teams Processed: {overall_stats['teams_processed']}")
    print(f"Teams Failed: {overall_stats['teams_failed']}")
    print(f"Total API Requests: {overall_stats['total_api_requests']}")
    print(f"Total Players: {overall_stats['total_players']}")
    print(f"Total Inserted: {overall_stats['total_inserted']}")
    print(f"Total Updated: {overall_stats['total_updated']}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Avg API Requests/Team: {overall_stats['total_api_requests'] / max(overall_stats['teams_processed'], 1):.1f}")
    print("="*70)
    
    return overall_stats


def main():
    """CLI for multi-season runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Season NFL Player ETL')
    parser.add_argument('--start-season', type=int, help='Starting season (e.g., 2020)')
    parser.add_argument('--end-season', type=int, help='Ending season (e.g., 2023)')
    parser.add_argument('--single-season', type=int, help='Run single season (shortcut)')
    parser.add_argument('--teams', nargs='+', type=int, help='Run specific teams for a season')
    parser.add_argument('--season-for-teams', type=int, help='Season year when using --teams')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.single_season:
        # Single season mode
        result = run_multi_season_etl(args.single_season, args.single_season)
    elif args.teams:
        # Team-specific mode
        if not args.season_for_teams:
            print("Error: --season-for-teams required when using --teams")
            sys.exit(1)
        result = run_all_teams_for_season(args.season_for_teams, args.teams)
    elif args.start_season and args.end_season:
        # Multi-season mode
        if args.start_season > args.end_season:
            print("Error: start-season must be <= end-season")
            sys.exit(1)
        result = run_multi_season_etl(args.start_season, args.end_season)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Single season")
        print("  python multi_season_runner.py --single-season 2023")
        print("\n  # Multiple seasons")
        print("  python multi_season_runner.py --start-season 2020 --end-season 2023")
        print("\n  # Specific teams")
        print("  python multi_season_runner.py --season-for-teams 2023 --teams 1 2 3 4")
        sys.exit(1)
    
    # Exit with appropriate code
    if result.get('seasons_failed', 0) == 0 and result.get('teams_failed', 0) == 0:
        print("\n✅ All operations completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some operations failed. Check logs for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
