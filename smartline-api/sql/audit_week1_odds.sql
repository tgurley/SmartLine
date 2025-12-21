-- =========================================================
-- SmartLine Odds Data Audit - Week 1
-- =========================================================
-- Run these queries to verify your Week 1 odds data looks good
-- =========================================================

-- =========================================================
-- 1. HIGH-LEVEL COVERAGE
-- =========================================================

-- Total odds lines inserted
SELECT 
    'Total Odds Lines' AS metric,
    COUNT(*) AS value
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1;

-- Games with odds data
SELECT 
    'Games with Odds' AS metric,
    COUNT(DISTINCT ol.game_id) AS value
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1;

-- Total Week 1 games
SELECT 
    'Total Week 1 Games' AS metric,
    COUNT(*) AS value
FROM game
WHERE week = 1
  AND season_id = (
      SELECT season_id FROM season s
      JOIN league l ON l.league_id = s.league_id
      WHERE l.name = 'NFL' AND s.year = 2023
  );

-- =========================================================
-- 2. COVERAGE BY BOOK
-- =========================================================

SELECT 
    b.name AS sportsbook,
    COUNT(*) AS total_odds_lines,
    COUNT(DISTINCT ol.game_id) AS games_covered,
    COUNT(DISTINCT ol.market) AS markets_covered
FROM odds_line ol
JOIN book b ON b.book_id = ol.book_id
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
GROUP BY b.name
ORDER BY total_odds_lines DESC;

-- =========================================================
-- 3. COVERAGE BY MARKET
-- =========================================================

SELECT 
    market,
    COUNT(*) AS total_lines,
    COUNT(DISTINCT game_id) AS games_covered,
    COUNT(DISTINCT book_id) AS books_offering
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
GROUP BY market
ORDER BY market;

-- =========================================================
-- 4. SNAPSHOTS PER GAME
-- =========================================================
-- Should see 2 distinct timestamps per game (opening + closing)

SELECT 
    g.game_id,
    at.abbrev || ' @ ' || ht.abbrev AS matchup,
    COUNT(DISTINCT ol.pulled_at_utc) AS num_snapshots,
    MIN(ol.pulled_at_utc) AS earliest_snapshot,
    MAX(ol.pulled_at_utc) AS latest_snapshot,
    g.game_datetime_utc AS kickoff
FROM game g
JOIN team ht ON g.home_team_id = ht.team_id
JOIN team at ON g.away_team_id = at.team_id
LEFT JOIN odds_line ol ON ol.game_id = g.game_id
WHERE g.week = 1
GROUP BY g.game_id, at.abbrev, ht.abbrev, g.game_datetime_utc
ORDER BY g.game_datetime_utc;

-- =========================================================
-- 5. SAMPLE GAME - FULL ODDS DETAIL
-- =========================================================
-- Pick the first game and show all odds

WITH first_game AS (
    SELECT game_id, home_team_id, away_team_id
    FROM game
    WHERE week = 1
      AND season_id = (
          SELECT season_id FROM season s
          JOIN league l ON l.league_id = s.league_id
          WHERE l.name = 'NFL' AND s.year = 2023
      )
    ORDER BY game_datetime_utc
    LIMIT 1
)
SELECT 
    at.abbrev || ' @ ' || ht.abbrev AS matchup,
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
FROM first_game fg
JOIN game g ON g.game_id = fg.game_id
JOIN team ht ON g.home_team_id = ht.team_id
JOIN team at ON g.away_team_id = at.team_id
JOIN odds_line ol ON ol.game_id = fg.game_id
JOIN book b ON b.book_id = ol.book_id
ORDER BY ol.pulled_at_utc, b.name, ol.market, ol.side;

-- =========================================================
-- 6. LINE MOVEMENT ANALYSIS - SPREADS
-- =========================================================
-- Compare opening vs closing spreads for all Week 1 games

WITH spread_movement AS (
    SELECT 
        g.game_id,
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
    WHERE g.week = 1
      AND ol.market = 'spread'
      AND ol.side = 'home'  -- Just look at home side for simplicity
    GROUP BY g.game_id, at.abbrev, ht.abbrev, b.name, ol.side
)
SELECT 
    matchup,
    book,
    opening_line,
    closing_line,
    (closing_line - opening_line) AS line_movement,
    opening_price,
    closing_price,
    CASE 
        WHEN ABS(closing_line - opening_line) >= 1.0 THEN 'Significant'
        WHEN ABS(closing_line - opening_line) >= 0.5 THEN 'Moderate'
        ELSE 'Minimal'
    END AS movement_type
FROM spread_movement
WHERE opening_line IS NOT NULL 
  AND closing_line IS NOT NULL
ORDER BY ABS(closing_line - opening_line) DESC, matchup;

-- =========================================================
-- 7. TOTAL (O/U) MOVEMENT ANALYSIS
-- =========================================================

WITH total_movement AS (
    SELECT 
        g.game_id,
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
    WHERE g.week = 1
      AND ol.market = 'total'
      AND ol.side = 'over'  -- Both over/under have same line_value
    GROUP BY g.game_id, at.abbrev, ht.abbrev, b.name
)
SELECT 
    matchup,
    book,
    opening_total,
    closing_total,
    (closing_total - opening_total) AS total_movement,
    CASE 
        WHEN ABS(closing_total - opening_total) >= 3.0 THEN 'Major Move'
        WHEN ABS(closing_total - opening_total) >= 1.0 THEN 'Moved'
        ELSE 'Stable'
    END AS movement_type
