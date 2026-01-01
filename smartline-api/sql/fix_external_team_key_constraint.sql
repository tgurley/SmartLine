-- =========================================================
-- Fix external_team_key Unique Constraint
-- =========================================================
-- Problem: external_team_key is UNIQUE across ALL sports
-- Solution: Make it UNIQUE per sport (external_team_key + sport_id)
--
-- NFL team ID 1 = Raiders
-- NBA team ID 1 = Hawks  
-- Both should be allowed!
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Fixing external_team_key Constraint'
\echo '=========================================='
\echo ''

-- Drop the old constraint (UNIQUE on external_team_key alone)
\echo 'Dropping old constraint...'
ALTER TABLE team DROP CONSTRAINT IF EXISTS team_external_team_key_key;

-- Add new constraint (UNIQUE on external_team_key + sport_id)
\echo 'Adding new constraint (external_team_key + sport_id)...'
ALTER TABLE team 
    ADD CONSTRAINT team_external_team_key_sport_id_key 
    UNIQUE (external_team_key, sport_id);

-- Also add an index for performance
CREATE INDEX IF NOT EXISTS idx_team_external_key_sport 
    ON team(external_team_key, sport_id);

\echo ''
\echo 'Constraint fixed!'
\echo ''

-- Verify the new constraint
\echo 'New constraints on team table:'
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'team'::regclass
  AND conname LIKE '%external%';

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Fix Complete!'
\echo '=========================================='
\echo ''
\echo 'Now you can have:'
\echo '  - NFL team with external_team_key = 1'
\echo '  - NBA team with external_team_key = 1'
\echo '  - MLB team with external_team_key = 1'
\echo '  - etc.'
\echo ''
\echo 'Next step: Re-run NBA ETL'
\echo '  python team_etl.py --sport NBA --season 2024 --all'
\echo ''
