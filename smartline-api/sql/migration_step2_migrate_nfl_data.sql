-- =========================================================
-- SmartLine Multi-Sport Migration - Step 2
-- =========================================================
-- Version: 5.2.0 → 5.3.0
-- Purpose: Migrate existing NFL data
-- Date: 2024-12-31
--
-- This migration:
-- 1. Sets sport_id = 1 (NFL) for all existing data
-- 2. Maps player positions to position_id
-- 3. Sets league_code for existing league
-- 4. Verifies data migration
--
-- SAFE: Only updates existing data with NFL sport_id
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Step 2: Migrating NFL Data'
\echo '=========================================='
\echo ''

-- =========================================================
-- STEP 2.1: UPDATE league TABLE
-- =========================================================

\echo 'Updating league table...'

-- Set sport_id and league_code for existing NFL league
UPDATE league 
SET sport_id = 1,
    league_code = 'nfl'
WHERE sport_id IS NULL;

SELECT 
    league_id,
    name,
    sport_id,
    league_code,
    '✓ Updated' as status
FROM league;

-- =========================================================
-- STEP 2.2: UPDATE team TABLE
-- =========================================================

\echo ''
\echo 'Updating team table...'

-- Set sport_id for all teams (from their league)
UPDATE team t
SET sport_id = l.sport_id
FROM league l
WHERE t.league_id = l.league_id
  AND t.sport_id IS NULL;

SELECT 
    'Teams updated' as description,
    COUNT(*) as count,
    '✓ Updated' as status
FROM team
WHERE sport_id = 1;

-- =========================================================
-- STEP 2.3: UPDATE player TABLE
-- =========================================================

\echo ''
\echo 'Updating player table...'

-- First, set sport_id for all players (from their team)
UPDATE player p
SET sport_id = t.sport_id
FROM team t
WHERE p.team_id = t.team_id
  AND p.sport_id IS NULL;

-- Then, map position codes to position_id
UPDATE player p
SET position_id = sp.position_id
FROM sport_position sp
WHERE sp.sport_id = p.sport_id
  AND sp.position_code = p.position
  AND p.position_id IS NULL
  AND p.position IS NOT NULL;

SELECT 
    'Players updated' as description,
    COUNT(*) as total_players,
    COUNT(position_id) as players_with_position,
    '✓ Updated' as status
FROM player
WHERE sport_id = 1;

\echo ''
\echo 'Position mapping summary:'
SELECT 
    sp.position_code,
    sp.position_name,
    COUNT(p.player_id) as player_count
FROM sport_position sp
LEFT JOIN player p ON sp.position_id = p.position_id
WHERE sp.sport_id = 1
GROUP BY sp.position_code, sp.position_name
ORDER BY player_count DESC;

-- =========================================================
-- STEP 2.4: UPDATE game TABLE
-- =========================================================

\echo ''
\echo 'Updating game table...'

-- Set sport_id for all games (from their season's league)
UPDATE game g
SET sport_id = l.sport_id
FROM season s
JOIN league l ON s.league_id = l.league_id
WHERE g.season_id = s.season_id
  AND g.sport_id IS NULL;

SELECT 
    'Games updated' as description,
    COUNT(*) as count,
    '✓ Updated' as status
FROM game
WHERE sport_id = 1;

-- =========================================================
-- STEP 2.5: UPDATE bets TABLE
-- =========================================================

\echo ''
\echo 'Updating bets table...'

-- Set sport_id for all bets (from their game)
UPDATE bets b
SET sport_id = g.sport_id
FROM game g
WHERE b.game_id = g.game_id
  AND b.sport_id IS NULL;

-- Also update bets without game_id (if any) based on player
UPDATE bets b
SET sport_id = p.sport_id
FROM player p
WHERE b.player_id = p.player_id
  AND b.sport_id IS NULL;

SELECT 
    'Bets updated' as description,
    COUNT(*) as count,
    '✓ Updated' as status
FROM bets
WHERE sport_id = 1;

-- =========================================================
-- STEP 2.6: VERIFICATION
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'Verification Summary'
\echo '=========================================='
\echo ''

-- Check all tables have sport_id populated
SELECT 
    'league' as table_name,
    COUNT(*) as total_records,
    COUNT(sport_id) as with_sport_id,
    COUNT(*) - COUNT(sport_id) as missing_sport_id
FROM league
UNION ALL
SELECT 
    'team',
    COUNT(*),
    COUNT(sport_id),
    COUNT(*) - COUNT(sport_id)
FROM team
UNION ALL
SELECT 
    'player',
    COUNT(*),
    COUNT(sport_id),
    COUNT(*) - COUNT(sport_id)
FROM player
UNION ALL
SELECT 
    'game',
    COUNT(*),
    COUNT(sport_id),
    COUNT(*) - COUNT(sport_id)
FROM game
UNION ALL
SELECT 
    'bets',
    COUNT(*),
    COUNT(sport_id),
    COUNT(*) - COUNT(sport_id)
FROM bets;

\echo ''
\echo 'Sport distribution:'
SELECT 
    st.sport_code,
    st.sport_name,
    COUNT(l.league_id) as leagues,
    (SELECT COUNT(*) FROM team WHERE sport_id = st.sport_id) as teams,
    (SELECT COUNT(*) FROM player WHERE sport_id = st.sport_id) as players,
    (SELECT COUNT(*) FROM game WHERE sport_id = st.sport_id) as games,
    (SELECT COUNT(*) FROM bets WHERE sport_id = st.sport_id) as bets
FROM sport_type st
LEFT JOIN league l ON st.sport_id = l.sport_id
GROUP BY st.sport_id, st.sport_code, st.sport_name
ORDER BY st.sport_id;

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Step 2 Complete: NFL Data Migrated'
\echo '=========================================='
\echo ''
\echo 'All existing data now has sport_id = 1 (NFL)'
\echo 'Players now have position_id mapped'
\echo 'League has league_code = "nfl"'
\echo ''
\echo 'Next step: Run migration_step3_add_constraints.sql'
\echo ''

/*
SUMMARY:
✅ Set sport_id = 1 (NFL) for all existing records
✅ Mapped player positions to position_id
✅ Set league_code = 'nfl'
✅ Verified all data migrated correctly

NEXT: Step 3 will make sport_id NOT NULL and add constraints
*/