FROM total_movement
WHERE opening_total IS NOT NULL 
  AND closing_total IS NOT NULL
ORDER BY ABS(closing_total - opening_total) DESC, matchup;

-- =========================================================
-- 8. MONEYLINE ODDS DISTRIBUTION
-- =========================================================
-- See the range of moneyline prices

SELECT 
    CASE 
        WHEN ol.price_american < -300 THEN 'Heavy Favorite (-300 or better)'
        WHEN ol.price_american < -200 THEN 'Favorite (-200 to -299)'
        WHEN ol.price_american < -150 THEN 'Moderate Favorite (-150 to -199)'
        WHEN ol.price_american < 0 THEN 'Slight Favorite (-1 to -149)'
        WHEN ol.price_american < 150 THEN 'Slight Underdog (+1 to +149)'
        WHEN ol.price_american < 200 THEN 'Moderate Underdog (+150 to +199)'
        WHEN ol.price_american < 300 THEN 'Underdog (+200 to +299)'
        ELSE 'Heavy Underdog (+300 or more)'
    END AS odds_category,
    COUNT(*) AS count
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
  AND ol.market = 'moneyline'
GROUP BY 
    CASE 
        WHEN ol.price_american < -300 THEN 1
        WHEN ol.price_american < -200 THEN 2
        WHEN ol.price_american < -150 THEN 3
        WHEN ol.price_american < 0 THEN 4
        WHEN ol.price_american < 150 THEN 5
        WHEN ol.price_american < 200 THEN 6
        WHEN ol.price_american < 300 THEN 7
        ELSE 8
    END,
    CASE 
        WHEN ol.price_american < -300 THEN 'Heavy Favorite (-300 or better)'
        WHEN ol.price_american < -200 THEN 'Favorite (-200 to -299)'
        WHEN ol.price_american < -150 THEN 'Moderate Favorite (-150 to -199)'
        WHEN ol.price_american < 0 THEN 'Slight Favorite (-1 to -149)'
        WHEN ol.price_american < 150 THEN 'Slight Underdog (+1 to +149)'
        WHEN ol.price_american < 200 THEN 'Moderate Underdog (+150 to +199)'
        WHEN ol.price_american < 300 THEN 'Underdog (+200 to +299)'
        ELSE 'Heavy Underdog (+300 or more)'
    END
ORDER BY 
    CASE 
        WHEN ol.price_american < -300 THEN 1
        WHEN ol.price_american < -200 THEN 2
        WHEN ol.price_american < -150 THEN 3
        WHEN ol.price_american < 0 THEN 4
        WHEN ol.price_american < 150 THEN 5
        WHEN ol.price_american < 200 THEN 6
        WHEN ol.price_american < 300 THEN 7
        ELSE 8
    END;

-- =========================================================
-- 9. DATA QUALITY CHECKS
-- =========================================================

-- Check for NULL values where they shouldn't be
SELECT 
    'Null Line Values in Spreads/Totals' AS issue,
    COUNT(*) AS count
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
  AND ol.market IN ('spread', 'total')
  AND ol.line_value IS NULL

UNION ALL

SELECT 
    'Null Line Values in Moneyline' AS issue,
    COUNT(*) AS count
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
  AND ol.market = 'moneyline'
  AND ol.line_value IS NOT NULL  -- Should be NULL for moneyline

UNION ALL

SELECT 
    'Invalid Price (zero)' AS issue,
    COUNT(*) AS count
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
  AND ol.price_american = 0

UNION ALL

SELECT 
    'Future-dated Snapshots' AS issue,
    COUNT(*) AS count
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1
  AND ol.pulled_at_utc > g.game_datetime_utc;

-- =========================================================
-- 10. CROSS-BOOK COMPARISON
-- =========================================================
-- Compare spread lines across all books for consistency

SELECT 
    g.game_id,
    at.abbrev || ' @ ' || ht.abbrev AS matchup,
    ol.pulled_at_utc,
    STRING_AGG(
        b.name || ': ' || ol.line_value::TEXT || ' (' || ol.price_american || ')',
        ' | '
        ORDER BY b.name
    ) AS all_books_spreads
FROM game g
JOIN team ht ON g.home_team_id = ht.team_id
JOIN team at ON g.away_team_id = at.team_id
JOIN odds_line ol ON ol.game_id = g.game_id
JOIN book b ON b.book_id = ol.book_id
WHERE g.week = 1
  AND ol.market = 'spread'
  AND ol.side = 'home'
GROUP BY g.game_id, at.abbrev, ht.abbrev, ol.pulled_at_utc, g.game_datetime_utc
ORDER BY g.game_datetime_utc, ol.pulled_at_utc;

-- =========================================================
-- 11. SUMMARY STATISTICS
-- =========================================================

SELECT 
    'Week 1 Odds Summary' AS summary_title,
    COUNT(DISTINCT ol.game_id) AS games_with_odds,
    COUNT(*) AS total_odds_lines,
    COUNT(DISTINCT ol.book_id) AS unique_books,
    COUNT(DISTINCT ol.pulled_at_utc) AS unique_snapshots,
    MIN(ol.pulled_at_utc) AS earliest_snapshot,
    MAX(ol.pulled_at_utc) AS latest_snapshot
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.week = 1;