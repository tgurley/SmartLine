-- =========================================================
-- NHL Team Verification
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'NHL Team Verification'
\echo '=========================================='
\echo ''

-- 1. Team Count
\echo '1. NHL Team Count:'
SELECT COUNT(*) as nhl_teams FROM team WHERE sport_id = 6;

\echo ''

-- 2. Conference Breakdown
\echo '2. Conference Breakdown:'
SELECT 
    nhl.conference,
    COUNT(*) as teams
FROM team t
LEFT JOIN nhl_team_data nhl ON t.team_id = nhl.team_id
WHERE t.sport_id = 6
GROUP BY nhl.conference
ORDER BY nhl.conference;

\echo ''

-- 3. Division Breakdown
\echo '3. Division Breakdown:'
SELECT 
    nhl.conference,
    nhl.division,
    COUNT(*) as teams
FROM team t
LEFT JOIN nhl_team_data nhl ON t.team_id = nhl.team_id
WHERE t.sport_id = 6
GROUP BY nhl.conference, nhl.division
ORDER BY nhl.conference, nhl.division;

\echo ''

-- 4. Country Breakdown
\echo '4. Teams by Country:'
SELECT 
    country_code,
    country_name,
    COUNT(*) as teams
FROM team
WHERE sport_id = 6
GROUP BY country_code, country_name
ORDER BY teams DESC;

\echo ''

-- 5. Canadian Teams
\echo '5. Canadian Teams (should be 7):'
SELECT 
    name,
    city,
    abbrev
FROM team
WHERE sport_id = 6 AND country_code = 'CA'
ORDER BY name;

\echo ''

-- 6. Abbreviation Check
\echo '6. Abbreviation Length:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 6
GROUP BY LENGTH(abbrev);

\echo ''

-- 7. Duplicate Abbreviations Check
\echo '7. Duplicate Abbreviations:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as teams
FROM team
WHERE sport_id = 6
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'

\echo ''

-- 8. Colorado vs Columbus (should both exist)
\echo '8. Colorado vs Columbus (conflict test):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 6
  AND (name LIKE '%Colorado%' OR name LIKE '%Columbus%')
ORDER BY name;

\echo ''

-- 9. Extension Data
\echo '9. NHL Extension Data (conference/division/colors):'
SELECT 
    'Teams with conference' as metric,
    COUNT(*) as count
FROM nhl_team_data WHERE conference IS NOT NULL
UNION ALL
SELECT 'Teams with division', COUNT(*)
FROM nhl_team_data WHERE division IS NOT NULL
UNION ALL
SELECT 'Teams with colors', COUNT(*)
FROM nhl_team_data WHERE colors IS NOT NULL
UNION ALL
SELECT 'Total extension records', COUNT(*)
FROM nhl_team_data;

\echo ''

-- 10. Venues
\echo '10. NHL Venues:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 6 AND venue_id IS NOT NULL;

\echo ''

-- 11. Data Quality
\echo '11. Data Quality:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 6 AND city IS NULL
UNION ALL
SELECT 'Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 6 AND abbrev IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 6 AND logo_url IS NULL
UNION ALL
SELECT 'Teams missing country', COUNT(*) 
FROM team WHERE sport_id = 6 AND country_code IS NULL;

\echo ''

-- 12. Famous Teams
\echo '12. Famous Teams Check:'
SELECT name, abbrev, city, country_code
FROM team
WHERE sport_id = 6
  AND name IN (
    'Toronto Maple Leafs',
    'Montreal Canadiens',
    'Boston Bruins',
    'Chicago Blackhawks',
    'Detroit Red Wings'
  )
ORDER BY name;

\echo ''

-- 13. Sample Complete Records
\echo '13. Sample Teams with Full Data (5 teams):'
SELECT 
    t.name,
    t.abbrev,
    t.city,
    t.country_code,
    nhl.conference,
    nhl.division,
    v.name as venue_name
FROM team t
LEFT JOIN nhl_team_data nhl ON t.team_id = nhl.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 6
ORDER BY t.name
LIMIT 5;

\echo ''

-- 14. View Test
\echo '14. View Test (v_nhl_teams):'
SELECT 
    name,
    city,
    conference,
    division,
    venue_name
FROM v_nhl_teams
LIMIT 5;

\echo ''

\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 32 teams total'
\echo '  - ~25 US teams, 7 Canadian teams'
\echo '  - Eastern Conference: ~16 teams'
\echo '  - Western Conference: ~16 teams'
\echo '  - 4 divisions (Atlantic, Metropolitan, Central, Pacific)'
\echo '  - All abbreviations unique (4 chars)'
\echo '  - Colorado (CAVA) and Columbus (CBLU) both exist'
\echo '=========================================='
\echo ''

-- BONUS: All Abbreviations
\echo 'BONUS: All NHL Abbreviations:'
SELECT abbrev, name, city
FROM team
WHERE sport_id = 6
ORDER BY abbrev;

\echo ''
\echo 'If 32 teams with unique abbrevs, NHL is complete!'
\echo ''
