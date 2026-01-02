-- =========================================================
-- VERIFY PARLAYS TABLE SCHEMA
-- =========================================================
-- Run this to check if your table matches what the endpoints expect
-- Copy the entire script and run it in Railway

-- 1. Check if parlays table exists and show its structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'parlays'
ORDER BY ordinal_position;

-- Expected output should show these columns:
-- parlay_id (integer, NOT NULL, auto-increment)
-- user_id (integer, NOT NULL, default 1)
-- account_id (integer, nullable) ← CHECK THIS ONE
-- total_legs (integer, NOT NULL)
-- combined_odds_american (integer, NOT NULL)
-- stake_amount (numeric, NOT NULL)
-- potential_payout (numeric)
-- actual_payout (numeric)
-- profit_loss (numeric)
-- sport_mix (varchar)
-- status (varchar, NOT NULL, default 'pending')
-- placed_at (timestamp, NOT NULL, default NOW())
-- settled_at (timestamp)
-- notes (text)
-- created_at (timestamp, default NOW())
-- updated_at (timestamp, default NOW())

-- 2. Check constraints
SELECT
    con.conname AS constraint_name,
    con.contype AS constraint_type,
    pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
WHERE rel.relname = 'parlays';

-- 3. Check if foreign key to bankroll_accounts exists
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'parlays'
    AND tc.constraint_type = 'FOREIGN KEY';

-- 4. Check if view exists
SELECT EXISTS (
    SELECT FROM information_schema.views 
    WHERE table_name = 'v_parlay_details'
) AS view_exists;

-- 5. Test INSERT to see exact error
-- This will fail but show us the exact error message
DO $$
BEGIN
    INSERT INTO parlays (
        user_id, 
        account_id, 
        total_legs, 
        combined_odds_american,
        stake_amount, 
        potential_payout, 
        sport_mix
    )
    VALUES (
        1,      -- user_id
        1,      -- account_id ← THIS IS THE SUSPECT
        2,      -- total_legs
        264,    -- combined_odds_american
        100.00, -- stake_amount
        364.00, -- potential_payout
        'NFL'   -- sport_mix
    );
    
    -- If it worked, roll it back
    RAISE EXCEPTION 'Test insert successful - rolling back';
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Error: %', SQLERRM;
END $$;

-- 6. If account_id is the problem, check bankroll_accounts
SELECT 
    account_id,
    bookmaker_name,
    current_balance
FROM bankroll_accounts
WHERE user_id = 1
LIMIT 5;

-- If this returns no rows, that's your problem!
-- The account_id you're trying to use doesn't exist

-- 7. Check what account_id your frontend is sending
-- Look at the error logs or add this to your endpoint:
-- print(f"Received account_id: {parlay.account_id}")
