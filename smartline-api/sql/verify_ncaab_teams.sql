-- =========================================================
-- NCAAB Team Verification
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'NCAAB Team Verification'
\echo '=========================================='
\echo ''

-- 1. Team Count
\echo '1. NCAAB Team Count:'
SELECT COUNT(*) as ncaab_teams FROM team WHERE sport_id = 4;

\echo ''

-- 2. Abbreviation Length Distribution
\echo '2. Abbreviation Length Distribution:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 4
GROUP BY LENGTH(abbrev)
ORDER BY abbrev_length;

\echo ''

-- 3. Numeric Suffix Usage
\echo '3. Teams with Numeric Suffixes (conflict resolution):'
SELECT 
    'Teams with numeric suffix' as category,
    COUNT(*) as count
FROM team
WHERE sport_id = 4 
  AND abbrev ~ '[0-9]$'  -- Ends with a digit
UNION ALL
SELECT 
    'Teams without numeric suffix',
    COUNT(*)
FROM team
WHERE sport_id = 4 
  AND abbrev !~ '[0-9]$';

\echo ''

-- 4. Sample Teams with Numeric Suffixes
\echo '4. Sample Teams with Numeric Suffixes (showing conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 4 
  AND abbrev ~ '[0-9]$'
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 5. Duplicate Abbreviations Check
\echo '5. Duplicate Abbreviations Check:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ' ORDER BY name) as teams
FROM team
WHERE sport_id = 4
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'

\echo ''

-- 6. Famous Teams Check (Power 6 Conferences)
\echo '6. Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 4
  AND (
    name LIKE '%Duke%' OR
    name LIKE '%Kentucky%' OR
    name LIKE '%Kansas%' OR
    name LIKE '%North Carolina%' OR
    name LIKE '%Villanova%' OR
    name LIKE '%Gonzaga%' OR
    name LIKE '%UCLA%' OR
    name LIKE '%Michigan State%' OR
    name LIKE '%Connecticut%' OR
    name LIKE '%Arizona%'
  )
ORDER BY name;

\echo ''

-- 7. "State" Teams (common conflict pattern)
\echo '7. "State" Teams (checking conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 4
  AND name LIKE '%State%'
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 8. "University" Teams Sample
\echo '8. Sample "University of..." Teams:'
SELECT name, abbrev
FROM team
WHERE sport_id = 4
  AND name LIKE 'University of%'
ORDER BY name
LIMIT 20;

\echo ''

-- 9. Data Quality
\echo '9. Data Quality:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 4 AND city IS NULL
UNION ALL
SELECT 'Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 4 AND abbrev IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 4 AND logo_url IS NULL
UNION ALL
SELECT 'Teams missing name', COUNT(*) 
FROM team WHERE sport_id = 4 AND name IS NULL;

\echo ''

-- 10. Venues
\echo '10. NCAAB Venues:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 4 AND venue_id IS NOT NULL;

\echo ''

-- 11. Top 20 Teams Alphabetically
\echo '11. Sample Teams (First 20 alphabetically):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 4
ORDER BY name
LIMIT 20;

\echo ''

-- 12. Teams Starting with 'A' (Alabama schools)
\echo '12. Teams Starting with "A" (Alabama example):'
SELECT name, abbrev
FROM team
WHERE sport_id = 4
  AND name LIKE 'A%'
ORDER BY name
LIMIT 20;

\echo ''

-- 13. Abbreviation Patterns
\echo '13. Most Common Abbreviation Patterns (first 2 chars):'
SELECT 
    SUBSTRING(abbrev FROM 1 FOR 2) as abbrev_prefix,
    COUNT(*) as count
FROM team
WHERE sport_id = 4
GROUP BY abbrev_prefix
HAVING COUNT(*) > 10
ORDER BY count DESC
LIMIT 15;

\echo ''

-- 14. Country Distribution
\echo '14. Teams by Country:'
SELECT 
    COALESCE(country_code, 'NULL') as country,
    COUNT(*) as teams
