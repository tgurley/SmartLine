-- =========================================================
-- SmartLine Multi-Sport Migration - Step 3
-- =========================================================
-- Version: 5.2.0 → 5.3.0
-- Purpose: Add constraints and update views
-- Date: 2024-12-31
--
-- This migration:
-- 1. Makes sport_id NOT NULL
-- 2. Adds foreign key constraints
-- 3. Drops old NFL-specific views
-- 4. Creates new multi-sport views
--
-- BREAKING: Makes sport_id required
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Step 3: Adding Constraints and Views'
\echo '=========================================='
\echo ''

-- =========================================================
-- STEP 3.1: MAKE sport_id NOT NULL
-- =========================================================

\echo 'Making sport_id NOT NULL...'

-- league
ALTER TABLE league 
    ALTER COLUMN sport_id SET NOT NULL;

-- game (critical for filtering)
ALTER TABLE game 
    ALTER COLUMN sport_id SET NOT NULL;

\echo '✓ sport_id is now required on league and game tables'
\echo ''

-- =========================================================
-- STEP 3.2: ADD FOREIGN KEY CONSTRAINTS
-- =========================================================

\echo 'Adding foreign key constraints...'

-- league -> sport_type
ALTER TABLE league 
    ADD CONSTRAINT fk_league_sport_id 
    FOREIGN KEY (sport_id) REFERENCES sport_type(sport_id);

-- team -> sport_type (optional, can be NULL if inferred from league)
ALTER TABLE team 
    ADD CONSTRAINT fk_team_sport_id 
    FOREIGN KEY (sport_id) REFERENCES sport_type(sport_id);

-- player -> sport_type
ALTER TABLE player 
    ADD CONSTRAINT fk_player_sport_id 
    FOREIGN KEY (sport_id) REFERENCES sport_type(sport_id);

-- player -> sport_position
ALTER TABLE player 
    ADD CONSTRAINT fk_player_position_id 
    FOREIGN KEY (position_id) REFERENCES sport_position(position_id);

-- game -> sport_type
ALTER TABLE game 
    ADD CONSTRAINT fk_game_sport_id 
    FOREIGN KEY (sport_id) REFERENCES sport_type(sport_id);

-- bets -> sport_type
ALTER TABLE bets 
    ADD CONSTRAINT fk_bets_sport_id 
    FOREIGN KEY (sport_id) REFERENCES sport_type(sport_id);

\echo '✓ Foreign key constraints added'
\echo ''

-- =========================================================
-- STEP 3.3: DROP OLD NFL-SPECIFIC VIEWS
-- =========================================================

\echo 'Dropping old NFL-specific materialized view...'

DROP MATERIALIZED VIEW IF EXISTS player_season_summary CASCADE;

\echo '✓ Old views dropped'
\echo ''

-- =========================================================
-- STEP 3.4: CREATE MULTI-SPORT VIEWS
-- =========================================================

\echo 'Creating new multi-sport views...'

-- =========================================================
-- Generic player season stats (sport-agnostic)
-- =========================================================
CREATE OR REPLACE VIEW v_player_season_stats AS
SELECT 
    ps.player_id,
    ps.season_id,
    ps.team_id,
    p.full_name,
    COALESCE(sp.position_code, p.position) as position,
    p.sport_id,
    st.sport_code,
    st.sport_name,
    t.name AS team_name,
    t.abbrev AS team_abbrev,
    s.year AS season_year,
    ps.stat_group,
    ps.metric_name,
    ps.metric_value,
    -- Try to cast to numeric for aggregation
    CASE 
        WHEN ps.metric_value ~ '^[0-9]+\.?[0-9]*$' 
        THEN ps.metric_value::numeric 
        ELSE NULL 
    END as metric_value_numeric
FROM player_statistic ps
JOIN player p ON ps.player_id = p.player_id
LEFT JOIN sport_position sp ON p.position_id = sp.position_id
JOIN team t ON ps.team_id = t.team_id
JOIN season s ON ps.season_id = s.season_id
JOIN league l ON s.league_id = l.league_id
JOIN sport_type st ON l.sport_id = st.sport_id;

COMMENT ON VIEW v_player_season_stats IS 'Generic player stats view - works for all sports';

