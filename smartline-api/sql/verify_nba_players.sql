-- Verification Script: NBA Player ETL
-- =====================================

-- 1. Check existing NBA players
SELECT 
    COUNT(*) as total_players,
    COUNT(DISTINCT team_id) as teams_with_players,
    MIN(updated_at) as oldest_update,
    MAX(updated_at) as newest_update
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA');

-- 2. Sample NBA players
SELECT 
    p.player_id,
    p.external_player_id,
    p.full_name,
    p.position,
    t.name as team_name,
    p.jersey_number,
    p.height,
    p.weight,
    p.college,
    p.experience_years
FROM player p
LEFT JOIN team t ON p.team_id = t.team_id
WHERE p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA')
ORDER BY p.full_name
LIMIT 20;

-- 3. Players by team
SELECT 
    t.name as team_name,
    t.abbrev,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id 
    AND p.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA')
WHERE t.sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA')
GROUP BY t.team_id, t.name, t.abbrev
ORDER BY player_count DESC;

-- 4. Position distribution (should be PG, SG, SF, PF, C, F, G, F-C, etc.)
SELECT 
    position,
    COUNT(*) as player_count
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA')
GROUP BY position
ORDER BY player_count DESC;

-- 5. Data completeness check
SELECT 
    COUNT(*) as total,
    COUNT(jersey_number) as has_jersey,
    COUNT(height) as has_height,
    COUNT(weight) as has_weight,
    COUNT(college) as has_college,
    COUNT(experience_years) as has_experience
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA');

-- 6. Find duplicate external_player_ids (should be none)
SELECT 
    external_player_id,
    COUNT(*) as count
FROM player
WHERE sport_id = (SELECT sport_id FROM sport_type WHERE sport_code = 'NBA')
GROUP BY external_player_id
HAVING COUNT(*) > 1;