FROM team
WHERE sport_id = 4
GROUP BY country_code
ORDER BY teams DESC;

\echo ''

-- 15. Conflict Resolution Examples
\echo '15. Abbreviation Series Examples (conflict resolution):'
SELECT abbrev, name
FROM team
WHERE sport_id = 4
  AND (
    abbrev LIKE 'AL%' OR 
    abbrev LIKE 'ST%' OR 
    abbrev LIKE 'UN%'
  )
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 16. Summary Statistics
\echo '16. Summary Statistics:'
SELECT 
    'Total NCAAB Teams' as metric,
    COUNT(*)::text as value
FROM team WHERE sport_id = 4
UNION ALL
SELECT 
    'Teams with Numeric Suffix',
    COUNT(*)::text
FROM team WHERE sport_id = 4 AND abbrev ~ '[0-9]$'
UNION ALL
SELECT 
    'Unique Abbreviations',
    COUNT(DISTINCT abbrev)::text
FROM team WHERE sport_id = 4
UNION ALL
SELECT 
    'Teams with Venues',
    COUNT(*)::text
FROM team WHERE sport_id = 4 AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Teams with Logos',
    COUNT(*)::text
FROM team WHERE sport_id = 4 AND logo_url IS NOT NULL;

\echo ''

\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 696 teams total (all divisions)'
\echo '  - All abbreviations unique (4 chars)'
\echo '  - Many teams have numeric suffixes (conflict resolution)'
\echo '  - Famous teams present'
\echo '  - State/University teams have unique abbreviations'
\echo '=========================================='
\echo ''

-- BONUS: Show all teams starting with same prefix
\echo 'BONUS: All Alabama Teams (showing conflicts):'
SELECT abbrev, name
FROM team
WHERE sport_id = 4 AND name LIKE 'Alabama%'
ORDER BY abbrev;

\echo ''

-- BONUS 2: Conference representation check
\echo 'BONUS: Sample Power Conference Teams:'
SELECT name, abbrev
FROM team
WHERE sport_id = 4
  AND (
    -- Big Ten
    name IN ('Michigan', 'Ohio State', 'Indiana', 'Purdue', 'Wisconsin') OR
    -- SEC
    name IN ('Kentucky', 'Alabama', 'Auburn', 'Tennessee', 'Florida') OR
    -- ACC
    name IN ('Duke', 'North Carolina', 'Virginia', 'Syracuse') OR
    -- Big 12
    name IN ('Kansas', 'Baylor', 'Texas', 'Oklahoma') OR
    -- Big East
    name IN ('Villanova', 'Georgetown', 'Connecticut', 'Marquette') OR
    -- Pac-12
    name IN ('UCLA', 'Arizona', 'USC', 'Oregon')
  )
ORDER BY name;

\echo ''

-- BONUS 3: All teams total across all sports
\echo 'BONUS: Total Teams Across All Sports:'
SELECT 
    st.sport_code,
    st.sport_name,
    COUNT(t.team_id) as teams
FROM sport_type st
LEFT JOIN team t ON st.sport_id = t.sport_id
GROUP BY st.sport_id, st.sport_code, st.sport_name
ORDER BY st.sport_id;

\echo ''

SELECT 
    'GRAND TOTAL' as metric,
    COUNT(*) as teams
FROM team;

\echo ''
\echo 'If 696 NCAAB teams with unique abbreviations, ready for player ETL!'
\echo ''

\echo ''

-- 2. Abbreviation Length Distribution
\echo '2. Abbreviation Length Distribution:'
SELECT 
    LENGTH(abbrev) as abbrev_length,
    COUNT(*) as count
FROM team
WHERE sport_id = 3
GROUP BY LENGTH(abbrev)
ORDER BY abbrev_length;

\echo ''

