-- =========================================================
-- MLB Team Verification
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'MLB Team Verification'
\echo '=========================================='
\echo ''

-- 1. Team Count
\echo '1. MLB Team Count:'
SELECT COUNT(*) as mlb_teams FROM team WHERE sport_id = 5;

\echo ''

-- 2. All Teams Listed
\echo '2. All MLB Teams:'
SELECT 
    team_id,
    name,
    abbrev,
    city
FROM team 
WHERE sport_id = 5
ORDER BY name;

\echo ''

-- 3. Abbreviation Length Check
\echo '3. Abbreviation Length Distribution:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 5
GROUP BY LENGTH(abbrev)
ORDER BY abbrev_length;

\echo ''

-- 4. Check for Duplicates
\echo '4. Duplicate Abbreviations Check:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as teams
FROM team
WHERE sport_id = 5
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'

\echo ''

-- 5. Data Quality
\echo '5. Data Quality Check:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 5 AND city IS NULL
UNION ALL
SELECT 'Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 5 AND abbrev IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 5 AND logo_url IS NULL
UNION ALL
SELECT 'Teams missing name', COUNT(*) 
FROM team WHERE sport_id = 5 AND name IS NULL;

\echo ''

-- 6. Sample Teams
\echo '6. Sample Teams (10 teams):'
SELECT 
    name,
    abbrev,
    city,
    CASE WHEN logo_url IS NOT NULL THEN 'Yes' ELSE 'No' END as has_logo
FROM team
WHERE sport_id = 5
ORDER BY name
LIMIT 10;

\echo ''

-- 7. MLB Extension Data
\echo '7. MLB Extension Data (league/division):'
SELECT COUNT(*) as teams_with_extensions FROM mlb_team_data;

\echo '(May be 0 if API doesnt provide league/division data - thats OK!)'

\echo ''

-- 8. Venues
\echo '8. MLB Venues Created:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 5 AND venue_id IS NOT NULL;

\echo ''

-- 9. Famous Teams Check
\echo '9. Famous Teams Check (verify these loaded):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 5
  AND name IN (
    'New York Yankees',
    'Boston Red Sox',
    'Los Angeles Dodgers',
    'Chicago Cubs',
    'San Francisco Giants'
  )
ORDER BY name;

\echo ''

-- 10. Conflicting Teams (Rangers/Rays)
\echo '10. Texas Rangers vs Tampa Bay Rays (should both exist):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 5
  AND (name LIKE '%Rangers%' OR name LIKE '%Rays%')
ORDER BY name;

\echo ''

\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 30 teams total'
\echo '  - All abbreviations unique'
\echo '  - Abbreviations 3-4 chars long'
\echo '  - No missing critical data'
\echo '  - Rangers (TRAN) and Rays (TRAY) both exist'
\echo '=========================================='
\echo ''

-- BONUS: Show all abbreviations to verify uniqueness
\echo 'BONUS: All 30 Abbreviations:'
SELECT abbrev, name
FROM team
WHERE sport_id = 5
ORDER BY abbrev;

\echo ''
\echo 'If 30 teams shown above with unique abbrevs, MLB is complete!'
\echo ''
