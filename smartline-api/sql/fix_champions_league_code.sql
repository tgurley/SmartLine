-- =========================================================
-- Fix Champions League Code
-- =========================================================
-- Change from 'champions_league' to 'champions' to match ETL
-- =========================================================

BEGIN;

\echo 'Updating Champions League code...'

UPDATE league 
SET league_code = 'champions'
WHERE league_id = 15;

\echo 'Champions League code updated!'

-- Verify
\echo ''
\echo 'Verifying Champions League:'
SELECT 
    league_id,
    name,
    sport_id,
    league_code
FROM league
WHERE league_id = 15;

COMMIT;

\echo ''
\echo 'Complete! Now re-run: python team_etl.py --sport CHAMPIONS --season 2024 --all'
\echo ''
