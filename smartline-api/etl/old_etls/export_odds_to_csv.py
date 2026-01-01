#!/usr/bin/env python3
"""
Export SmartLine odds data to CSV files for analysis.

This script exports:
1. Summary statistics
2. Sample odds data
3. Line movement analysis
4. Data quality report

Usage:
    python export_odds_to_csv.py
"""

import os
import csv
from datetime import datetime
from etl.db import get_conn
from dotenv import load_dotenv

load_dotenv()

# Output directory
OUTPUT_DIR = "odds_export_" + datetime.now().strftime("%Y%m%d_%H%M%S")

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
    
    # ========================================
    # 1. SUMMARY STATISTICS
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            'Total Odds Lines' AS metric,
            COUNT(*) AS value
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        UNION ALL
        SELECT 
            'Total Games' AS metric,
            COUNT(*) AS value
        FROM game
        WHERE season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        UNION ALL
        SELECT 
            'Games with Odds' AS metric,
            COUNT(DISTINCT ol.game_id) AS value
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        UNION ALL
        SELECT 
            'Unique Books' AS metric,
            COUNT(DISTINCT book_id) AS value
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        UNION ALL
        SELECT 
            'Unique Snapshots' AS metric,
            COUNT(DISTINCT pulled_at_utc) AS value
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        );
        """,
        "01_summary_statistics.csv",
        "Summary Statistics"
    )
    
    # ========================================
    # 2. COVERAGE BY WEEK
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            g.week,
            COUNT(DISTINCT g.game_id) AS total_games,
            COUNT(DISTINCT ol.game_id) AS games_with_odds,
            COUNT(*) AS total_odds_lines,
            COUNT(DISTINCT ol.pulled_at_utc) AS unique_snapshots,
            ROUND(COUNT(DISTINCT ol.game_id)::NUMERIC / COUNT(DISTINCT g.game_id) * 100, 1) AS coverage_pct
        FROM game g
        LEFT JOIN odds_line ol ON ol.game_id = g.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        GROUP BY g.week
        ORDER BY g.week;
        """,
        "02_coverage_by_week.csv",
        "Coverage by Week"
    )
    
    # ========================================
    # 3. COVERAGE BY BOOK
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            b.name AS sportsbook,
            COUNT(*) AS total_odds_lines,
            COUNT(DISTINCT ol.game_id) AS games_covered,
            COUNT(DISTINCT ol.market) AS markets_covered,
            COUNT(DISTINCT ol.pulled_at_utc) AS snapshots
        FROM odds_line ol
        JOIN book b ON b.book_id = ol.book_id
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        GROUP BY b.name
        ORDER BY total_odds_lines DESC;
        """,
        "03_coverage_by_book.csv",
        "Coverage by Sportsbook"
    )
    
    # ========================================
    # 4. COVERAGE BY MARKET
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            market,
            COUNT(*) AS total_lines,
            COUNT(DISTINCT ol.game_id) AS games_covered,
            COUNT(DISTINCT book_id) AS books_offering,
            COUNT(DISTINCT pulled_at_utc) AS snapshots
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        GROUP BY market
        ORDER BY market;
        """,
        "04_coverage_by_market.csv",
        "Coverage by Market"
    )
    
    # ========================================
    # 5. DATA QUALITY CHECKS
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            'Null line_value in spread/total' AS issue,
            COUNT(*) AS count
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND ol.market IN ('spread', 'total')
        AND ol.line_value IS NULL
        UNION ALL
        SELECT 
            'Non-null line_value in moneyline' AS issue,
            COUNT(*) AS count
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND ol.market = 'moneyline'
        AND ol.line_value IS NOT NULL
        UNION ALL
        SELECT 
            'Invalid price (zero)' AS issue,
            COUNT(*) AS count
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND ol.price_american = 0
        UNION ALL
        SELECT 
            'Future-dated snapshots' AS issue,
            COUNT(*) AS count
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND ol.pulled_at_utc > g.game_datetime_utc
        UNION ALL
        SELECT 
            'Extreme prices (abs > 5000)' AS issue,
            COUNT(*) AS count
        FROM odds_line ol
        JOIN game g ON g.game_id = ol.game_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND ABS(ol.price_american) > 5000;
        """,
        "05_data_quality_checks.csv",
        "Data Quality Checks"
    )
    
    # ========================================
    # 6. SAMPLE ODDS DATA (Week 1)
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            g.week,
            g.game_id,
            at.abbrev || ' @ ' || ht.abbrev AS matchup,
            g.game_datetime_utc AS kickoff,
            b.name AS book,
            ol.market,
            ol.side,
            ol.line_value,
            ol.price_american,
            ol.pulled_at_utc,
            CASE 
                WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days'
                THEN 'Opening'
                ELSE 'Closing'
            END AS snapshot_type
        FROM game g
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        JOIN odds_line ol ON ol.game_id = g.game_id
        JOIN book b ON b.book_id = ol.book_id
        WHERE g.week = 1
          AND g.season_id = (
              SELECT season_id FROM season s
              JOIN league l ON l.league_id = s.league_id
              WHERE l.name = 'NFL' AND s.year = 2023
          )
        ORDER BY g.game_datetime_utc, ol.pulled_at_utc, b.name, ol.market, ol.side
        LIMIT 1000;
        """,
        "06_sample_odds_week1.csv",
        "Sample Odds Data (Week 1, first 1000 rows)"
    )
    
    # ========================================
    # 7. SPREAD LINE MOVEMENT
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        WITH spread_movement AS (
            SELECT 
                g.game_id,
                g.week,
                at.abbrev || ' @ ' || ht.abbrev AS matchup,
                b.name AS book,
                ol.side,
                MIN(CASE WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.line_value END) AS opening_line,
                MAX(CASE WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.line_value END) AS closing_line,
                MIN(CASE WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.price_american END) AS opening_price,
                MAX(CASE WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.price_american END) AS closing_price
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
            AND ol.market = 'spread'
            AND ol.side = 'home'
            GROUP BY g.game_id, g.week, at.abbrev, ht.abbrev, b.name, ol.side
        )
        SELECT 
            week,
            matchup,
            book,
            opening_line,
            closing_line,
            (closing_line - opening_line) AS line_movement,
            opening_price,
            closing_price,
            CASE 
                WHEN ABS(closing_line - opening_line) >= 2.5 THEN 'Large'
                WHEN ABS(closing_line - opening_line) >= 1.0 THEN 'Moderate'
                WHEN ABS(closing_line - opening_line) >= 0.5 THEN 'Small'
                ELSE 'None'
            END AS movement_type
        FROM spread_movement
        WHERE opening_line IS NOT NULL 
          AND closing_line IS NOT NULL
        ORDER BY ABS(closing_line - opening_line) DESC, week, matchup
        LIMIT 500;
        """,
        "07_spread_line_movement.csv",
        "Spread Line Movement (top 500 by movement)"
    )
    
    # ========================================
    # 8. TOTAL LINE MOVEMENT
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        WITH total_movement AS (
            SELECT 
                g.game_id,
                g.week,
                at.abbrev || ' @ ' || ht.abbrev AS matchup,
                b.name AS book,
                MIN(CASE WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.line_value END) AS opening_total,
                MAX(CASE WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' 
                    THEN ol.line_value END) AS closing_total
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
            AND ol.market = 'total'
            AND ol.side = 'over'
            GROUP BY g.game_id, g.week, at.abbrev, ht.abbrev, b.name
        )
        SELECT 
            week,
            matchup,
            book,
            opening_total,
            closing_total,
            (closing_total - opening_total) AS total_movement,
            CASE 
                WHEN ABS(closing_total - opening_total) >= 3.0 THEN 'Large'
                WHEN ABS(closing_total - opening_total) >= 1.5 THEN 'Moderate'
                WHEN ABS(closing_total - opening_total) >= 0.5 THEN 'Small'
                ELSE 'None'
            END AS movement_type
        FROM total_movement
        WHERE opening_total IS NOT NULL 
          AND closing_total IS NOT NULL
        ORDER BY ABS(closing_total - opening_total) DESC, week, matchup
        LIMIT 500;
        """,
        "08_total_line_movement.csv",
        "Total Line Movement (top 500 by movement)"
    )
    
    # ========================================
    # 9. SNAPSHOTS PER GAME
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        WITH snapshots_per_game AS (
            SELECT 
                g.game_id,
                g.week,
                at.abbrev || ' @ ' || ht.abbrev AS matchup,
                COUNT(DISTINCT ol.pulled_at_utc) AS num_snapshots
            FROM game g
            JOIN team ht ON g.home_team_id = ht.team_id
            JOIN team at ON g.away_team_id = at.team_id
            LEFT JOIN odds_line ol ON ol.game_id = g.game_id
            WHERE g.season_id = (
                SELECT season_id FROM season s
                JOIN league l ON l.league_id = s.league_id
                WHERE l.name = 'NFL' AND s.year = 2023
            )
            GROUP BY g.game_id, g.week, at.abbrev, ht.abbrev
        )
        SELECT 
            week,
            matchup,
            num_snapshots
        FROM snapshots_per_game
        ORDER BY num_snapshots DESC, week, matchup;
        """,
        "09_snapshots_per_game.csv",
        "Snapshots per Game"
    )
    
    # ========================================
    # 10. MISSING ODDS GAMES
    # ========================================
    
    export_query_to_csv(
        conn,
        """
        SELECT 
            g.week,
            g.game_id,
            at.abbrev || ' @ ' || ht.abbrev AS matchup,
            g.game_datetime_utc AS kickoff
        FROM game g
        JOIN team ht ON g.home_team_id = ht.team_id
        JOIN team at ON g.away_team_id = at.team_id
        WHERE g.season_id = (
            SELECT season_id FROM season s
            JOIN league l ON l.league_id = s.league_id
            WHERE l.name = 'NFL' AND s.year = 2023
        )
        AND g.game_id NOT IN (
            SELECT DISTINCT game_id FROM odds_line
        )
        ORDER BY g.week, g.game_datetime_utc;
        """,
        "10_missing_odds_games.csv",
        "Games Missing Odds Data"
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