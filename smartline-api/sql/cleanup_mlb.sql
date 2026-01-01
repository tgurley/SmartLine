-- =========================================================
-- Cleanup Failed MLB Inserts
-- =========================================================

BEGIN;

\echo 'Cleaning up partial MLB data...'

-- Delete any MLB teams that were inserted
DELETE FROM team WHERE sport_id = 5;

\echo 'Cleanup complete!'

-- Verify
SELECT COUNT(*) as remaining_mlb_teams FROM team WHERE sport_id = 5;

COMMIT;

\echo ''
\echo 'Ready to re-run MLB ETL with fixed abbreviations'
\echo 'Run: python team_etl.py --sport MLB --season 2024 --all'
\echo ''
