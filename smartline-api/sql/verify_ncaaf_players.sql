-- NCAAF Player ETL Validation Script
-- =====================================
-- Validates the ~15,500 NCAAF players that were just loaded

-- ===========================================
-- 1. OVERALL SUMMARY
-- ===========================================
SELECT 
    '=== NCAAF PLAYER LOAD SUMMARY ===' as section;

SELECT 
    COUNT(*) as total_ncaaf_players,
    COUNT(DISTINCT team_id) as teams_with_players,
    MIN(created_at) as first_player_created,
    MAX(created_at) as last_player_created,
    MIN(updated_at) as oldest_update,
    MAX(updated_at) as newest_update
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF');

-- Expected: ~15,500 players

-- ===========================================
-- 2. COMPARE TO TEAM COUNT
-- ===========================================
SELECT 
    '=== TEAM COVERAGE ===' as section;

SELECT 
    COUNT(DISTINCT t.team_id) as total_ncaaf_teams,
    COUNT(DISTINCT p.team_id) as teams_with_players,
    COUNT(DISTINCT t.team_id) - COUNT(DISTINCT p.team_id) as teams_without_players,
    ROUND(100.0 * COUNT(DISTINCT p.team_id) / COUNT(DISTINCT t.team_id), 1) as coverage_pct
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id 
    AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF');

-- Expected: ~706 total teams, ~260-280 with players, ~40% coverage

-- ===========================================
-- 3. PLAYERS PER TEAM DISTRIBUTION
-- ===========================================
SELECT 
    '=== PLAYERS PER TEAM ===' as section;

SELECT 
    t.name as team_name,
    t.abbrev,
    COUNT(p.player_id) as player_count
FROM team t
JOIN player p ON t.team_id = p.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
GROUP BY t.team_id, t.name, t.abbrev
ORDER BY player_count DESC
LIMIT 20;

-- Expected: Major teams have 60-80 players each

-- ===========================================
-- 4. TEAMS WITHOUT PLAYERS (Sample)
-- ===========================================
SELECT 
    '=== TEAMS WITHOUT PLAYERS (Sample) ===' as section;

SELECT 
    t.name as team_name,
    t.abbrev,
    t.external_team_key
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id 
    AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
  AND p.player_id IS NULL
ORDER BY t.name
LIMIT 30;

-- Expected: Mostly smaller Division II/III schools

-- ===========================================
-- 5. POSITION DISTRIBUTION
-- ===========================================
SELECT 
    '=== POSITION DISTRIBUTION ===' as section;

SELECT 
    position,
    COUNT(*) as player_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
  AND position IS NOT NULL
GROUP BY position
ORDER BY player_count DESC;

-- Expected positions: QB, RB, WR, TE, OL, DL, LB, DB, K, P, LS

-- ===========================================
-- 6. PLAYER GROUP DISTRIBUTION
-- ===========================================
SELECT 
    '=== PLAYER GROUP DISTRIBUTION ===' as section;

SELECT 
    player_group,
    COUNT(*) as player_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
  AND player_group IS NOT NULL
GROUP BY player_group
ORDER BY player_count DESC;

-- Expected: Offense, Defense, Special Teams

-- ===========================================
-- 7. DATA COMPLETENESS
-- ===========================================
SELECT 
    '=== DATA COMPLETENESS ===' as section;

SELECT 
    COUNT(*) as total_players,
    COUNT(position) as has_position,
    COUNT(jersey_number) as has_jersey,
    COUNT(height) as has_height,
    COUNT(weight) as has_weight,
    COUNT(age) as has_age,
    COUNT(college) as has_college,
    COUNT(experience_years) as has_experience,
    COUNT(player_group) as has_group,
    ROUND(100.0 * COUNT(position) / COUNT(*), 1) as position_pct,
    ROUND(100.0 * COUNT(jersey_number) / COUNT(*), 1) as jersey_pct,
    ROUND(100.0 * COUNT(height) / COUNT(*), 1) as height_pct,
    ROUND(100.0 * COUNT(weight) / COUNT(*), 1) as weight_pct
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF');

-- Expected: Good position/jersey coverage, variable height/weight

-- ===========================================
-- 8. SAMPLE PLAYERS FROM MAJOR PROGRAMS
-- ===========================================
SELECT 
    '=== SAMPLE: ALABAMA CRIMSON TIDE ===' as section;

SELECT 
    p.full_name,
    p.position,
    p.player_group,
    p.jersey_number,
    p.height,
    p.weight,
    p.age
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.name = 'Alabama'
  AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
ORDER BY p.position, p.jersey_number
LIMIT 20;

