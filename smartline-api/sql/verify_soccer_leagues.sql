-- =========================================================
-- Soccer Leagues Verification (MLS, EPL, La Liga)
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'SOCCER LEAGUES VERIFICATION'
\echo '=========================================='
\echo ''

-- =========================================================
-- OVERALL SUMMARY
-- =========================================================

\echo '1. Overall Soccer Team Count:'
SELECT 
    st.sport_code,
    st.sport_name,
    COUNT(t.team_id) as teams
FROM sport_type st
LEFT JOIN team t ON st.sport_id = t.sport_id
WHERE st.sport_id IN (7, 8, 9)  -- MLS, EPL, La Liga
GROUP BY st.sport_id, st.sport_code, st.sport_name
ORDER BY st.sport_id;

\echo ''
\echo 'Expected: MLS (~29), EPL (~20), La Liga (~20)'
\echo ''

-- =========================================================
-- MLS (Major League Soccer)
-- =========================================================

\echo '=========================================='
\echo 'MLS VERIFICATION'
\echo '=========================================='
\echo ''

\echo '2. MLS Team Count:'
SELECT COUNT(*) as mls_teams FROM team WHERE sport_id = 7;

\echo ''

\echo '3. MLS Teams by Country:'
SELECT 
    country_code,
    country_name,
    COUNT(*) as teams
FROM team
WHERE sport_id = 7
GROUP BY country_code, country_name
ORDER BY teams DESC;

\echo ''
\echo 'Expected: ~26 US teams, ~3 Canadian teams'
\echo ''

\echo '4. MLS Canadian Teams:'
SELECT name, city, abbrev
FROM team
WHERE sport_id = 7 AND country_code = 'CA'
ORDER BY name;

\echo ''
\echo 'Expected: Toronto FC, Vancouver Whitecaps, CF Montreal'
\echo ''

\echo '5. MLS Abbreviation Check:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 7
GROUP BY LENGTH(abbrev);

\echo ''

\echo '6. MLS Duplicate Abbreviations:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as teams
FROM team
WHERE sport_id = 7
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'
\echo ''

\echo '7. MLS Sample Teams:'
SELECT name, abbrev, city, country_code
FROM team
WHERE sport_id = 7
ORDER BY name
LIMIT 10;

\echo ''

\echo '8. MLS Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 7
  AND name IN (
    'LA Galaxy',
    'Seattle Sounders',
    'Atlanta United',
    'Inter Miami',
    'Toronto FC'
  )
ORDER BY name;

\echo ''

\echo '9. MLS Venues:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 7 AND venue_id IS NOT NULL;

\echo ''

-- =========================================================
-- EPL (English Premier League)
-- =========================================================

\echo '=========================================='
\echo 'EPL VERIFICATION'
\echo '=========================================='
\echo ''

\echo '10. EPL Team Count:'
SELECT COUNT(*) as epl_teams FROM team WHERE sport_id = 8;

\echo ''
\echo 'Expected: 20 teams'
\echo ''

\echo '11. EPL Teams by Country:'
SELECT 
    country_code,
    country_name,
    COUNT(*) as teams
FROM team
WHERE sport_id = 8
GROUP BY country_code, country_name;

\echo ''
\echo 'Expected: All teams should be England (GB/UK)'
\echo ''

\echo '12. EPL Abbreviation Length:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 8
GROUP BY LENGTH(abbrev);

\echo ''

\echo '13. EPL Duplicate Abbreviations:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as teams
FROM team
WHERE sport_id = 8
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'
\echo ''

\echo '14. EPL All Teams:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 8
ORDER BY name;

\echo ''

\echo '15. EPL Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 8
  AND name IN (
    'Manchester United',
    'Manchester City',
    'Liverpool',
    'Chelsea',
    'Arsenal',
    'Tottenham Hotspur'
  )
ORDER BY name;

\echo ''
\echo 'Expected: All 6 famous teams should exist'
\echo ''

\echo '16. EPL Manchester Teams (conflict test):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 8
  AND name LIKE '%Manchester%'
ORDER BY name;

\echo ''
\echo 'Expected: Manchester United and Manchester City with unique abbrevs'
\echo ''

-- =========================================================
-- LA LIGA (Spanish League)
-- =========================================================

\echo '=========================================='
\echo 'LA LIGA VERIFICATION'
\echo '=========================================='
\echo ''

\echo '17. La Liga Team Count:'
SELECT COUNT(*) as la_liga_teams FROM team WHERE sport_id = 9;

\echo ''
\echo 'Expected: 20 teams'
\echo ''

\echo '18. La Liga Teams by Country:'
SELECT 
    country_code,
    country_name,
    COUNT(*) as teams
FROM team
WHERE sport_id = 9
GROUP BY country_code, country_name;

\echo ''
\echo 'Expected: All teams should be Spain (ES)'
\echo ''

\echo '19. La Liga Abbreviation Length:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 9
GROUP BY LENGTH(abbrev);