-- =========================================================
-- NFL Player Season Summary (materialized)
-- =========================================================
CREATE MATERIALIZED VIEW v_nfl_player_season_summary AS
SELECT 
    player_id,
    season_id,
    team_id,
    full_name,
    position,
    team_name,
    team_abbrev,
    season_year,
    -- Passing
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'passing attempts' THEN metric_value END) as passing_attempts,
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'completions' THEN metric_value END) as completions,
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'yards' THEN metric_value END) as passing_yards,
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'passing touchdowns' THEN metric_value END) as passing_tds,
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'interceptions' THEN metric_value END) as interceptions,
    MAX(CASE WHEN stat_group = 'Passing' AND metric_name = 'quaterback rating' THEN metric_value END) as qb_rating,
    -- Rushing
    MAX(CASE WHEN stat_group = 'Rushing' AND metric_name = 'rushing attempts' THEN metric_value END) as rushing_attempts,
    MAX(CASE WHEN stat_group = 'Rushing' AND metric_name = 'yards' THEN metric_value END) as rushing_yards,
    MAX(CASE WHEN stat_group = 'Rushing' AND metric_name = 'rushing touchdowns' THEN metric_value END) as rushing_tds,
    -- Receiving
    MAX(CASE WHEN stat_group = 'Receiving' AND metric_name = 'receptions' THEN metric_value END) as receptions,
    MAX(CASE WHEN stat_group = 'Receiving' AND metric_name = 'yards' THEN metric_value END) as receiving_yards,
    MAX(CASE WHEN stat_group = 'Receiving' AND metric_name = 'receiving touchdowns' THEN metric_value END) as receiving_tds,
    -- Defense
    MAX(CASE WHEN stat_group = 'Defense' AND metric_name = 'total tackles' THEN metric_value END) as tackles,
    MAX(CASE WHEN stat_group = 'Defense' AND metric_name = 'sacks' THEN metric_value END) as sacks,
    MAX(CASE WHEN stat_group = 'Defense' AND metric_name = 'interceptions' THEN metric_value END) as def_interceptions
FROM v_player_season_stats
WHERE sport_code = 'NFL'
GROUP BY player_id, season_id, team_id, full_name, position, team_name, team_abbrev, season_year;

CREATE INDEX idx_nfl_player_summary_player ON v_nfl_player_season_summary(player_id);
CREATE INDEX idx_nfl_player_summary_season ON v_nfl_player_season_summary(season_id);

COMMENT ON MATERIALIZED VIEW v_nfl_player_season_summary IS 'NFL-specific player stats - refreshed periodically';

-- =========================================================
-- NBA Player Season Summary (materialized)
-- =========================================================
CREATE MATERIALIZED VIEW v_nba_player_season_summary AS
SELECT 
    player_id,
    season_id,
    team_id,
    full_name,
    position,
    team_name,
    team_abbrev,
    season_year,
    -- Scoring
    MAX(CASE WHEN metric_name = 'points' THEN metric_value_numeric END) as points,
    MAX(CASE WHEN metric_name = 'field goals made' THEN metric_value_numeric END) as fgm,
    MAX(CASE WHEN metric_name = 'field goals attempted' THEN metric_value_numeric END) as fga,
    MAX(CASE WHEN metric_name = 'field goal percentage' THEN metric_value_numeric END) as fg_pct,
    MAX(CASE WHEN metric_name = 'three pointers made' THEN metric_value_numeric END) as threes_made,
    MAX(CASE WHEN metric_name = 'three pointers attempted' THEN metric_value_numeric END) as threes_attempted,
    MAX(CASE WHEN metric_name = 'three point percentage' THEN metric_value_numeric END) as three_pct,
    -- Rebounding
    MAX(CASE WHEN metric_name = 'rebounds' THEN metric_value_numeric END) as rebounds,
    MAX(CASE WHEN metric_name = 'offensive rebounds' THEN metric_value_numeric END) as offensive_rebounds,
    MAX(CASE WHEN metric_name = 'defensive rebounds' THEN metric_value_numeric END) as defensive_rebounds,
    -- Playmaking
    MAX(CASE WHEN metric_name = 'assists' THEN metric_value_numeric END) as assists,
    MAX(CASE WHEN metric_name = 'steals' THEN metric_value_numeric END) as steals,
    MAX(CASE WHEN metric_name = 'blocks' THEN metric_value_numeric END) as blocks,
    MAX(CASE WHEN metric_name = 'turnovers' THEN metric_value_numeric END) as turnovers