-- ===========================================
SELECT 
    '=== SAMPLE: OHIO STATE BUCKEYES ===' as section;

SELECT 
    p.full_name,
    p.position,
    p.player_group,
    p.jersey_number,
    p.height,
    p.weight
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.name = 'Ohio State'
  AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
ORDER BY p.position, p.jersey_number
LIMIT 20;

-- ===========================================
SELECT 
    '=== SAMPLE: GEORGIA BULLDOGS ===' as section;

SELECT 
    p.full_name,
    p.position,
    p.player_group,
    p.jersey_number,
    p.height,
    p.weight,
    p.age
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.name = 'Georgia'
  AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
ORDER BY p.position, p.jersey_number
LIMIT 20;

-- ===========================================
-- 9. CHECK FOR DUPLICATES (Should be ZERO)
-- ===========================================
SELECT 
    '=== DUPLICATE CHECK ===' as section;

SELECT 
    external_player_id,
    sport_id,
    COUNT(*) as duplicate_count,
    STRING_AGG(full_name, ', ') as player_names
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
GROUP BY external_player_id, sport_id
HAVING COUNT(*) > 1;

-- Expected: 0 rows (no duplicates)

-- ===========================================
-- 10. PLAYERS BY CONFERENCE (If team has conference data)
-- ===========================================
SELECT 
    '=== PLAYERS BY CONFERENCE (Top 10) ===' as section;

-- Note: This requires that teams have conference data
-- If not available, this will show NULL conferences
SELECT 
    COALESCE(t.conference, 'Unknown') as conference,
    COUNT(p.player_id) as player_count,
    COUNT(DISTINCT t.team_id) as team_count,
    ROUND(AVG(CASE WHEN p.player_id IS NOT NULL THEN 1.0 ELSE 0 END), 1) as avg_players_per_team
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id 
    AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
GROUP BY t.conference
ORDER BY player_count DESC
LIMIT 10;

-- ===========================================
-- 11. RECENTLY CREATED PLAYERS (Last 100)
-- ===========================================
SELECT 
    '=== RECENTLY LOADED PLAYERS ===' as section;

SELECT 
    p.full_name,
    t.name as team_name,
    p.position,
    p.jersey_number,
    p.created_at
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
ORDER BY p.created_at DESC
LIMIT 20;

-- ===========================================
-- 12. AVERAGE ROSTER SIZE BY DIVISION
-- ===========================================
SELECT 
    '=== AVERAGE ROSTER SIZE ===' as section;

WITH team_player_counts AS (
    SELECT 
        t.team_id,
        t.name,
        COUNT(p.player_id) as player_count
    FROM team t
    LEFT JOIN player p ON t.team_id = p.team_id 
        AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
    WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
    GROUP BY t.team_id, t.name
)
SELECT 
    COUNT(*) as total_teams,
    COUNT(*) FILTER (WHERE player_count > 0) as teams_with_players,
    ROUND(AVG(player_count), 1) as avg_players_per_team,
    MIN(player_count) as min_roster,
    MAX(player_count) as max_roster,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY player_count) as median_roster
FROM team_player_counts;

-- ===========================================
-- 13. QUICK HEALTH CHECK
-- ===========================================
SELECT 
    '=== HEALTH CHECK ===' as section;

SELECT 
    'Total NCAAF Players' as metric,
    COUNT(*)::text as value
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')

UNION ALL

SELECT 
    'Players with Position',
    COUNT(*)::text
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
  AND position IS NOT NULL

UNION ALL

SELECT 
    'Players with Jersey Number',
    COUNT(*)::text
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')
  AND jersey_number IS NOT NULL

UNION ALL

SELECT 
    'Teams with Players',
    COUNT(DISTINCT team_id)::text
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF')

UNION ALL

SELECT 
    'Unique External Player IDs',
    COUNT(DISTINCT external_player_id)::text
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NCAAF');

-- ===========================================
-- 14. FINAL SUMMARY - ALL SPORTS
-- ===========================================
SELECT 
    '=== GRAND TOTAL: ALL SPORTS ===' as section;

SELECT 
    st.sport_code,
    st.sport_name,
    COUNT(p.player_id) as player_count,
    COUNT(DISTINCT p.team_id) as teams_with_players
FROM sport_type st
LEFT JOIN player p ON st.sport_id = p.sport_id
GROUP BY st.sport_id, st.sport_code, st.sport_name
ORDER BY player_count DESC;

-- Expected total now: ~21,000 players
-- (627 NBA + 4,011 Soccer + 15,500 NCAAF + any NFL if loaded)

-- ===========================================
-- END OF VALIDATION
-- ===========================================