\echo ''

\echo '20. La Liga Duplicate Abbreviations:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ') as teams
FROM team
WHERE sport_id = 9
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'
\echo ''

\echo '21. La Liga All Teams:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 9
ORDER BY name;

\echo ''

\echo '22. La Liga Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 9
  AND (
    name LIKE '%Real Madrid%' OR
    name LIKE '%Barcelona%' OR
    name LIKE '%Atletico%' OR
    name LIKE '%Sevilla%' OR
    name LIKE '%Valencia%'
  )
ORDER BY name;

\echo ''
\echo 'Expected: Real Madrid, Barcelona, Atletico Madrid should exist'
\echo ''

\echo '23. La Liga Madrid Teams (conflict test):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 9
  AND name LIKE '%Madrid%'
ORDER BY name;

\echo ''
\echo 'Expected: Real Madrid and Atletico Madrid with unique abbrevs'
\echo ''

-- =========================================================
-- CROSS-LEAGUE CHECKS
-- =========================================================

\echo '=========================================='
\echo 'CROSS-LEAGUE CHECKS'
\echo '=========================================='
\echo ''

\echo '24. All Soccer Teams Summary:'
SELECT 
    sport_id,
    COUNT(*) as teams,
    COUNT(DISTINCT abbrev) as unique_abbrevs,
    COUNT(DISTINCT venue_id) as venues
FROM team
WHERE sport_id IN (7, 8, 9)
GROUP BY sport_id
ORDER BY sport_id;

\echo ''

\echo '25. Soccer Data Quality:'
SELECT 
    'MLS - Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 7 AND city IS NULL
UNION ALL
SELECT 'MLS - Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 7 AND abbrev IS NULL
UNION ALL
SELECT 'EPL - Teams missing city', COUNT(*) 
FROM team WHERE sport_id = 8 AND city IS NULL
UNION ALL
SELECT 'EPL - Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 8 AND abbrev IS NULL
UNION ALL
SELECT 'La Liga - Teams missing city', COUNT(*) 
FROM team WHERE sport_id = 9 AND city IS NULL
UNION ALL
SELECT 'La Liga - Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 9 AND abbrev IS NULL;

\echo ''

\echo '26. All Soccer Abbreviations (checking for conflicts):'
SELECT 
    t.abbrev,
    COUNT(*) as count,
    STRING_AGG(st.sport_code || ': ' || t.name, ', ') as teams
FROM team t
JOIN sport_type st ON t.sport_id = st.sport_id
WHERE t.sport_id IN (7, 8, 9)
GROUP BY t.abbrev
HAVING COUNT(*) > 1;

\echo ''
\echo '(If no rows, no abbreviation conflicts across all soccer leagues!)'
\echo ''

-- =========================================================
-- BONUS: ALL ABBREVIATIONS
-- =========================================================

\echo '=========================================='
\echo 'BONUS: ALL SOCCER TEAM ABBREVIATIONS'
\echo '=========================================='
\echo ''

\echo '27. MLS Abbreviations:'
SELECT abbrev, name FROM team WHERE sport_id = 7 ORDER BY abbrev;

\echo ''

\echo '28. EPL Abbreviations:'
SELECT abbrev, name FROM team WHERE sport_id = 8 ORDER BY abbrev;

\echo ''

\echo '29. La Liga Abbreviations:'
SELECT abbrev, name FROM team WHERE sport_id = 9 ORDER BY abbrev;

\echo ''

-- =========================================================
-- FINAL SUMMARY
-- =========================================================

\echo '=========================================='
\echo 'FINAL SUMMARY'
\echo '=========================================='
\echo ''

SELECT 
    'Total Soccer Teams' as metric,
    COUNT(*)::text as value
FROM team WHERE sport_id IN (7, 8, 9)
UNION ALL
SELECT 
    'MLS Teams',
    COUNT(*)::text
FROM team WHERE sport_id = 7
UNION ALL
SELECT 
    'EPL Teams',
    COUNT(*)::text
FROM team WHERE sport_id = 8
UNION ALL
SELECT 
    'La Liga Teams',
    COUNT(*)::text
FROM team WHERE sport_id = 9
UNION ALL
SELECT 
    'Soccer Venues',
    COUNT(DISTINCT venue_id)::text
FROM team WHERE sport_id IN (7, 8, 9) AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Unique Abbreviations',
    COUNT(DISTINCT abbrev)::text
FROM team WHERE sport_id IN (7, 8, 9);

\echo ''
\echo '=========================================='
\echo 'Expected Results:'
\echo '  - MLS: 29 teams (26 US, 3 CA)'
\echo '  - EPL: 20 teams (all England)'
\echo '  - La Liga: 20 teams (all Spain)'
\echo '  - Total: 69 soccer teams'
\echo '  - All abbreviations unique within each league'
\echo '  - No cross-league abbreviation conflicts'
\echo '=========================================='
\echo ''
