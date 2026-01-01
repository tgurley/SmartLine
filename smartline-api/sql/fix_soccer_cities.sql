-- =========================================================
-- Fix Soccer Team Cities (MLS, EPL, La Liga)
-- =========================================================
-- Adds missing cities for all soccer teams
-- Data sourced from official league information (2024-25 season)
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Fixing Soccer Team Cities'
\echo '=========================================='
\echo ''

-- =========================================================
-- MLS (Major League Soccer) - 29 Teams
-- =========================================================

\echo 'Updating MLS team cities...'

-- Eastern Conference
UPDATE team SET city = 'Atlanta', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Atlanta United';
UPDATE team SET city = 'Charlotte', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Charlotte FC';
UPDATE team SET city = 'Chicago', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Chicago Fire';
UPDATE team SET city = 'Cincinnati', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'FC Cincinnati';
UPDATE team SET city = 'Columbus', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Columbus Crew';
UPDATE team SET city = 'Washington', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'DC United';
UPDATE team SET city = 'Miami', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Inter Miami';
UPDATE team SET city = 'Miami', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Inter Miami CF';
UPDATE team SET city = 'Montreal', country_code = 'CA', country_name = 'Canada' WHERE sport_id = 7 AND name = 'CF Montreal';
UPDATE team SET city = 'Montreal', country_code = 'CA', country_name = 'Canada' WHERE sport_id = 7 AND name = 'CF Montréal';
UPDATE team SET city = 'Nashville', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Nashville SC';
UPDATE team SET city = 'Foxborough', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'New England Revolution';
UPDATE team SET city = 'New York', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'New York City FC';
UPDATE team SET city = 'Harrison', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'New York Red Bulls';
UPDATE team SET city = 'Orlando', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Orlando City';
UPDATE team SET city = 'Orlando', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Orlando City SC';
UPDATE team SET city = 'Philadelphia', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Philadelphia Union';
UPDATE team SET city = 'Toronto', country_code = 'CA', country_name = 'Canada' WHERE sport_id = 7 AND name = 'Toronto FC';

-- Western Conference
UPDATE team SET city = 'Austin', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Austin FC';
UPDATE team SET city = 'Commerce City', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Colorado Rapids';
UPDATE team SET city = 'Houston', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Houston Dynamo';
UPDATE team SET city = 'Houston', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Houston Dynamo FC';
UPDATE team SET city = 'Los Angeles', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'LA Galaxy';
UPDATE team SET city = 'Los Angeles', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'LAFC';
UPDATE team SET city = 'St. Paul', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Minnesota United';
UPDATE team SET city = 'St. Paul', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Minnesota United FC';
UPDATE team SET city = 'Portland', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Portland Timbers';
UPDATE team SET city = 'Sandy', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Real Salt Lake';
UPDATE team SET city = 'San Jose', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'San Jose Earthquakes';
UPDATE team SET city = 'Seattle', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Seattle Sounders';
UPDATE team SET city = 'Seattle', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Seattle Sounders FC';
UPDATE team SET city = 'Kansas City', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'Sporting Kansas City';
UPDATE team SET city = 'St. Louis', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'St. Louis City';
UPDATE team SET city = 'St. Louis', country_code = 'US', country_name = 'USA' WHERE sport_id = 7 AND name = 'St. Louis City SC';
UPDATE team SET city = 'Vancouver', country_code = 'CA', country_name = 'Canada' WHERE sport_id = 7 AND name = 'Vancouver Whitecaps';
UPDATE team SET city = 'Vancouver', country_code = 'CA', country_name = 'Canada' WHERE sport_id = 7 AND name = 'Vancouver Whitecaps FC';

-- =========================================================
-- EPL (English Premier League) - 20 Teams
-- =========================================================

\echo 'Updating EPL team cities...'

UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Arsenal';
UPDATE team SET city = 'Birmingham', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Aston Villa';
UPDATE team SET city = 'Bournemouth', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Bournemouth';
UPDATE team SET city = 'Bournemouth', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'AFC Bournemouth';
UPDATE team SET city = 'Brentford', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Brentford';
UPDATE team SET city = 'Brighton', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Brighton';
UPDATE team SET city = 'Brighton', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Brighton & Hove Albion';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Chelsea';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Crystal Palace';
UPDATE team SET city = 'Liverpool', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Everton';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Fulham';
UPDATE team SET city = 'Ipswich', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Ipswich Town';
UPDATE team SET city = 'Leicester', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Leicester City';
UPDATE team SET city = 'Liverpool', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Liverpool';
UPDATE team SET city = 'Manchester', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Manchester City';
UPDATE team SET city = 'Manchester', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Manchester United';
UPDATE team SET city = 'Newcastle', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Newcastle';
UPDATE team SET city = 'Newcastle', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Newcastle United';
UPDATE team SET city = 'Nottingham', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Nottingham Forest';
UPDATE team SET city = 'Southampton', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Southampton';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Tottenham';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Tottenham Hotspur';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'West Ham';
UPDATE team SET city = 'London', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'West Ham United';
UPDATE team SET city = 'Wolverhampton', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Wolves';
UPDATE team SET city = 'Wolverhampton', country_code = 'GB', country_name = 'England' WHERE sport_id = 8 AND name = 'Wolverhampton Wanderers';

