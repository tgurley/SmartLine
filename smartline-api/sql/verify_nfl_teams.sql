-- =========================================================
-- NFL Team ETL Verification
-- =========================================================
-- Run these queries to verify everything loaded correctly
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'NFL Team ETL Verification'
\echo '=========================================='
\echo ''

-- =========================================================
-- 1. TEAM COUNT
-- =========================================================

\echo '1. Team Count:'
SELECT 
    'NFL Teams' as category,
    COUNT(*) as count
FROM team 
WHERE sport_id = 1;

\echo ''

-- =========================================================
-- 2. TEAMS WITH ALL FIELDS
-- =========================================================

\echo '2. Sample Teams (First 5):'
SELECT 
    team_id,
    name,
    abbrev,
    city,
    established,
    CASE WHEN logo_url IS NOT NULL THEN 'Yes' ELSE 'No' END as has_logo
FROM team 
WHERE sport_id = 1
ORDER BY name
LIMIT 5;

\echo ''

-- =========================================================
-- 3. NFL EXTENSIONS CHECK
-- =========================================================

\echo '3. NFL Extension Data:'
SELECT 
    'Teams with coach data' as metric,
    COUNT(*) as count
FROM nfl_team_data 
WHERE head_coach IS NOT NULL
UNION ALL
SELECT 
    'Teams with owner data',
    COUNT(*)
FROM nfl_team_data 
WHERE team_owner IS NOT NULL
UNION ALL
SELECT 
    'Total extension records',
    COUNT(*)
FROM nfl_team_data;

\echo ''

-- =========================================================
-- 4. VENUE DATA CHECK
-- =========================================================

\echo '4. Venue Data:'
SELECT 
    COUNT(*) as total_venues,
    COUNT(CASE WHEN state_province IS NOT NULL THEN 1 END) as venues_with_state,
    COUNT(CASE WHEN capacity IS NOT NULL THEN 1 END) as venues_with_capacity,
    COUNT(CASE WHEN surface_type IS NOT NULL THEN 1 END) as venues_with_surface
FROM venue v
WHERE EXISTS (
    SELECT 1 FROM team t 
    WHERE t.venue_id = v.venue_id 
    AND t.sport_id = 1
);

\echo ''

-- =========================================================
-- 5. TEAMS WITH VENUES
-- =========================================================

\echo '5. Teams Linked to Venues:'
SELECT 
    COUNT(*) as teams_with_venues
FROM team 
WHERE sport_id = 1 
  AND venue_id IS NOT NULL;

\echo ''

-- =========================================================
-- 6. SAMPLE COMPLETE DATA
-- =========================================================

\echo '6. Sample Complete Records (3 teams with all data):'
SELECT 
    t.name as team_name,
    t.city as team_city,
    nfl.head_coach,
    nfl.team_owner,
    v.name as venue_name,
    v.city as venue_city,
    v.capacity
FROM team t
LEFT JOIN nfl_team_data nfl ON t.team_id = nfl.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 1
ORDER BY t.name
LIMIT 3;

\echo ''

-- =========================================================
-- 7. DATA QUALITY CHECKS
-- =========================================================

\echo '7. Data Quality:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team 
WHERE sport_id = 1 AND city IS NULL
UNION ALL
SELECT 
    'Teams missing abbrev',
    COUNT(*)
FROM team 
WHERE sport_id = 1 AND abbrev IS NULL
UNION ALL
SELECT 
    'Teams missing logo',
    COUNT(*)
FROM team 
WHERE sport_id = 1 AND logo_url IS NULL
UNION ALL
SELECT 
    'Teams missing venue',
    COUNT(*)
FROM team 
WHERE sport_id = 1 AND venue_id IS NULL;

\echo ''

-- =========================================================
-- 8. VENUE QUALITY CHECK
-- =========================================================

\echo '8. Venues Created (Sample 5):'
SELECT 
    v.name as venue_name,
    v.city as venue_city,
    v.state_province,
    t.name as team_name
FROM venue v
JOIN team t ON v.venue_id = t.venue_id
WHERE t.sport_id = 1
ORDER BY v.name
LIMIT 5;

\echo ''

-- =========================================================
-- 9. COMPLETE VIEW TEST
-- =========================================================

\echo '9. Using v_nfl_teams View (Sample 3):'
SELECT 
    name,
    city,
    head_coach,
    venue_name,
    venue_capacity
FROM v_nfl_teams
ORDER BY name
LIMIT 3;

\echo ''

-- =========================================================
-- 10. SUMMARY STATISTICS
-- =========================================================

\echo '10. Summary Statistics:'
SELECT 
    'Total NFL Teams' as metric,
    COUNT(*)::text as value
FROM team WHERE sport_id = 1
UNION ALL
SELECT 
    'Teams with Extensions',
    COUNT(*)::text
FROM nfl_team_data
UNION ALL
SELECT 
    'Teams with Venues',
    COUNT(*)::text
FROM team WHERE sport_id = 1 AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Unique Venues',
    COUNT(DISTINCT venue_id)::text
FROM team WHERE sport_id = 1 AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Teams with Coach',
    COUNT(*)::text
FROM nfl_team_data WHERE head_coach IS NOT NULL
UNION ALL
SELECT 
    'Teams with Owner',
    COUNT(*)::text
FROM nfl_team_data WHERE team_owner IS NOT NULL;

\echo ''
\echo '=========================================='
\echo 'Verification Complete!'
\echo '=========================================='
\echo ''
\echo 'Expected Results:'
\echo '  - 32 NFL teams'
\echo '  - 32 extension records'
\echo '  - ~30 venues (some teams share stadiums)'
\echo '  - All teams should have coach/owner data'
\echo '  - Most teams should have venue_id'
\echo ''
\echo 'If numbers look good, ready to move to next league!'
\echo ''

-- =========================================================
-- BONUS: QUICK ISSUE FINDER
-- =========================================================

\echo 'Issues to Review (if any):'

-- Teams without coach
SELECT 'Missing Coach: ' || name 
FROM team t
LEFT JOIN nfl_team_data nfl ON t.team_id = nfl.team_id
WHERE t.sport_id = 1 
  AND (nfl.head_coach IS NULL OR nfl.head_coach = '');

-- Teams without owner  
SELECT 'Missing Owner: ' || name 
FROM team t
LEFT JOIN nfl_team_data nfl ON t.team_id = nfl.team_id
WHERE t.sport_id = 1 
  AND (nfl.team_owner IS NULL OR nfl.team_owner = '');

-- Teams without venue
SELECT 'Missing Venue: ' || name 
FROM team 
WHERE sport_id = 1 
  AND venue_id IS NULL;

\echo ''
\echo 'If no issues printed above, all data is complete!'
\echo ''
