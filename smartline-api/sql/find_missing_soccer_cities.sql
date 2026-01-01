-- =========================================================
-- Find and Fix Missing Soccer Cities
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'Finding Teams Missing Cities'
\echo '=========================================='
\echo ''

-- MLS teams without cities
\echo 'MLS teams missing cities:'
SELECT team_id, name, abbrev, country_code
FROM team
WHERE sport_id = 7 AND city IS NULL
ORDER BY name;

\echo ''

-- EPL teams without cities
\echo 'EPL teams missing cities:'
SELECT team_id, name, abbrev, country_code
FROM team
WHERE sport_id = 8 AND city IS NULL
ORDER BY name;

\echo ''

-- La Liga teams without cities
\echo 'La Liga teams missing cities:'
SELECT team_id, name, abbrev, country_code
FROM team
WHERE sport_id = 9 AND city IS NULL
ORDER BY name;

\echo ''

-- Teams with wrong country codes
\echo 'EPL teams with wrong country code (should be GB):'
SELECT team_id, name, country_code
FROM team
WHERE sport_id = 8 AND country_code != 'GB'
ORDER BY name;

\echo ''

\echo 'La Liga teams with wrong country code (should be ES):'
SELECT team_id, name, country_code
FROM team
WHERE sport_id = 9 AND country_code != 'ES'
ORDER BY name;

\echo ''
\echo 'Use the team names above to create targeted fixes.'
\echo ''