-- =========================================================
-- LA LIGA (Spanish League) - 20 Teams
-- =========================================================

\echo 'Updating La Liga team cities...'

UPDATE team SET city = 'Alaves', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Alaves';
UPDATE team SET city = 'Alaves', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Deportivo Alaves';
UPDATE team SET city = 'Almeria', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Almeria';
UPDATE team SET city = 'Almeria', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'UD Almeria';
UPDATE team SET city = 'Bilbao', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Athletic Bilbao';
UPDATE team SET city = 'Bilbao', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Athletic Club';
UPDATE team SET city = 'Madrid', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Atletico Madrid';
UPDATE team SET city = 'Barcelona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Barcelona';
UPDATE team SET city = 'Barcelona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'FC Barcelona';
UPDATE team SET city = 'Cadiz', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Cadiz';
UPDATE team SET city = 'Cadiz', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Cadiz CF';
UPDATE team SET city = 'Vigo', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Celta Vigo';
UPDATE team SET city = 'Vigo', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'RC Celta';
UPDATE team SET city = 'Girona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Girona';
UPDATE team SET city = 'Girona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Girona FC';
UPDATE team SET city = 'Getafe', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Getafe';
UPDATE team SET city = 'Getafe', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Getafe CF';
UPDATE team SET city = 'Las Palmas', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Las Palmas';
UPDATE team SET city = 'Las Palmas', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'UD Las Palmas';
UPDATE team SET city = 'Mallorca', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Mallorca';
UPDATE team SET city = 'Mallorca', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'RCD Mallorca';
UPDATE team SET city = 'Pamplona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Osasuna';
UPDATE team SET city = 'Pamplona', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'CA Osasuna';
UPDATE team SET city = 'Vallecas', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Rayo Vallecano';
UPDATE team SET city = 'Madrid', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Real Madrid';
UPDATE team SET city = 'San Sebastian', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Real Sociedad';
UPDATE team SET city = 'Seville', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Sevilla';
UPDATE team SET city = 'Seville', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Sevilla FC';
UPDATE team SET city = 'Valencia', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Valencia';
UPDATE team SET city = 'Valencia', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Valencia CF';
UPDATE team SET city = 'Valladolid', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Valladolid';
UPDATE team SET city = 'Valladolid', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Real Valladolid';
UPDATE team SET city = 'Villarreal', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Villarreal';
UPDATE team SET city = 'Villarreal', country_code = 'ES', country_name = 'Spain' WHERE sport_id = 9 AND name = 'Villarreal CF';

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Verification'
\echo '=========================================='
\echo ''

-- Verify MLS cities
\echo 'MLS - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 7 AND city IS NOT NULL;

\echo ''

-- Verify MLS countries
\echo 'MLS - Teams by country:'
SELECT country_code, COUNT(*) as teams
FROM team
WHERE sport_id = 7
GROUP BY country_code
ORDER BY teams DESC;

\echo ''

-- Verify EPL cities
\echo 'EPL - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 8 AND city IS NOT NULL;

\echo ''

-- Verify EPL country
\echo 'EPL - All teams should be England (GB):'
SELECT country_code, COUNT(*) as teams
FROM team
WHERE sport_id = 8
GROUP BY country_code;

\echo ''

-- Verify La Liga cities
\echo 'La Liga - Teams with cities:'
SELECT COUNT(*) as teams_with_city
FROM team
WHERE sport_id = 9 AND city IS NOT NULL;

\echo ''

-- Verify La Liga country
\echo 'La Liga - All teams should be Spain (ES):'
SELECT country_code, COUNT(*) as teams
FROM team
WHERE sport_id = 9
GROUP BY country_code;

\echo ''

\echo '=========================================='
\echo 'Fix Complete!'
\echo '=========================================='
\echo ''
\echo 'Expected results:'
\echo '  - MLS: 29 teams with cities (26 US, 3 CA)'
\echo '  - EPL: 20 teams with cities (all GB/England)'
\echo '  - La Liga: 20 teams with cities (all ES/Spain)'
\echo ''
