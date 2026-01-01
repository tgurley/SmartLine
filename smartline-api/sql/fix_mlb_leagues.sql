-- =========================================================
-- Fix MLB Teams - Remove League Entries
-- =========================================================

BEGIN;

\echo 'Removing non-team entries from MLB...'

-- Delete "American League" and "National League" entries
DELETE FROM team 
WHERE sport_id = 5 
  AND name IN ('American League', 'National League');

\echo 'Removed league entries'
\echo ''

-- Verify count
\echo 'MLB team count after cleanup:'
SELECT COUNT(*) as mlb_teams FROM team WHERE sport_id = 5;

\echo ''
\echo 'Remaining teams:'
SELECT name FROM team WHERE sport_id = 5 ORDER BY name;

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Complete! Should now have 30 MLB teams'
\echo '=========================================='
\echo ''
