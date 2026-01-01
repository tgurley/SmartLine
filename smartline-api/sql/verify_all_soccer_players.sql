-- ⚽ Soccer Player ETL Verification Script
-- ==========================================
-- Comprehensive verification for MLS, EPL, La Liga, Bundesliga, Serie A, Ligue 1, Champions League

-- ===========================================
-- 1. OVERVIEW: Total Players by Soccer League
-- ===========================================
SELECT 
    l.league_name,
    l.league_code,
    COUNT(p.player_id) as player_count,
    MIN(p.updated_at) as oldest_update,
    MAX(p.updated_at) as newest_update
FROM league l
JOIN team t ON l.league_id = t.league_id
JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'champions')
GROUP BY l.league_name, l.league_code
ORDER BY player_count DESC;

-- Expected Results:
-- Champions League: ~2,000 players (81 teams)
-- MLS: ~700 players (29 teams)
-- Serie A: ~600 players (20 teams)
-- EPL: ~500 players (20 teams)
-- La Liga: ~500 players (20 teams)
-- Ligue 1: ~500 players (19 teams)
-- Bundesliga: ~450 players (19 teams)

-- ===========================================
-- 2. PLAYERS PER TEAM: Check Distribution
-- ===========================================
-- All soccer leagues combined
SELECT 
    l.league_name,
    t.name as team_name,
    t.city,
    COUNT(p.player_id) as player_count
FROM league l
JOIN team t ON l.league_id = t.league_id
LEFT JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
GROUP BY l.league_name, t.name, t.city
ORDER BY l.league_name, player_count DESC;

-- Expected: 20-35 players per team (typical squad size)

-- ===========================================
-- 3. MLS SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== MLS VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    t.city,
    t.abbrev,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'mls')
GROUP BY t.team_id, t.name, t.city, t.abbrev
ORDER BY player_count DESC;

-- Sample MLS players
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    p.height,
    p.weight,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'mls')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 4. EPL SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== EPL VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    t.city,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'epl')
GROUP BY t.team_id, t.name, t.city
ORDER BY player_count DESC;

-- Sample EPL players (should include big names)
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    p.nationality,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'epl')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 5. LA LIGA SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== LA LIGA VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'la_liga')
GROUP BY t.team_id, t.name
ORDER BY player_count DESC;

-- Sample La Liga players
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'la_liga')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 6. BUNDESLIGA SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== BUNDESLIGA VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'bundesliga')
GROUP BY t.team_id, t.name
ORDER BY player_count DESC;

-- Sample Bundesliga players
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'bundesliga')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 7. SERIE A SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== SERIE A VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'serie_a')
GROUP BY t.team_id, t.name
ORDER BY player_count DESC;

-- Sample Serie A players
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'serie_a')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 8. LIGUE 1 SPECIFIC VERIFICATION
-- ===========================================
SELECT 
    '=== LIGUE 1 VERIFICATION ===' as section;

SELECT 
    t.name as team_name,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'ligue_1')
GROUP BY t.team_id, t.name
ORDER BY player_count DESC;

-- Sample Ligue 1 players
SELECT 
    p.full_name,
    p.position,
    p.jersey_number,
    p.age,
    t.name as team_name
FROM player p
JOIN team t ON p.team_id = t.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'ligue_1')
ORDER BY t.name, p.jersey_number
LIMIT 30;

-- ===========================================
-- 9. CHAMPIONS LEAGUE VERIFICATION
-- ===========================================
SELECT 
    '=== CHAMPIONS LEAGUE VERIFICATION ===' as section;

SELECT 
    COUNT(DISTINCT t.team_id) as unique_teams,
    COUNT(p.player_id) as total_players
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'champions');

-- Top teams by player count in Champions League
SELECT 
    t.name as team_name,
    COUNT(p.player_id) as player_count
FROM team t
LEFT JOIN player p ON t.team_id = p.team_id
WHERE t.league_id = (SELECT league_id FROM league WHERE league_code = 'champions')
GROUP BY t.team_id, t.name
ORDER BY player_count DESC
LIMIT 20;

-- ===========================================
-- 10. POSITION DISTRIBUTION (Soccer-Specific)
-- ===========================================
SELECT 
    '=== POSITION DISTRIBUTION ===' as section;

SELECT 
    l.league_name,
    p.position,
    COUNT(*) as player_count
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.position IS NOT NULL
GROUP BY l.league_name, p.position
ORDER BY l.league_name, player_count DESC;

-- Expected positions: Goalkeeper, Defender, Midfielder, Attacker, Forward
-- Or abbreviated: GK, DF, MF, FW, AT

-- Summary across all soccer
SELECT 
    p.position,
    COUNT(*) as total_count
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.position IS NOT NULL
GROUP BY p.position
ORDER BY total_count DESC;

-- ===========================================
-- 11. DATA COMPLETENESS CHECK
-- ===========================================
SELECT 
    '=== DATA COMPLETENESS ===' as section;

SELECT 
    l.league_name,
    COUNT(p.player_id) as total_players,
    COUNT(p.jersey_number) as has_jersey,
    COUNT(p.height) as has_height,
    COUNT(p.weight) as has_weight,
    COUNT(p.age) as has_age,
    COUNT(p.position) as has_position,
    COUNT(p.image_url) as has_image,
    ROUND(100.0 * COUNT(p.jersey_number) / COUNT(p.player_id), 1) as jersey_pct,
    ROUND(100.0 * COUNT(p.height) / COUNT(p.player_id), 1) as height_pct,
    ROUND(100.0 * COUNT(p.weight) / COUNT(p.player_id), 1) as weight_pct
