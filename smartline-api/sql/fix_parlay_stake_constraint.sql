-- =========================================================
-- FIX: Allow 0 stake_amount for parlay legs
-- =========================================================

-- The issue: bets table has CHECK (stake_amount > 0)
-- But parlay legs should have stake_amount = 0 (only the parent parlay has stake)

-- SOLUTION: Change constraint to allow 0 stake for parlay legs

-- Step 1: Drop the old constraint
ALTER TABLE bets DROP CONSTRAINT IF EXISTS bets_stake_amount_check;

-- Step 2: Add new constraint that allows 0 for parlay legs, but requires > 0 for regular bets
ALTER TABLE bets ADD CONSTRAINT bets_stake_amount_check 
CHECK (
    (parlay_id IS NOT NULL AND stake_amount >= 0) OR  -- Parlay legs can be 0
    (parlay_id IS NULL AND stake_amount > 0)           -- Regular bets must be > 0
);

-- Verify the constraint was updated
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'bets'::regclass 
AND conname = 'bets_stake_amount_check';

-- Expected output:
-- bets_stake_amount_check | CHECK (((parlay_id IS NOT NULL AND stake_amount >= 0) OR (parlay_id IS NULL AND stake_amount > 0)))
