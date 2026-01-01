-- =========================================================
-- Quick Fix: Make state_province Nullable
-- =========================================================
-- Run this to fix the state_province NOT NULL constraint
-- =========================================================

BEGIN;

\echo 'Making state_province nullable...'

-- Make state_province nullable (not all venues have states)
ALTER TABLE venue ALTER COLUMN state_province DROP NOT NULL;

\echo 'Checking constraint...'
SELECT 
    column_name, 
    is_nullable,
    data_type 
FROM information_schema.columns 
WHERE table_name = 'venue' 
  AND column_name = 'state_province';

COMMIT;

\echo ''
\echo 'Fix complete! state_province is now nullable.'
\echo 'Re-run the team ETL now.'
