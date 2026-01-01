-- =========================================================
-- NCAAF Team Verification
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'NCAAF Team Verification'
\echo '=========================================='
\echo ''

-- 1. Team Count
\echo '1. NCAAF Team Count:'
SELECT COUNT(*) as ncaaf_teams FROM team WHERE sport_id = 2;

\echo ''

-- 2. Abbreviation Length Distribution
\echo '2. Abbreviation Length Distribution:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 2
GROUP BY LENGTH(abbrev)
ORDER BY abbrev_length;

\echo ''

-- 3. Numeric Suffix Usage
\echo '3. Teams with Numeric Suffixes (conflict resolution):'
SELECT 
    'Teams with numeric suffix' as category,
    COUNT(*) as count
FROM team
WHERE sport_id = 2 
  AND abbrev ~ '[0-9]$'  -- Ends with a digit
UNION ALL
SELECT 
    'Teams without numeric suffix',
    COUNT(*)
FROM team
WHERE sport_id = 2 
  AND abbrev !~ '[0-9]$';

\echo ''

-- 4. Sample Teams with Numeric Suffixes
\echo '4. Sample Teams with Numeric Suffixes (showing conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 2 
  AND abbrev ~ '[0-9]$'
ORDER BY abbrev
LIMIT 20;

\echo ''

-- 5. Duplicate Abbreviations Check
\echo '5. Duplicate Abbreviations Check:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ' ORDER BY name) as teams
FROM team
WHERE sport_id = 2
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'

\echo ''

-- 6. Famous Teams Check
\echo '6. Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 2
  AND (
    name LIKE '%Alabama%' OR
    name LIKE '%Ohio State%' OR
    name LIKE '%Michigan%' OR
    name LIKE '%Georgia%' OR
    name LIKE '%Notre Dame%' OR
    name LIKE '%Texas%' OR
    name LIKE '%USC%' OR
    name LIKE '%Penn State%'
  )
ORDER BY name;

\echo ''

-- 7. "State" Teams (common conflict pattern)
\echo '7. "State" Teams (checking conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 2
  AND name LIKE '%State%'
ORDER BY abbrev;

\echo ''

-- 8. "Tech" Teams (another common conflict pattern)
\echo '8. "Tech" Teams (checking conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 2
  AND name LIKE '%Tech%'
ORDER BY abbrev;

\echo ''

-- 9. Data Quality
\echo '9. Data Quality:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 2 AND city IS NULL
UNION ALL
SELECT 'Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 2 AND abbrev IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 2 AND logo_url IS NULL
UNION ALL
SELECT 'Teams missing name', COUNT(*) 
FROM team WHERE sport_id = 2 AND name IS NULL;

\echo ''

-- 10. Venues
\echo '10. NCAAF Venues:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 2 AND venue_id IS NOT NULL;

\echo ''

-- 11. Sample Teams by Division (if identifiable)
\echo '11. Sample FBS Teams (Power 5 Conferences):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 2
  AND (
    name LIKE '%Alabama%' OR
    name LIKE '%Auburn%' OR
    name LIKE '%Florida%' OR
    name LIKE '%LSU%' OR
    name LIKE '%Georgia%' OR
    name LIKE '%Tennessee%' OR
    name LIKE '%Michigan%' OR
    name LIKE '%Ohio State%' OR
    name LIKE '%Penn State%' OR
    name LIKE '%Wisconsin%' OR
    name LIKE '%USC%' OR
    name LIKE '%UCLA%' OR
    name LIKE '%Stanford%' OR
    name LIKE '%Oregon%' OR
    name LIKE '%Oklahoma%' OR
    name LIKE '%Texas%' OR
    name LIKE '%Clemson%' OR
    name LIKE '%Miami%' OR
    name LIKE '%Florida State%' OR
    name LIKE '%Notre Dame%'
  )
ORDER BY name
LIMIT 20;

\echo ''

-- 12. Top 20 Teams Alphabetically
\echo '12. Sample Teams (First 20 alphabetically):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 2
ORDER BY name
LIMIT 20;

\echo ''

-- 13. Abbreviation Patterns
\echo '13. Most Common Abbreviation Patterns:'
SELECT 
    SUBSTRING(abbrev FROM 1 FOR 2) as abbrev_prefix,
    COUNT(*) as count
FROM team
WHERE sport_id = 2
GROUP BY abbrev_prefix
HAVING COUNT(*) > 5
ORDER BY count DESC
LIMIT 10;

\echo ''

-- 14. Country Distribution
\echo '14. Teams by Country:'
SELECT 
    COALESCE(country_code, 'NULL') as country,
    COUNT(*) as teams
FROM team
WHERE sport_id = 2
GROUP BY country_code
ORDER BY teams DESC;

\echo ''

-- 15. Summary Statistics
\echo '15. Summary Statistics:'
SELECT 
    'Total NCAAF Teams' as metric,
    COUNT(*)::text as value
FROM team WHERE sport_id = 2
UNION ALL
SELECT 
    'Teams with Numeric Suffix',
    COUNT(*)::text
FROM team WHERE sport_id = 2 AND abbrev ~ '[0-9]$'
UNION ALL
SELECT 
    'Unique Abbreviations',
    COUNT(DISTINCT abbrev)::text
FROM team WHERE sport_id = 2
UNION ALL
SELECT 
    'Teams with Venues',
    COUNT(*)::text
FROM team WHERE sport_id = 2 AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Teams with Logos',
    COUNT(*)::text
FROM team WHERE sport_id = 2 AND logo_url IS NOT NULL;

\echo ''

\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 706 teams total (all divisions)'
\echo '  - All abbreviations unique (4 chars)'
\echo '  - Some teams have numeric suffixes (conflict resolution)'
\echo '  - Famous teams present'
\echo '  - State/Tech teams have unique abbreviations'
\echo '=========================================='
\echo ''

-- BONUS: Show all State teams with their abbreviations
\echo 'BONUS: All "State" Teams:'
SELECT abbrev, name
FROM team
WHERE sport_id = 2 AND name LIKE '%State%'
ORDER BY abbrev;

\echo ''

-- BONUS 2: Abbreviation conflict examples
\echo 'BONUS: Abbreviation Series (showing conflict resolution):'
SELECT abbrev, name
FROM team
WHERE sport_id = 2
  AND (abbrev LIKE 'OHS%' OR abbrev LIKE 'MIS%' OR abbrev LIKE 'PES%')
ORDER BY abbrev;

\echo ''
\echo 'If 706 teams with unique abbreviations, NCAAF is complete!'
\echo ''
