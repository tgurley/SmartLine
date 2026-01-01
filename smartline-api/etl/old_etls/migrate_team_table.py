#!/usr/bin/env python3
"""
Team Table Migration
====================
Adds additional columns to the team table for API data.

Usage:
    python migrate_team_table.py
"""

import os
import sys
import psycopg2
from datetime import datetime


def get_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )


def migrate_team_table():
    """Add new columns to team table"""
    
    print("="*70)
    print("TEAM TABLE MIGRATION")
    print("="*70)
    print()
    
    conn = get_conn()
    cursor = conn.cursor()
    
    # Check current table structure
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'team' 
        ORDER BY ordinal_position
    """)
    
    current_columns = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"Current team table has {len(current_columns)} columns:")
    for col, dtype in current_columns.items():
        print(f"  - {col}: {dtype}")
    print()
    
    # Define new columns to add
    new_columns = [
        ("coach", "TEXT", "Team's current head coach"),
        ("owner", "TEXT", "Team owner(s)"),
        ("stadium", "TEXT", "Home stadium name"),
        ("established", "INTEGER", "Year team was established"),
        ("logo_url", "TEXT", "URL to team logo image"),
        ("country_name", "TEXT", "Country name (e.g., USA)"),
        ("country_code", "TEXT", "Country code (e.g., US)"),
        ("country_flag_url", "TEXT", "URL to country flag image"),
        ("updated_at", "TIMESTAMPTZ", "Last update timestamp"),
    ]
    
    # Add columns if they don't exist
    print("Adding new columns...")
    added_count = 0
    
    for col_name, col_type, description in new_columns:
        if col_name not in current_columns:
            try:
                sql = f"ALTER TABLE team ADD COLUMN {col_name} {col_type}"
                if col_name == "updated_at":
                    sql += " DEFAULT NOW()"
                
                cursor.execute(sql)
                conn.commit()
                print(f"  ✓ Added {col_name} ({col_type}) - {description}")
                added_count += 1
            except Exception as e:
                print(f"  ✗ Failed to add {col_name}: {str(e)}")
                conn.rollback()
        else:
            print(f"  - {col_name} already exists")
    
    print()
    print(f"Migration complete: {added_count} columns added")
    
    # Show updated structure
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'team' 
        ORDER BY ordinal_position
    """)
    
    updated_columns = cursor.fetchall()
    
    print()
    print(f"Updated team table now has {len(updated_columns)} columns:")
    for col, dtype in updated_columns:
        print(f"  - {col}: {dtype}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*70)
    print("MIGRATION SUCCESSFUL")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Run: python nfl_team_etl.py --all")
    print("  2. This will fetch logos and additional data for all teams")
    print()


def main():
    """Main entry point"""
    
    # Check environment variables
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    try:
        migrate_team_table()
        sys.exit(0)
    except Exception as e:
        print(f"\nMigration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