FROM v_player_season_stats
WHERE sport_code = 'NBA'
GROUP BY player_id, season_id, team_id, full_name, position, team_name, team_abbrev, season_year;

CREATE INDEX idx_nba_player_summary_player ON v_nba_player_season_summary(player_id);
CREATE INDEX idx_nba_player_summary_season ON v_nba_player_season_summary(season_id);

COMMENT ON MATERIALIZED VIEW v_nba_player_season_summary IS 'NBA-specific player stats - refreshed periodically';

-- =========================================================
-- Update existing player odds views to include sport
-- =========================================================
CREATE OR REPLACE VIEW v_player_odds_detailed AS
SELECT 
    po.*,
    p.full_name,
    COALESCE(sp.position_code, p.position) as position,
    g.game_datetime_utc,
    ht.name as home_team,
    at.name as away_team,
    b.name as book_name,
    st.sport_code,
    st.sport_name
FROM player_odds po
JOIN player p ON po.player_id = p.player_id
LEFT JOIN sport_position sp ON p.position_id = sp.position_id
JOIN game g ON po.game_id = g.game_id
JOIN team ht ON g.home_team_id = ht.team_id
JOIN team at ON g.away_team_id = at.team_id
JOIN book b ON po.book_id = b.book_id
LEFT JOIN sport_type st ON g.sport_id = st.sport_id;

-- Sport-specific player odds views
CREATE OR REPLACE VIEW v_nfl_player_odds AS
SELECT * FROM v_player_odds_detailed WHERE sport_code = 'NFL';

CREATE OR REPLACE VIEW v_nba_player_odds AS
SELECT * FROM v_player_odds_detailed WHERE sport_code = 'NBA';

CREATE OR REPLACE VIEW v_mlb_player_odds AS
SELECT * FROM v_player_odds_detailed WHERE sport_code = 'MLB';

-- =========================================================
-- Update v_player_odds_consensus to include sport
-- =========================================================
CREATE OR REPLACE VIEW v_player_odds_consensus AS
SELECT 
    po.player_id,
    p.full_name,
    po.game_id,
    g.game_datetime_utc,
    st.sport_code,
    st.sport_name,
    po.market_key,
    po.bet_type,
    AVG(po.line_value) as avg_line,
    MIN(po.odds_american) as min_odds,
    MAX(po.odds_american) as max_odds,
    COUNT(DISTINCT po.book_id) as book_count,
    MAX(po.pulled_at_utc) as last_update
FROM player_odds po
JOIN player p ON po.player_id = p.player_id
JOIN game g ON po.game_id = g.game_id
LEFT JOIN sport_type st ON g.sport_id = st.sport_id
GROUP BY po.player_id, p.full_name, po.game_id, g.game_datetime_utc, 
         st.sport_code, st.sport_name, po.market_key, po.bet_type;

-- =========================================================
-- Update v_best_odds_finder to include sport
-- =========================================================
CREATE OR REPLACE VIEW v_best_odds_finder AS
WITH ranked_odds AS (
    SELECT 
        po.*,
        p.full_name,
        g.game_datetime_utc,
        st.sport_code,
        st.sport_name,
        b.name as book_name,
        ROW_NUMBER() OVER (
            PARTITION BY po.player_id, po.game_id, po.market_key, po.bet_type
            ORDER BY po.odds_american DESC
        ) as rn
    FROM player_odds po
    JOIN player p ON po.player_id = p.player_id
    JOIN game g ON po.game_id = g.game_id
    LEFT JOIN sport_type st ON g.sport_id = st.sport_id
    JOIN book b ON po.book_id = b.book_id
)
SELECT * FROM ranked_odds WHERE rn = 1;

