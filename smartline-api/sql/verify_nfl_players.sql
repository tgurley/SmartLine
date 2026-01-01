-- Verification Script: NFL Player ETL Testing
-- =============================================
-- This script helps verify the player ETL functionality and test update detection

-- 1. Check existing 2023 NFL players in database
-- ===============================================
SELECT 
    COUNT(*) as total_players,
    COUNT(DISTINCT team_id) as teams_with_players,
    MIN(updated_at) as oldest_update,
    MAX(updated_at) as newest_update
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL');

-- 2. Sample of existing 2023 players
-- ===================================
SELECT 
    p.player_id,
    p.external_player_id,
    p.full_name,
    p.position,
    t.name as team_name,
    t.abbrev as team_abbrev,
    p.jersey_number,
    p.age,
    p.updated_at
FROM player p
LEFT JOIN team t ON p.team_id = t.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
ORDER BY p.full_name
LIMIT 20;

-- 3. Players by team (to verify team assignments)
-- ================================================
SELECT 
    t.name as team_name,
    t.abbrev,
    t.external_team_key,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id 
    AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
GROUP BY t.team_id, t.name, t.abbrev, t.external_team_key
ORDER BY player_count DESC;

-- 4. Check for position distribution
-- ===================================
SELECT 
    position,
    COUNT(*) as player_count
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
GROUP BY position
ORDER BY player_count DESC;

-- 5. Players with all data fields populated
-- ==========================================
SELECT 
    COUNT(*) as total,
    COUNT(jersey_number) as has_jersey,
    COUNT(height) as has_height,
    COUNT(weight) as has_weight,
    COUNT(age) as has_age,
    COUNT(college) as has_college,
    COUNT(experience_years) as has_experience,
    COUNT(salary) as has_salary,
    COUNT(image_url) as has_image
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL');

-- 6. Sample players from a specific team (e.g., Dallas Cowboys = external_team_key 6)
-- ====================================================================================
SELECT 
    p.external_player_id,
    p.full_name,
    p.position,
    p.jersey_number,
    p.height,
    p.weight,
    p.age,
    p.college,
    p.experience_years,
    p.player_group,
    p.updated_at
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.external_team_key = '6'  -- Dallas Cowboys
  AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
ORDER BY p.position, p.jersey_number;

-- 7. BEFORE UPDATE TEST: Save snapshot of specific players
-- =========================================================
-- This query shows data BEFORE running the 2024 ETL
-- Run this, then run the ETL, then run query #8 to see changes
CREATE TEMP TABLE player_snapshot_before AS
SELECT 
    p.player_id,
    p.external_player_id,
    p.full_name,
    p.position,
    p.team_id,
    t.name as team_name,
    p.jersey_number,
    p.age,
    p.experience_years,
    p.updated_at
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
  AND p.external_player_id IN (1, 2, 3, 4, 5, 10, 20, 50, 100);  -- Sample player IDs

SELECT * FROM player_snapshot_before ORDER BY external_player_id;

-- 8. AFTER UPDATE TEST: Compare with snapshot to see what changed
-- ================================================================
-- Run this AFTER running the 2024 ETL to see what was updated
SELECT 
    'BEFORE' as snapshot,
    * 
FROM player_snapshot_before
UNION ALL
SELECT 
    'AFTER' as snapshot,
    p.player_id,
    p.external_player_id,
    p.full_name,
    p.position,
    p.team_id,
    t.name as team_name,
    p.jersey_number,
    p.age,
    p.experience_years,
    p.updated_at
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
  AND p.external_player_id IN (1, 2, 3, 4, 5, 10, 20, 50, 100)
ORDER BY external_player_id, snapshot;

-- 9. Find players who changed teams (after running 2024 ETL)
-- ===========================================================
-- This identifies roster moves between seasons
WITH before_snapshot AS (
    SELECT player_id, external_player_id, full_name, team_id, updated_at
    FROM player_snapshot_before
)
SELECT 
    b.external_player_id,
    b.full_name,
    t1.name as old_team,
    t2.name as new_team,
    b.updated_at as old_update,
    p.updated_at as new_update
FROM before_snapshot b
JOIN player p ON b.player_id = p.player_id
LEFT JOIN team t1 ON b.team_id = t1.team_id
LEFT JOIN team t2 ON p.team_id = t2.team_id
WHERE b.team_id != p.team_id
ORDER BY b.full_name;

-- 10. ETL Statistics - Update vs Insert breakdown
-- ================================================
-- Run this query before and after ETL to see the difference
SELECT 
    DATE(updated_at) as update_date,
    COUNT(*) as players_updated_on_date
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NFL')
GROUP BY DATE(updated_at)
ORDER BY update_date DESC;
