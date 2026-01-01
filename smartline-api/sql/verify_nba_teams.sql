-- =========================================================
-- NBA Team Verification
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'NBA Team Verification'
\echo '=========================================='
\echo ''

-- 1. Team Count
\echo '1. NBA Team Count:'
SELECT COUNT(*) as nba_teams FROM team WHERE sport_id = 3;

\echo ''

-- 2. Conference Breakdown
\echo '2. Conference Breakdown:'
SELECT 
    nba.conference,
    COUNT(*) as teams
FROM team t
JOIN nba_team_data nba ON t.team_id = nba.team_id
WHERE t.sport_id = 3
GROUP BY nba.conference
ORDER BY nba.conference;

\echo ''

-- 3. Division Breakdown
\echo '3. Division Breakdown:'
SELECT 
    nba.conference,
    nba.division,
    COUNT(*) as teams
FROM team t
JOIN nba_team_data nba ON t.team_id = nba.team_id
WHERE t.sport_id = 3
GROUP BY nba.conference, nba.division
ORDER BY nba.conference, nba.division;

\echo ''

-- 4. Sample Teams
\echo '4. Sample Teams (5 from each conference):'
SELECT 
    t.name,
    t.city,
    nba.conference,
    nba.division,
    nba.nickname
FROM team t
JOIN nba_team_data nba ON t.team_id = nba.team_id
WHERE t.sport_id = 3
ORDER BY nba.conference, t.name
LIMIT 10;

\echo ''

-- 5. Data Quality
\echo '5. Data Quality Check:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 3 AND city IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 3 AND logo_url IS NULL
UNION ALL
SELECT 'Extensions missing conference', COUNT(*)
FROM nba_team_data WHERE conference IS NULL
UNION ALL
SELECT 'Extensions missing division', COUNT(*)
FROM nba_team_data WHERE division IS NULL;

\echo ''

-- 6. View Test
\echo '6. View Test (v_nba_teams):'
SELECT 
    name,
    city,
    conference,
    division,
    nickname
FROM v_nba_teams
LIMIT 5;

\echo ''
\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 30 teams total'
\echo '  - 15 East, 15 West'
\echo '  - 6 divisions (3 per conference)'
\echo '  - All teams have conference/division'
\echo '=========================================='
\echo ''
