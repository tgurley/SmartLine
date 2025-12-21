-- =========================================================
-- SmartLine Full Season Odds Data Validation
-- =========================================================
-- Comprehensive checks for 2023 NFL season odds data
-- =========================================================

-- =========================================================
-- 1. OVERALL COVERAGE SUMMARY
-- =========================================================

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
    'Games Missing Odds' AS metric,
    COUNT(*) AS value
FROM game g
WHERE g.season_id = (
    SELECT season_id FROM season s
    JOIN league l ON l.league_id = s.league_id
    WHERE l.name = 'NFL' AND s.year = 2023
)
AND g.game_id NOT IN (
    SELECT DISTINCT game_id FROM odds_line
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

-- =========================================================
-- 2. COVERAGE BY WEEK
-- =========================================================

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

-- =========================================================
-- 3. COVERAGE BY BOOK
-- =========================================================

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

-- =========================================================
-- 4. COVERAGE BY MARKET
-- =========================================================

SELECT 
    market,
    COUNT(*) AS total_lines,
    COUNT(DISTINCT game_id) AS games_covered,
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

-- =========================================================
-- 5. SNAPSHOTS PER GAME DISTRIBUTION
-- =========================================================

WITH snapshots_per_game AS (
    SELECT 
        g.game_id,
        COUNT(DISTINCT ol.pulled_at_utc) AS num_snapshots
    FROM game g
    LEFT JOIN odds_line ol ON ol.game_id = g.game_id
    WHERE g.season_id = (
        SELECT season_id FROM season s
        JOIN league l ON l.league_id = s.league_id
        WHERE l.name = 'NFL' AND s.year = 2023
    )
    GROUP BY g.game_id
)
SELECT 
    num_snapshots,
    COUNT(*) AS num_games,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 1) AS pct_of_games
FROM snapshots_per_game
GROUP BY num_snapshots
ORDER BY num_snapshots;

-- =========================================================
-- 6. DATA QUALITY CHECKS
-- =========================================================

-- Check for invalid data
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

-- =========================================================
-- 7. LINE MOVEMENT STATISTICS (SPREADS)
-- =========================================================

WITH spread_movement AS (
    SELECT 
        g.game_id,
        g.week,
        b.name AS book,
        ol.side,
        MIN(CASE WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days' 
            THEN ol.line_value END) AS opening_line,
        MAX(CASE WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' 
            THEN ol.line_value END) AS closing_line
    FROM game g
    JOIN odds_line ol ON ol.game_id = g.game_id
    JOIN book b ON b.book_id = ol.book_id
    WHERE g.season_id = (
        SELECT season_id FROM season s
        JOIN league l ON l.league_id = s.league_id
        WHERE l.name = 'NFL' AND s.year = 2023
    )
    AND ol.market = 'spread'
    AND ol.side = 'home'
    GROUP BY g.game_id, g.week, b.name, ol.side
)
SELECT 
    'No Movement (0)' AS movement_category,
    COUNT(*) AS count
FROM spread_movement
WHERE opening_line IS NOT NULL 
  AND closing_line IS NOT NULL
  AND opening_line = closing_line

UNION ALL

SELECT 
    'Small Move (0.5)' AS movement_category,
    COUNT(*) AS count
FROM spread_movement
WHERE opening_line IS NOT NULL 
  AND closing_line IS NOT NULL
  AND ABS(closing_line - opening_line) = 0.5

UNION ALL

SELECT 
    'Moderate Move (1-2 pts)' AS movement_category,
    COUNT(*) AS count
FROM spread_movement
WHERE opening_line IS NOT NULL 
  AND closing_line IS NOT NULL
  AND ABS(closing_line - opening_line) BETWEEN 1.0 AND 2.0

UNION ALL

SELECT 
    'Large Move (2.5+ pts)' AS movement_category,
    COUNT(*) AS count
FROM spread_movement
WHERE opening_line IS NOT NULL 
  AND closing_line IS NOT NULL
  AND ABS(closing_line - opening_line) >= 2.5;

-- =========================================================
-- 8. TOTAL (O/U) MOVEMENT STATISTICS
-- =========================================================

WITH total_movement AS (
    SELECT 
        g.game_id,
        g.week,
        b.name AS book,
        MIN(CASE WHEN ol.pulled_at_utc < g.game_datetime_utc - INTERVAL '3 days' 
            THEN ol.line_value END) AS opening_total,
        MAX(CASE WHEN ol.pulled_at_utc >= g.game_datetime_utc - INTERVAL '3 days' 
            THEN ol.line_value END) AS closing_total
    FROM game g
    JOIN odds_line ol ON ol.game_id = g.game_id
    JOIN book b ON b.book_id = ol.book_id
    WHERE g.season_id = (
        SELECT season_id FROM season s
        JOIN league l ON l.league_id = s.league_id
        WHERE l.name = 'NFL' AND s.year = 2023
    )
    AND ol.market = 'total'
    AND ol.side = 'over'
    GROUP BY g.game_id, g.week, b.name
)
SELECT 
    'No Movement (0)' AS movement_category,
    COUNT(*) AS count
