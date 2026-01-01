#!/usr/bin/env python3
"""
Database Migration: Player Table Enhancements
==============================================
Adds columns needed for comprehensive player data storage.
Can be run safely multiple times (idempotent).

This migration extends the base player table schema to support
all fields returned by the sports-api.
"""

import os
import sys
import psycopg2
from psycopg2 import sql


def get_conn():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432)
    )


MIGRATION_COLUMNS = [
    # Core identifiers
    ("external_player_id", "INTEGER", "UNIQUE", "External API player ID"),
    
    # Jersey and physical stats
    ("jersey_number", "SMALLINT", None, "Player's jersey number"),
    ("height", "TEXT", None, "Player height (e.g., 6' 3\")"),
    ("weight", "TEXT", None, "Player weight (e.g., 230 lbs)"),
    ("age", "SMALLINT", None, "Current age"),
    
    # Background
    ("college", "TEXT", None, "College/university attended"),
    ("experience_years", "SMALLINT", None, "Years of NFL experience"),
    
    # Contract and media
    ("salary", "TEXT", None, "Annual salary"),
    ("image_url", "TEXT", None, "Player image URL"),
    
    # Categorization
    ("player_group", "TEXT", None, "Offense/Defense/Special Teams"),
    
    # Metadata
    ("created_at", "TIMESTAMPTZ", "DEFAULT NOW()", "Record creation timestamp"),
    ("updated_at", "TIMESTAMPTZ", "DEFAULT NOW()", "Record update timestamp"),
]


def run_migration(dry_run: bool = False):
    """
    Run the player table migration
    
    Args:
        dry_run: If True, only show what would be done
    """
    print("="*70)
    print("Player Table Migration")
    print("="*70)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    
    try:
        # Connect to database
        print("\n1. Connecting to database...")
        conn = get_conn()
        cursor = conn.cursor()
        print("✅ Connected successfully")
        
        # Check if player table exists
        print("\n2. Checking player table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'player'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Player table does not exist!")
            print("   Please ensure your base schema is deployed first.")
            cursor.close()
            conn.close()
            return False
        
        print("✅ Player table exists")
        
        # Get existing columns
        print("\n3. Checking existing columns...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'player';
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"✅ Found {len(existing_columns)} existing columns")
        
        # Determine which columns need to be added
        columns_to_add = []
        columns_already_exist = []
        
        for col_name, col_type, constraint, description in MIGRATION_COLUMNS:
            if col_name in existing_columns:
                columns_already_exist.append(col_name)
            else:
                columns_to_add.append((col_name, col_type, constraint, description))
        
        # Report status
        print(f"\n4. Migration plan:")
        print(f"   Columns already exist: {len(columns_already_exist)}")
        print(f"   Columns to add: {len(columns_to_add)}")
        
        if columns_already_exist:
            print(f"\n   ℹ️  Already exists: {', '.join(columns_already_exist)}")
        
        if not columns_to_add:
            print("\n✅ No migration needed - all columns already exist!")
            cursor.close()
            conn.close()
            return True
        
        # Add new columns
        print(f"\n5. Adding {len(columns_to_add)} new columns...")
        
        for col_name, col_type, constraint, description in columns_to_add:
            # Build ALTER TABLE statement
            constraint_clause = f" {constraint}" if constraint else ""
            alter_statement = f"""
                ALTER TABLE player 
                ADD COLUMN {col_name} {col_type}{constraint_clause}
            """
            
            print(f"\n   Adding: {col_name} ({description})")
            print(f"   SQL: {alter_statement.strip()}")
            
            if not dry_run:
                try:
                    cursor.execute(alter_statement)
                    conn.commit()
                    print(f"   ✅ Added {col_name}")
                except Exception as e:
                    print(f"   ❌ Failed to add {col_name}: {str(e)}")
                    conn.rollback()
                    raise
        
        # Create index on external_player_id if it doesn't exist
        print("\n6. Creating indexes...")
        index_sql = """
            CREATE INDEX IF NOT EXISTS idx_player_external_id 
            ON player(external_player_id)
        """
        
        print(f"   Creating index on external_player_id...")
        if not dry_run:
            cursor.execute(index_sql)
            conn.commit()
            print("   ✅ Index created")
        else:
            print("   🔍 Would create index")
        
        # Summary
        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        
        if dry_run:
            print("Mode: DRY RUN (no changes made)")
        else:
            print("Mode: LIVE (changes committed)")
        
        print(f"Columns added: {len(columns_to_add)}")
        print(f"Columns already existed: {len(columns_already_exist)}")
        print(f"Total columns in player table: {len(existing_columns) + len(columns_to_add)}")
        
        if not dry_run:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n🔍 Dry run completed. Run without --dry-run to apply changes.")
        
        print("="*70)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False


