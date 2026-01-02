-- =========================================================
-- SIMPLE PARLAY TABLE CHECK & FIX
-- =========================================================

-- STEP 1: Check if account_id column exists and is correct type
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'parlays'
    AND column_name = 'account_id';

-- Expected: account_id | integer | YES

-- STEP 2: Check if foreign key constraint exists
SELECT constraint_name
FROM information_schema.table_constraints
WHERE table_name = 'parlays'
    AND constraint_type = 'FOREIGN KEY'
    AND constraint_name LIKE '%account%';

-- Expected: fk_parlays_account or similar

-- STEP 3: If account_id column is missing, add it:
-- ALTER TABLE parlays ADD COLUMN account_id INTEGER REFERENCES bankroll_accounts(account_id) ON DELETE SET NULL;

-- STEP 4: If account_id exists but no foreign key, add constraint:
-- ALTER TABLE parlays ADD CONSTRAINT fk_parlays_account FOREIGN KEY (account_id) REFERENCES bankroll_accounts(account_id) ON DELETE SET NULL;

-- STEP 5: Test if you can insert a row manually
INSERT INTO parlays (
    user_id,
    account_id,
    total_legs,
    combined_odds_american,
    stake_amount,
    potential_payout,
    sport_mix,
    status
)
VALUES (
    1,                  -- user_id
    1,                  -- account_id (make sure this exists in bankroll_accounts!)
    2,                  -- total_legs
    264,                -- combined_odds_american
    100.00,             -- stake_amount
    364.00,             -- potential_payout
    'NFL',              -- sport_mix
    'pending'           -- status
)
RETURNING *;

-- If this INSERT works, the table is fine.
-- If it fails, you'll see the exact error.

-- STEP 6: Clean up test data
DELETE FROM parlays WHERE total_legs = 2 AND stake_amount = 100.00;
