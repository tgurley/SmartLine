-- Player Table Schema Fix
-- ========================
-- Issue: external_player_id is UNIQUE globally, but should be UNIQUE per sport
-- Same issue we had with team.external_team_key

-- Problem:
-- NBA player ID #1 and NFL player ID #1 are DIFFERENT players
-- But current constraint prevents both from existing

-- Current constraint:
-- CONSTRAINT player_external_player_id_key UNIQUE (external_player_id)

-- Needed constraint:
-- CONSTRAINT player_external_player_id_sport_id_key UNIQUE (external_player_id, sport_id)

-- ========================================
-- FIX: Update player table constraint
-- ========================================

BEGIN;

-- 1. Drop the old single-column unique constraint
ALTER TABLE player 
DROP CONSTRAINT IF EXISTS player_external_player_id_key;

-- 2. Add the new composite unique constraint (external_player_id + sport_id)
ALTER TABLE player 
ADD CONSTRAINT player_external_player_id_sport_id_key 
UNIQUE (external_player_id, sport_id);

-- 3. Verify the change
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint
WHERE conrelid = 'player'::regclass
  AND conname LIKE '%external%';

COMMIT;

-- ========================================
-- Verification Queries
-- ========================================

-- Should return the new constraint:
-- player_external_player_id_sport_id_key | UNIQUE (external_player_id, sport_id)

-- Test: This should now work (same external_player_id across different sports)
-- Currently would fail, but after fix will work:
/*
INSERT INTO player (external_player_id, sport_id, full_name, created_at, updated_at)
VALUES 
    (1, 1, 'NFL Player ID 1', NOW(), NOW()),  -- sport_id 1 = NFL
    (1, 2, 'NBA Player ID 1', NOW(), NOW());  -- sport_id 2 = NBA (different player!)
*/