-- 3. Numeric Suffix Usage
\echo '3. Teams with Numeric Suffixes (conflict resolution):'
SELECT 
    'Teams with numeric suffix' as category,
    COUNT(*) as count
FROM team
WHERE sport_id = 3 
  AND abbrev ~ '[0-9]$'  -- Ends with a digit
UNION ALL
SELECT 
    'Teams without numeric suffix',
    COUNT(*)
FROM team
WHERE sport_id = 3 
  AND abbrev !~ '[0-9]$';

\echo ''

-- 4. Sample Teams with Numeric Suffixes
\echo '4. Sample Teams with Numeric Suffixes (showing conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 3 
  AND abbrev ~ '[0-9]$'
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 5. Duplicate Abbreviations Check
\echo '5. Duplicate Abbreviations Check:'
SELECT 
    abbrev,
    COUNT(*) as count,
    STRING_AGG(name, ', ' ORDER BY name) as teams
FROM team
WHERE sport_id = 3
GROUP BY abbrev
HAVING COUNT(*) > 1;

\echo '(If no rows, all abbreviations are unique!)'

\echo ''

-- 6. Famous Teams Check (Power 6 Conferences)
\echo '6. Famous Teams Check:'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 3
  AND (
    name LIKE '%Duke%' OR
    name LIKE '%Kentucky%' OR
    name LIKE '%Kansas%' OR
    name LIKE '%North Carolina%' OR
    name LIKE '%Villanova%' OR
    name LIKE '%Gonzaga%' OR
    name LIKE '%UCLA%' OR
    name LIKE '%Michigan State%' OR
    name LIKE '%Connecticut%' OR
    name LIKE '%Arizona%'
  )
ORDER BY name;

\echo ''

-- 7. "State" Teams (common conflict pattern)
\echo '7. "State" Teams (checking conflict resolution):'
SELECT name, abbrev
FROM team
WHERE sport_id = 3
  AND name LIKE '%State%'
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 8. "University" Teams Sample
\echo '8. Sample "University of..." Teams:'
SELECT name, abbrev
FROM team
WHERE sport_id = 3
  AND name LIKE 'University of%'
ORDER BY name
LIMIT 20;

\echo ''

-- 9. Data Quality
\echo '9. Data Quality:'
SELECT 
    'Teams missing city' as issue,
    COUNT(*) as count
FROM team WHERE sport_id = 3 AND city IS NULL
UNION ALL
SELECT 'Teams missing abbrev', COUNT(*) 
FROM team WHERE sport_id = 3 AND abbrev IS NULL
UNION ALL
SELECT 'Teams missing logo', COUNT(*) 
FROM team WHERE sport_id = 3 AND logo_url IS NULL
UNION ALL
SELECT 'Teams missing name', COUNT(*) 
FROM team WHERE sport_id = 3 AND name IS NULL;

\echo ''

-- 10. Venues
\echo '10. NCAAB Venues:'
SELECT COUNT(DISTINCT venue_id) as unique_venues
FROM team
WHERE sport_id = 3 AND venue_id IS NOT NULL;

\echo ''

-- 11. Top 20 Teams Alphabetically
\echo '11. Sample Teams (First 20 alphabetically):'
SELECT name, abbrev, city
FROM team
WHERE sport_id = 3
ORDER BY name
LIMIT 20;

\echo ''

-- 12. Teams Starting with 'A' (Alabama schools)
\echo '12. Teams Starting with "A" (Alabama example):'
SELECT name, abbrev
FROM team
WHERE sport_id = 3
  AND name LIKE 'A%'
ORDER BY name
LIMIT 20;

\echo ''

-- 13. Abbreviation Patterns
\echo '13. Most Common Abbreviation Patterns (first 2 chars):'
SELECT 
    SUBSTRING(abbrev FROM 1 FOR 2) as abbrev_prefix,
    COUNT(*) as count