-- =========================================================
-- Update bankroll views to include sport filtering
-- =========================================================
CREATE OR REPLACE VIEW v_bet_statistics AS
SELECT 
    b.user_id,
    COALESCE(st.sport_code, 'UNKNOWN') as sport_code,
    COALESCE(st.sport_name, 'Unknown Sport') as sport_name,
    COUNT(b.bet_id) as total_bets,
    COUNT(b.bet_id) FILTER (WHERE b.status = 'won') as bets_won,
    COUNT(b.bet_id) FILTER (WHERE b.status = 'lost') as bets_lost,
    COUNT(b.bet_id) FILTER (WHERE b.status = 'push') as bets_push,
    COUNT(b.bet_id) FILTER (WHERE b.status = 'pending') as bets_pending,
    ROUND(
        COUNT(b.bet_id) FILTER (WHERE b.status = 'won')::NUMERIC / 
        NULLIF(COUNT(b.bet_id) FILTER (WHERE b.status IN ('won', 'lost')), 0) * 100, 
    1) as win_rate_percentage,
    SUM(b.stake_amount) as total_staked,
    SUM(b.profit_loss) FILTER (WHERE b.status IN ('won', 'lost', 'push')) as total_profit,
    ROUND(AVG(b.profit_loss) FILTER (WHERE b.status IN ('won', 'lost', 'push')), 2) as avg_profit_per_bet,
    ROUND(
        SUM(b.profit_loss) FILTER (WHERE b.status IN ('won', 'lost', 'push')) / 
        NULLIF(SUM(b.stake_amount), 0) * 100,
    2) as roi_percentage
FROM bets b
LEFT JOIN sport_type st ON b.sport_id = st.sport_id
GROUP BY b.user_id, st.sport_code, st.sport_name;

-- Overall stats (all sports combined)
CREATE OR REPLACE VIEW v_bet_statistics_overall AS
SELECT 
    user_id,
    'ALL' as sport_code,
    'All Sports' as sport_name,
    COUNT(bet_id) as total_bets,
    COUNT(bet_id) FILTER (WHERE status = 'won') as bets_won,
    COUNT(bet_id) FILTER (WHERE status = 'lost') as bets_lost,
    COUNT(bet_id) FILTER (WHERE status = 'push') as bets_push,
    COUNT(bet_id) FILTER (WHERE status = 'pending') as bets_pending,
    ROUND(
        COUNT(bet_id) FILTER (WHERE status = 'won')::NUMERIC / 
        NULLIF(COUNT(bet_id) FILTER (WHERE status IN ('won', 'lost')), 0) * 100, 
    1) as win_rate_percentage,
    SUM(stake_amount) as total_staked,
    SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')) as total_profit,
    ROUND(AVG(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 2) as avg_profit_per_bet,
    ROUND(
        SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')) / 
        NULLIF(SUM(stake_amount), 0) * 100,
    2) as roi_percentage
FROM bets
GROUP BY user_id;

\echo '✓ Multi-sport views created'
\echo ''

COMMIT;

-- =========================================================
-- VERIFICATION
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'Verification'
\echo '=========================================='
\echo ''

-- Check constraints
SELECT 
    'Foreign Keys Added' as check_name,
    COUNT(*) as count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND constraint_name LIKE 'fk_%_sport%';

-- Check views
SELECT 
    'Multi-Sport Views' as check_name,
    COUNT(*) as count
FROM information_schema.views
WHERE table_name LIKE 'v_%'
  AND table_schema = 'public';

-- Check materialized views
SELECT 
    'Sport-Specific Materialized Views' as check_name,
    COUNT(*) as count
FROM pg_matviews
WHERE schemaname = 'public'
  AND matviewname LIKE 'v_%_player%';

\echo ''
\echo '=========================================='
\echo 'Step 3 Complete: Constraints and Views Added'
\echo '=========================================='
\echo ''
\echo 'Database is now fully multi-sport ready!'
\echo ''
\echo 'Summary:'
\echo '  ✓ sport_id is now required'
\echo '  ✓ Foreign keys added'
\echo '  ✓ Old NFL-specific views removed'
\echo '  ✓ New multi-sport views created'
\echo '  ✓ Sport-specific materialized views created'
\echo ''
\echo 'You can now:'
\echo '  - Add new sports (NBA, MLB, etc.)'
\echo '  - Filter by sport_code'
\echo '  - Use sport-specific views'
\echo ''

/*
SUMMARY:
✅ Made sport_id NOT NULL on league and game
✅ Added 6 foreign key constraints
✅ Dropped old player_season_summary
✅ Created v_player_season_stats (generic)
✅ Created v_nfl_player_season_summary (NFL-specific)
✅ Created v_nba_player_season_summary (NBA-specific)
✅ Updated all player odds views with sport filtering
✅ Updated bankroll views with sport filtering

COMPLETE! Schema is now v5.3.0 - Multi-Sport Ready
*/