FROM league l
JOIN team t ON l.league_id = t.league_id
JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'champions')
GROUP BY l.league_name
ORDER BY total_players DESC;

-- ===========================================
-- 12. HEIGHT/WEIGHT FORMAT CHECK (Soccer uses cm/kg)
-- ===========================================
SELECT 
    '=== HEIGHT/WEIGHT FORMAT ===' as section;

-- Sample heights (should be in cm format like "175 cm")
SELECT DISTINCT height
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.height IS NOT NULL
ORDER BY height
LIMIT 20;

-- Sample weights (should be in kg format like "68 kg")
SELECT DISTINCT weight
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.weight IS NOT NULL
ORDER BY weight
LIMIT 20;

-- ===========================================
-- 13. DUPLICATE CHECK (Should be ZERO)
-- ===========================================
SELECT 
    '=== DUPLICATE CHECK ===' as section;

-- Check for duplicate external_player_ids within same sport
SELECT 
    p.external_player_id,
    p.sport_id,
    COUNT(*) as duplicate_count,
    STRING_AGG(p.full_name, ', ') as player_names
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'champions')
GROUP BY p.external_player_id, p.sport_id
HAVING COUNT(*) > 1;

-- Expected: 0 rows (no duplicates)

-- ===========================================
-- 14. COLLEGE FIELD CHECK (Should be mostly NULL for soccer)
-- ===========================================
SELECT 
    '=== COLLEGE FIELD CHECK ===' as section;

-- Soccer players shouldn't have college (that's a US thing)
SELECT 
    COUNT(*) as total_soccer_players,
    COUNT(p.college) as has_college,
    ROUND(100.0 * COUNT(p.college) / COUNT(*), 1) as college_pct
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1');

-- Expected: Very low percentage (maybe some MLS players from US colleges)

-- ===========================================
-- 15. FAMOUS PLAYERS SPOT CHECK
-- ===========================================
SELECT 
    '=== FAMOUS PLAYERS SPOT CHECK ===' as section;

-- Search for some well-known players (if they're in the leagues)
-- This will vary by season/transfers
SELECT 
    p.full_name,
    t.name as team_name,
    l.league_name,
    p.position,
    p.jersey_number,
    p.age
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'mls')
  AND (
    p.full_name ILIKE '%Messi%' OR
    p.full_name ILIKE '%Ronaldo%' OR
    p.full_name ILIKE '%Mbappé%' OR
    p.full_name ILIKE '%Haaland%' OR
    p.full_name ILIKE '%Salah%' OR
    p.full_name ILIKE '%De Bruyne%' OR
    p.full_name ILIKE '%Vinicius%' OR
    p.full_name ILIKE '%Kane%'
  )
ORDER BY p.full_name;

-- ===========================================
-- 16. AGE DISTRIBUTION
-- ===========================================
SELECT 
    '=== AGE DISTRIBUTION ===' as section;

SELECT 
    l.league_name,
    MIN(p.age) as youngest,
    MAX(p.age) as oldest,
    ROUND(AVG(p.age), 1) as avg_age
FROM player p
JOIN team t ON p.team_id = t.team_id
JOIN league l ON t.league_id = l.league_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.age IS NOT NULL
GROUP BY l.league_name
ORDER BY avg_age DESC;

-- Expected: Ages typically 17-40, average around 25-27

-- ===========================================
-- 17. TEAMS WITH NO PLAYERS (Should be ZERO)
-- ===========================================
SELECT 
    '=== TEAMS WITHOUT PLAYERS ===' as section;

SELECT 
    l.league_name,
    t.name as team_name,
    t.city
FROM team t
JOIN league l ON t.league_id = l.league_id
LEFT JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1')
  AND p.player_id IS NULL
ORDER BY l.league_name, t.name;

-- Expected: 0 rows (all teams should have players)

-- ===========================================
-- 18. FINAL SUMMARY
-- ===========================================
SELECT 
    '=== FINAL SUMMARY ===' as section;

SELECT 
    COUNT(DISTINCT l.league_id) as leagues_loaded,
    COUNT(DISTINCT t.team_id) as teams_with_players,
    COUNT(DISTINCT p.player_id) as total_unique_players,
    COUNT(DISTINCT p.external_player_id) as total_unique_api_ids
FROM league l
JOIN team t ON l.league_id = t.league_id
JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'champions');

-- Expected:
-- leagues_loaded: 7 (MLS, EPL, La Liga, Bundesliga, Serie A, Ligue 1, Champions)
-- teams_with_players: ~200+ teams
-- total_unique_players: ~5,250 players
-- total_unique_api_ids: ~5,250 (should match player count)

-- ===========================================
-- END OF VERIFICATION SCRIPT
-- ===========================================

-- Quick one-liner to see everything:
SELECT 
    'SOCCER ETL SUCCESS!' as status,
    COUNT(DISTINCT l.league_id) || ' leagues' as leagues,
    COUNT(DISTINCT t.team_id) || ' teams' as teams,
    COUNT(p.player_id) || ' players' as players
FROM league l
JOIN team t ON l.league_id = t.league_id
JOIN player p ON t.team_id = p.team_id
WHERE l.league_code IN ('mls', 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1', 'champions');