def rollback_migration(dry_run: bool = False):
    """
    Rollback the migration (remove added columns)
    
    WARNING: This will delete data in the added columns!
    
    Args:
        dry_run: If True, only show what would be done
    """
    print("="*70)
    print("Player Table Migration ROLLBACK")
    print("⚠️  WARNING: This will remove columns and their data!")
    print("="*70)
    
    if not dry_run:
        confirm = input("\nAre you sure you want to proceed? Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled.")
            return False
    else:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'player';
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        # Determine which columns to remove
        columns_to_remove = []
        for col_name, _, _, _ in MIGRATION_COLUMNS:
            if col_name in existing_columns:
                columns_to_remove.append(col_name)
        
        print(f"\nWill remove {len(columns_to_remove)} columns:")
        for col_name in columns_to_remove:
            print(f"   - {col_name}")
        
        if not columns_to_remove:
            print("\n✅ No columns to remove")
            cursor.close()
            conn.close()
            return True
        
        # Remove columns
        for col_name in columns_to_remove:
            drop_statement = f"ALTER TABLE player DROP COLUMN IF EXISTS {col_name}"
            print(f"\n   Removing: {col_name}")
            
            if not dry_run:
                cursor.execute(drop_statement)
                conn.commit()
                print(f"   ✅ Removed {col_name}")
            else:
                print(f"   🔍 Would remove {col_name}")
        
        # Drop index
        if not dry_run:
            cursor.execute("DROP INDEX IF EXISTS idx_player_external_id")
            conn.commit()
            print("\n   ✅ Removed index")
        
        cursor.close()
        conn.close()
        
        if not dry_run:
            print("\n✅ Rollback completed successfully!")
        else:
            print("\n🔍 Dry run completed.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {str(e)}")
        return False


def show_migration_info():
    """Display information about the migration"""
    print("="*70)
    print("Player Table Migration Information")
    print("="*70)
    
    print("\nThis migration adds the following columns to the player table:\n")
    
    for col_name, col_type, constraint, description in MIGRATION_COLUMNS:
        constraint_str = f" {constraint}" if constraint else ""
        print(f"  {col_name}")
        print(f"    Type: {col_type}{constraint_str}")
        print(f"    Description: {description}")
        print()
    
    print("="*70)


def main():
    """CLI for migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Database migration for player table enhancements',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show migration information
  python db_migration.py --info
  
  # Dry run (see what would change)
  python db_migration.py --dry-run
  
  # Apply migration
  python db_migration.py
  
  # Rollback migration (removes added columns)
  python db_migration.py --rollback --dry-run
  python db_migration.py --rollback
        """
    )
    
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration (remove added columns)')
    parser.add_argument('--info', action='store_true', help='Show migration information')
    
    args = parser.parse_args()
    
    # Show info and exit
    if args.info:
        show_migration_info()
        sys.exit(0)
    
    # Validate database environment variables
    required_db_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_db_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required database environment variables: {', '.join(missing_vars)}")
        print("Required: PGHOST, PGDATABASE, PGUSER, PGPASSWORD")
        print("Optional: PGPORT (defaults to 5432)")
        sys.exit(1)
    
    # Run migration or rollback
    if args.rollback:
        success = rollback_migration(args.dry_run)
    else:
        success = run_migration(args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
