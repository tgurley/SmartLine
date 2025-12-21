import os
import csv
from datetime import datetime
from etl.db import get_conn
from dotenv import load_dotenv

load_dotenv()

# Output directory
OUTPUT_DIR = "deepdive_export_" + datetime.now().strftime("%Y%m%d_%H%M%S")

def create_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    print(f"Export directory: {OUTPUT_DIR}/")
    return OUTPUT_DIR

def export_query_to_csv(conn, query, filename, description):
    """
    Execute a query and export results to CSV.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        filename: Output filename (without path)
        description: Description to print
    """
    print(f"\n📊 Exporting: {description}")
    print(f"   File: {filename}")
    
    cur = conn.cursor()
    cur.execute(query)
    
    rows = cur.fetchall()
    
    if not rows:
        print("   ⚠️  No data returned")
        cur.close()
        return
    
    # Get column names
    colnames = [desc[0] for desc in cur.description]
    
    # Write to CSV
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(colnames)
        writer.writerows(rows)
    
    print(f"   ✅ Exported {len(rows)} rows")
    cur.close()

def main():
    """Main export function"""
    create_output_dir()
    conn = get_conn()
    
    print(f"\n{'='*70}")
    print("SmartLine Odds Data Export")
    print(f"{'='*70}")
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            g.week,
            g.game_id,
            at.abbrev || ' @ ' || ht.abbrev AS matchup,
            g.game_datetime_utc AS kickoff_time,
            ol.pulled_at_utc AS snapshot_time,
            (g.game_datetime_utc - ol.pulled_at_utc) AS time_before_game,
            EXTRACT(EPOCH FROM (g.game_datetime_utc - ol.pulled_at_utc)) / 3600 AS hours_before_game,
            b.name AS book,
            ol.market,
            ol.side,
            ol.line_value,
            ol.price_american,
            CASE 
                WHEN ol.pulled_at_utc > g.game_datetime_utc THEN 'FUTURE (ERROR)'
                WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '6 hours' THEN 'Pre-Game (<6h)'
                WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '1 day' THEN 'Day Before'
                WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' THEN 'Closing Window (1-3d)'
                WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '5 days' THEN 'Mid-Week (3-5d)'
                WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '7 days' THEN 'Opening Window (5-7d)'
                ELSE 'Very Early (>7d)'
            END AS snapshot_category,
            -- Flag which week's "batch" this snapshot came from
            CASE 
                WHEN ol.pulled_at_utc BETWEEN '2023-09-01' AND '2023-09-02' THEN 'Week 1 Opening Batch'
                WHEN ol.pulled_at_utc BETWEEN '2023-09-07' AND '2023-09-08' THEN 'Week 1 Closing Batch'
                WHEN ol.pulled_at_utc BETWEEN '2023-09-08' AND '2023-09-09' THEN 'Week 2 Opening Batch'
                WHEN ol.pulled_at_utc BETWEEN '2023-09-15' AND '2023-09-16' THEN 'Week 3 Opening Batch'
                ELSE 'Other Batch'
            END AS api_batch_source
        FROM game g
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        JOIN odds_line ol ON ol.game_id = g.game_id
        JOIN book b ON b.book_id = ol.book_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        ORDER BY g.week, g.game_datetime_utc, ol.pulled_at_utc, b.name, ol.market, ol.side;

        """,
        "deepdive.csv",
        "Deep Dive"
    )
    
    conn.close()
    
    print(f"\n{'='*70}")
    print("Export Complete!")
    print(f"{'='*70}")
    print(f"\nAll files saved to: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("1. Review the CSV files")
    print("2. Check data quality report (05_data_quality_checks.csv)")
    print("3. Analyze line movement patterns (07 & 08)")
    print("4. Upload files to Claude for detailed analysis")
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()