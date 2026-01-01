-- =========================================================
-- Fix Missing Soccer Cities (Targeted)
-- =========================================================
-- Fixes the specific teams that were missed
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Fixing Missing Soccer Cities'
\echo '=========================================='
\echo ''

-- =========================================================
-- MLS - Fix 6 Teams
-- =========================================================

\echo 'Fixing MLS teams...'

UPDATE team SET city = 'Atlanta', country_code = 'US', country_name = 'USA' 
WHERE team_id = 295;  -- Atlanta United FC

UPDATE team SET city = 'Austin', country_code = 'US', country_name = 'USA' 
WHERE team_id = 308;  -- Austin

UPDATE team SET city = 'Charlotte', country_code = 'US', country_name = 'USA' 
WHERE team_id = 309;  -- Charlotte

UPDATE team SET city = 'Frisco', country_code = 'US', country_name = 'USA' 
WHERE team_id = 284;  -- FC Dallas

UPDATE team SET city = 'Los Angeles', country_code = 'US', country_name = 'USA' 
WHERE team_id = 303;  -- Los Angeles FC (LAFC)

UPDATE team SET city = 'Los Angeles', country_code = 'US', country_name = 'USA' 
WHERE team_id = 292;  -- Los Angeles Galaxy

-- =========================================================
-- EPL - Fix 2 Teams + Country Codes
-- =========================================================

\echo 'Fixing EPL teams...'

UPDATE team SET city = 'Ipswich', country_code = 'GB', country_name = 'England' 
WHERE team_id = 328;  -- Ipswich

UPDATE team SET city = 'Leicester', country_code = 'GB', country_name = 'England' 
WHERE team_id = 320;  -- Leicester

-- =========================================================
-- LA LIGA - Fix 3 Teams + Country Codes
-- =========================================================

\echo 'Fixing La Liga teams...'

UPDATE team SET city = 'Barcelona', country_code = 'ES', country_name = 'Spain' 
WHERE team_id = 340;  -- Espanyol (RCD Espanyol - Barcelona based)

UPDATE team SET city = 'Leganes', country_code = 'ES', country_name = 'Spain' 
WHERE team_id = 338;  -- Leganes (CD Leganes - near Madrid)

UPDATE team SET city = 'Seville', country_code = 'ES', country_name = 'Spain' 
WHERE team_id = 343;  -- Real Betis (based in Seville)

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Verification'
\echo '=========================================='
\echo ''

-- Verify MLS
\echo 'MLS - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 7 AND city IS NOT NULL;

\echo ''

-- Verify EPL
\echo 'EPL - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 8 AND city IS NOT NULL;

\echo ''

\echo 'EPL - Country codes (all should be GB):'
SELECT country_code, COUNT(*) as teams
FROM team
WHERE sport_id = 8
GROUP BY country_code;

\echo ''

-- Verify La Liga
\echo 'La Liga - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 9 AND city IS NOT NULL;

\echo ''

\echo 'La Liga - Country codes (all should be ES):'
SELECT country_code, COUNT(*) as teams
FROM team
WHERE sport_id = 9
GROUP BY country_code;

\echo ''

\echo '=========================================='
\echo 'Fix Complete!'
\echo '=========================================='
\echo ''
\echo 'Expected results:'
\echo '  - MLS: 29 teams with cities'
\echo '  - EPL: 20 teams with cities (all GB)'
\echo '  - La Liga: 20 teams with cities (all ES)'
\echo ''