FROM total_movement
WHERE opening_total IS NOT NULL 
  AND closing_total IS NOT NULL
  AND opening_total = closing_total

UNION ALL

SELECT 
    'Small Move (0.5-1)' AS movement_category,
    COUNT(*) AS count
FROM total_movement
WHERE opening_total IS NOT NULL 
  AND closing_total IS NOT NULL
  AND ABS(closing_total - opening_total) BETWEEN 0.5 AND 1.0

UNION ALL

SELECT 
    'Moderate Move (1.5-2.5)' AS movement_category,
    COUNT(*) AS count
FROM total_movement
WHERE opening_total IS NOT NULL 
  AND closing_total IS NOT NULL
  AND ABS(closing_total - opening_total) BETWEEN 1.5 AND 2.5

UNION ALL

SELECT 
    'Large Move (3+)' AS movement_category,
    COUNT(*) AS count
FROM total_movement
WHERE opening_total IS NOT NULL 
  AND closing_total IS NOT NULL
  AND ABS(closing_total - opening_total) >= 3.0;

-- =========================================================
-- 9. PRICE DISTRIBUTION (ALL MARKETS)
-- =========================================================

SELECT 
    CASE 
        WHEN ol.price_american < -300 THEN 'Heavy Favorite/Over (-300+)'
        WHEN ol.price_american < -200 THEN 'Favorite (-200 to -299)'
        WHEN ol.price_american < -150 THEN 'Moderate Favorite (-150 to -199)'
        WHEN ol.price_american < -100 THEN 'Slight Favorite (-100 to -149)'
        WHEN ol.price_american = -110 THEN 'Standard Line (-110)'
        WHEN ol.price_american > -110 AND ol.price_american < 0 THEN 'Juice Favorite (-109 to -100)'
        WHEN ol.price_american > 0 AND ol.price_american < 150 THEN 'Slight Underdog (+100 to +149)'
        WHEN ol.price_american < 200 THEN 'Moderate Underdog (+150 to +199)'
        WHEN ol.price_american < 300 THEN 'Underdog (+200 to +299)'
        ELSE 'Heavy Underdog (+300+)'
    END AS price_category,
    COUNT(*) AS count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) AS pct
FROM odds_line ol
JOIN game g ON g.game_id = ol.game_id
WHERE g.season_id = (
    SELECT season_id FROM season s
    JOIN league l ON l.league_id = s.league_id
    WHERE l.name = 'NFL' AND s.year = 2023
)
GROUP BY 
    CASE 
        WHEN ol.price_american < -300 THEN 1
        WHEN ol.price_american < -200 THEN 2
        WHEN ol.price_american < -150 THEN 3
        WHEN ol.price_american < -100 THEN 4
        WHEN ol.price_american = -110 THEN 5
        WHEN ol.price_american > -110 AND ol.price_american < 0 THEN 6
        WHEN ol.price_american > 0 AND ol.price_american < 150 THEN 7
        WHEN ol.price_american < 200 THEN 8
        WHEN ol.price_american < 300 THEN 9
        ELSE 10
    END,
    CASE 
        WHEN ol.price_american < -300 THEN 'Heavy Favorite/Over (-300+)'
        WHEN ol.price_american < -200 THEN 'Favorite (-200 to -299)'
        WHEN ol.price_american < -150 THEN 'Moderate Favorite (-150 to -199)'
        WHEN ol.price_american < -100 THEN 'Slight Favorite (-100 to -149)'
        WHEN ol.price_american = -110 THEN 'Standard Line (-110)'
        WHEN ol.price_american > -110 AND ol.price_american < 0 THEN 'Juice Favorite (-109 to -100)'
        WHEN ol.price_american > 0 AND ol.price_american < 150 THEN 'Slight Underdog (+100 to +149)'
        WHEN ol.price_american < 200 THEN 'Moderate Underdog (+150 to +199)'
        WHEN ol.price_american < 300 THEN 'Underdog (+200 to +299)'
        ELSE 'Heavy Underdog (+300+)'
    END
ORDER BY 
    CASE 
        WHEN ol.price_american < -300 THEN 1
        WHEN ol.price_american < -200 THEN 2
        WHEN ol.price_american < -150 THEN 3
        WHEN ol.price_american < -100 THEN 4
        WHEN ol.price_american = -110 THEN 5
        WHEN ol.price_american > -110 AND ol.price_american < 0 THEN 6
        WHEN ol.price_american > 0 AND ol.price_american < 150 THEN 7
        WHEN ol.price_american < 200 THEN 8
        WHEN ol.price_american < 300 THEN 9
        ELSE 10
    END;

-- =========================================================
-- 10. GAMES WITH MISSING ODDS
-- =========================================================

SELECT 
    g.week,
    g.game_id,
    at.abbrev || ' @ ' || ht.abbrev AS matchup,
    g.game_datetime_utc AS kickoff,
    'No odds data' AS issue
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