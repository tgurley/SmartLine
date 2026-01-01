-- =========================================================
-- Create All Sport Leagues
-- =========================================================
-- Run this BEFORE running team ETLs for each sport
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Creating Sport Leagues'
\echo '=========================================='
\echo ''

-- NFL (already exists, but just in case)
INSERT INTO league (name, sport_id, league_code)
VALUES ('NFL', 1, 'nfl')
ON CONFLICT DO NOTHING;

-- NCAAF
INSERT INTO league (name, sport_id, league_code)
VALUES ('NCAAF', 2, 'ncaaf')
ON CONFLICT DO NOTHING;

-- NBA
INSERT INTO league (name, sport_id, league_code)
VALUES ('NBA', 3, 'nba')
ON CONFLICT DO NOTHING;

-- NCAAB
INSERT INTO league (name, sport_id, league_code)
VALUES ('NCAAB', 4, 'ncaab')
ON CONFLICT DO NOTHING;

-- MLB
INSERT INTO league (name, sport_id, league_code)
VALUES ('MLB', 5, 'mlb')
ON CONFLICT DO NOTHING;

-- NHL
INSERT INTO league (name, sport_id, league_code)
VALUES ('NHL', 6, 'nhl')
ON CONFLICT DO NOTHING;

-- MLS
INSERT INTO league (name, sport_id, league_code)
VALUES ('MLS', 7, 'mls')
ON CONFLICT DO NOTHING;

-- EPL
INSERT INTO league (name, sport_id, league_code)
VALUES ('EPL', 8, 'epl')
ON CONFLICT DO NOTHING;

-- La Liga
INSERT INTO league (name, sport_id, league_code)
VALUES ('La Liga', 9, 'la_liga')
ON CONFLICT DO NOTHING;

-- Bundesliga
INSERT INTO league (name, sport_id, league_code)
VALUES ('Bundesliga', 10, 'bundesliga')
ON CONFLICT DO NOTHING;

-- Serie A
INSERT INTO league (name, sport_id, league_code)
VALUES ('Serie A', 11, 'serie_a')
ON CONFLICT DO NOTHING;

-- Ligue 1
INSERT INTO league (name, sport_id, league_code)
VALUES ('Ligue 1', 12, 'ligue_1')
ON CONFLICT DO NOTHING;

-- Champions League
INSERT INTO league (name, sport_id, league_code)
VALUES ('Champions League', 13, 'champions_league')
ON CONFLICT DO NOTHING;

COMMIT;

\echo ''
\echo '=========================================='
\echo 'Leagues Created'
\echo '=========================================='
\echo ''

-- Show all leagues
SELECT 
    l.league_id,
    l.name as league_name,
    l.league_code,
    st.sport_code,
    st.sport_name
FROM league l
JOIN sport_type st ON l.sport_id = st.sport_id
ORDER BY l.sport_id, l.league_id;

\echo ''
\echo 'Ready to run team ETLs!'
\echo ''
