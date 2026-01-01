-- =========================================================
-- Cleanup Failed NBA Team Inserts
-- =========================================================
-- This removes any partially inserted NBA teams that failed
-- due to missing league_id
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Cleaning Up Failed NBA Inserts'
\echo '=========================================='
\echo ''

-- Check what NBA teams exist (if any)
\echo 'Current NBA teams (should have league_id = NULL):'
SELECT team_id, name, league_id, sport_id
FROM team
WHERE sport_id = 3;

\echo ''
\echo 'Deleting failed NBA team records...'

-- Delete NBA teams that have NULL league_id (failed inserts)
DELETE FROM team
WHERE sport_id = 3 
  AND league_id IS NULL;

\echo ''
\echo 'Cleanup complete!'
\echo ''

-- Verify cleanup
SELECT COUNT(*) as remaining_nba_teams
FROM team
WHERE sport_id = 3;

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Ready to re-run NBA ETL'
\echo '=========================================='
\echo ''
\echo 'Next steps:'
\echo '1. Verify leagues exist: SELECT * FROM league WHERE sport_id = 3;'
\echo '2. Re-run ETL: python team_etl.py --sport NBA --season 2024 --all'
\echo ''
