-- =========================================================
-- Fix NHL Team Data
-- =========================================================
-- Adds missing: cities, Canadian teams, conferences, divisions
-- Data sourced from official NHL information (2024-25 season)
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Fixing NHL Team Data'
\echo '=========================================='
\echo ''

-- =========================================================
-- ATLANTIC DIVISION (Eastern Conference)
-- =========================================================

\echo 'Updating Atlantic Division teams...'

UPDATE team SET city = 'Boston', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Boston Bruins';

UPDATE team SET city = 'Buffalo', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Buffalo Sabres';

UPDATE team SET city = 'Detroit', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Detroit Red Wings';

UPDATE team SET city = 'Sunrise', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Florida Panthers';

UPDATE team SET city = 'Montreal', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Montreal Canadiens';

UPDATE team SET city = 'Ottawa', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Ottawa Senators';

UPDATE team SET city = 'Tampa', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Tampa Bay Lightning';

UPDATE team SET city = 'Toronto', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Toronto Maple Leafs';

-- Update conference/division for Atlantic
UPDATE nhl_team_data SET conference = 'Eastern', division = 'Atlantic'
WHERE team_id IN (
    SELECT team_id FROM team WHERE sport_id = 6 AND name IN (
        'Boston Bruins', 'Buffalo Sabres', 'Detroit Red Wings', 'Florida Panthers',
        'Montreal Canadiens', 'Ottawa Senators', 'Tampa Bay Lightning', 'Toronto Maple Leafs'
    )
);

-- =========================================================
-- METROPOLITAN DIVISION (Eastern Conference)
-- =========================================================

\echo 'Updating Metropolitan Division teams...'

UPDATE team SET city = 'Raleigh', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Carolina Hurricanes';

UPDATE team SET city = 'Columbus', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Columbus Blue Jackets';

UPDATE team SET city = 'Newark', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'New Jersey Devils';

UPDATE team SET city = 'Uniondale', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'New York Islanders';

UPDATE team SET city = 'New York', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'New York Rangers';

UPDATE team SET city = 'Philadelphia', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Philadelphia Flyers';

UPDATE team SET city = 'Pittsburgh', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Pittsburgh Penguins';

UPDATE team SET city = 'Washington', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Washington Capitals';

-- Update conference/division for Metropolitan
UPDATE nhl_team_data SET conference = 'Eastern', division = 'Metropolitan'
WHERE team_id IN (
    SELECT team_id FROM team WHERE sport_id = 6 AND name IN (
        'Carolina Hurricanes', 'Columbus Blue Jackets', 'New Jersey Devils', 'New York Islanders',
        'New York Rangers', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'Washington Capitals'
    )
);

-- =========================================================
-- CENTRAL DIVISION (Western Conference)
-- =========================================================

\echo 'Updating Central Division teams...'

UPDATE team SET city = 'Chicago', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Chicago Blackhawks';

UPDATE team SET city = 'Denver', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Colorado Avalanche';

UPDATE team SET city = 'Dallas', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Dallas Stars';

UPDATE team SET city = 'St. Paul', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Minnesota Wild';

UPDATE team SET city = 'Nashville', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Nashville Predators';

UPDATE team SET city = 'St. Louis', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'St. Louis Blues';

UPDATE team SET city = 'Salt Lake City', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Utah Hockey Club';

UPDATE team SET city = 'Salt Lake City', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Utah Mammoth';

UPDATE team SET city = 'Winnipeg', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Winnipeg Jets';

-- Update conference/division for Central
UPDATE nhl_team_data SET conference = 'Western', division = 'Central'
WHERE team_id IN (
    SELECT team_id FROM team WHERE sport_id = 6 AND name IN (
        'Chicago Blackhawks', 'Colorado Avalanche', 'Dallas Stars', 'Minnesota Wild',
        'Nashville Predators', 'St. Louis Blues', 'Utah Hockey Club', 'Utah Mammoth', 'Winnipeg Jets'
    )
);

-- =========================================================
-- PACIFIC DIVISION (Western Conference)
-- =========================================================

\echo 'Updating Pacific Division teams...'

UPDATE team SET city = 'Anaheim', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Anaheim Ducks';

UPDATE team SET city = 'Calgary', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Calgary Flames';

UPDATE team SET city = 'Edmonton', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Edmonton Oilers';

UPDATE team SET city = 'Los Angeles', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Los Angeles Kings';

UPDATE team SET city = 'San Jose', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'San Jose Sharks';

UPDATE team SET city = 'Seattle', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Seattle Kraken';

UPDATE team SET city = 'Vancouver', country_code = 'CA', country_name = 'Canada'
WHERE sport_id = 6 AND name = 'Vancouver Canucks';

UPDATE team SET city = 'Las Vegas', country_code = 'US', country_name = 'USA'
WHERE sport_id = 6 AND name = 'Vegas Golden Knights';

-- Update conference/division for Pacific
UPDATE nhl_team_data SET conference = 'Western', division = 'Pacific'
WHERE team_id IN (
    SELECT team_id FROM team WHERE sport_id = 6 AND name IN (
        'Anaheim Ducks', 'Calgary Flames', 'Edmonton Oilers', 'Los Angeles Kings',
        'San Jose Sharks', 'Seattle Kraken', 'Vancouver Canucks', 'Vegas Golden Knights'
    )
);

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Verification'
\echo '=========================================='
\echo ''

-- Verify countries
\echo 'Teams by Country:'
SELECT 
    country_code,
    country_name,
    COUNT(*) as teams
FROM team
WHERE sport_id = 6
GROUP BY country_code, country_name
ORDER BY teams DESC;

\echo ''

-- Verify Canadian teams
\echo 'Canadian Teams (should be 7):'
SELECT name, city FROM team 
WHERE sport_id = 6 AND country_code = 'CA'
ORDER BY name;

\echo ''

-- Verify conferences
\echo 'Conference Breakdown:'
SELECT 
    conference,
    COUNT(*) as teams
FROM nhl_team_data
GROUP BY conference
ORDER BY conference;

\echo ''

-- Verify divisions
\echo 'Division Breakdown:'
SELECT 
    conference,
    division,
    COUNT(*) as teams
FROM nhl_team_data
GROUP BY conference, division
ORDER BY conference, division;

\echo ''

-- Verify cities filled
\echo 'Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 6 AND city IS NOT NULL;

\echo ''

\echo '=========================================='
\echo 'Fix Complete!'
\echo '=========================================='
\echo ''
\echo 'Expected results:'
\echo '  - 7 Canadian teams'
\echo '  - 25 US teams'
\echo '  - Eastern Conference: 16 teams'
\echo '  - Western Conference: 16 teams'
\echo '  - 4 divisions (8 teams each)'
\echo '  - All teams have cities'
\echo ''