FROM team
WHERE sport_id = 3
GROUP BY abbrev_prefix
HAVING COUNT(*) > 10
ORDER BY count DESC
LIMIT 15;

\echo ''

-- 14. Country Distribution
\echo '14. Teams by Country:'
SELECT 
    COALESCE(country_code, 'NULL') as country,
    COUNT(*) as teams
FROM team
WHERE sport_id = 3
GROUP BY country_code
ORDER BY teams DESC;

\echo ''

-- 15. Conflict Resolution Examples
\echo '15. Abbreviation Series Examples (conflict resolution):'
SELECT abbrev, name
FROM team
WHERE sport_id = 3
  AND (
    abbrev LIKE 'AL%' OR 
    abbrev LIKE 'ST%' OR 
    abbrev LIKE 'UN%'
  )
ORDER BY abbrev
LIMIT 30;

\echo ''

-- 16. Summary Statistics
\echo '16. Summary Statistics:'
SELECT 
    'Total NCAAB Teams' as metric,
    COUNT(*)::text as value
FROM team WHERE sport_id = 3
UNION ALL
SELECT 
    'Teams with Numeric Suffix',
    COUNT(*)::text
FROM team WHERE sport_id = 3 AND abbrev ~ '[0-9]$'
UNION ALL
SELECT 
    'Unique Abbreviations',
    COUNT(DISTINCT abbrev)::text
FROM team WHERE sport_id = 3
UNION ALL
SELECT 
    'Teams with Venues',
    COUNT(*)::text
FROM team WHERE sport_id = 3 AND venue_id IS NOT NULL
UNION ALL
SELECT 
    'Teams with Logos',
    COUNT(*)::text
FROM team WHERE sport_id = 3 AND logo_url IS NOT NULL;

\echo ''

\echo '=========================================='
\echo 'Expected Results:'
\echo '  - 696 teams total (all divisions)'
\echo '  - All abbreviations unique (4 chars)'
\echo '  - Many teams have numeric suffixes (conflict resolution)'
\echo '  - Famous teams present'
\echo '  - State/University teams have unique abbreviations'
\echo '=========================================='
\echo ''

-- BONUS: Show all teams starting with same prefix
\echo 'BONUS: All Alabama Teams (showing conflicts):'
SELECT abbrev, name
FROM team
WHERE sport_id = 3 AND name LIKE 'Alabama%'
ORDER BY abbrev;

\echo ''

-- BONUS 2: Conference representation check
\echo 'BONUS: Sample Power Conference Teams:'
SELECT name, abbrev
FROM team
WHERE sport_id = 3
  AND (
    -- Big Ten
    name IN ('Michigan', 'Ohio State', 'Indiana', 'Purdue', 'Wisconsin') OR
    -- SEC
    name IN ('Kentucky', 'Alabama', 'Auburn', 'Tennessee', 'Florida') OR
    -- ACC
    name IN ('Duke', 'North Carolina', 'Virginia', 'Syracuse') OR
    -- Big 12
    name IN ('Kansas', 'Baylor', 'Texas', 'Oklahoma') OR
    -- Big East
    name IN ('Villanova', 'Georgetown', 'Connecticut', 'Marquette') OR
    -- Pac-12
    name IN ('UCLA', 'Arizona', 'USC', 'Oregon')
  )
ORDER BY name;

\echo ''

-- BONUS 3: All teams total across all sports
\echo 'BONUS: Total Teams Across All Sports:'
SELECT 
    st.sport_code,
    st.sport_name,
    COUNT(t.team_id) as teams
FROM sport_type st
LEFT JOIN team t ON st.sport_id = t.sport_id
GROUP BY st.sport_id, st.sport_code, st.sport_name
ORDER BY st.sport_id;

\echo ''

SELECT 
    'GRAND TOTAL' as metric,
    COUNT(*) as teams
FROM team;

\echo ''
\echo 'If 696 NCAAB teams with unique abbreviations, ready for player ETL!'
\echo ''
