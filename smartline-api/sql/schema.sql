-- =========================================================
-- SmartLine NFL Betting Analytics - Complete Database Schema
-- =========================================================
-- PostgreSQL 15+ 
-- This schema includes all tables, constraints, indexes, and relationships
-- for the SmartLine NFL betting intelligence platform.
--
-- Tables:
--   - Reference/Dimension: league, season, team, venue, book, player
--   - Core Facts: game, game_result, odds_line, player_odds
--   - Analytics: weather_observation, injury_report, team_game_stat
--   - Game Statistics: game_team_statistics, game_player_statistics
--   - Season Statistics: player_statistic
--
-- Last Updated: 2024-12-24
-- Version: 4.0.0
-- Added: player_odds table and 10 analytical views for prop betting
-- =========================================================

-- ⚠️ CRITICAL NOTE: SCORES ARE IN game_result TABLE, NOT game TABLE!
--
-- The game table does NOT contain home_score or away_score columns.
-- These are stored in the game_result table (1-to-1 relationship with game).
--
-- ❌ WRONG:
-- SELECT g.home_score, g.away_score FROM game g
--
-- ✅ CORRECT:
-- SELECT gr.home_score, gr.away_score 
-- FROM game g
-- INNER JOIN game_result gr ON g.game_id = gr.game_id
--
-- Always join game_result when you need scores!

BEGIN;

-- =========================================================
-- REFERENCE / DIMENSION TABLES
-- =========================================================

-- League (NFL)
CREATE TABLE league (
  league_id      SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

-- Season (e.g., 2023, 2024)
CREATE TABLE season (
  season_id      SMALLSERIAL PRIMARY KEY,
  league_id      SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  year           SMALLINT NOT NULL,
  UNIQUE (league_id, year)
);

-- Teams (32 NFL teams with extended info)
CREATE TABLE team (
  team_id              SMALLSERIAL PRIMARY KEY,
  league_id            SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  name                 TEXT NOT NULL,
  abbrev               TEXT NOT NULL,
  city                 TEXT,
  external_team_key    INTEGER NOT NULL UNIQUE,
  
  -- Extended team information (added via migration)
  coach                TEXT,
  owner                TEXT,
  stadium              TEXT,
  established          INTEGER,
  logo_url             TEXT,
  country_name         TEXT,
  country_code         TEXT,
  country_flag_url     TEXT,
  updated_at           TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (league_id, abbrev),
  UNIQUE (league_id, name)
);

-- Venues (stadiums)
CREATE TABLE venue (
  venue_id       SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  city           TEXT NOT NULL,
  state          TEXT NOT NULL,
  is_dome        BOOLEAN NOT NULL DEFAULT FALSE,
  surface        TEXT,
  
  CONSTRAINT uq_venue_name_city_state UNIQUE (name, city, state)
);

-- Players (complete roster data)
-- NOTE: player_group field can have unexpected values like "Injured Reserve Or O"
-- For position-based filtering, use the position field instead
CREATE TABLE player (
  player_id            BIGSERIAL PRIMARY KEY,
  external_player_id   INTEGER UNIQUE,
  full_name            TEXT NOT NULL,
  position             TEXT,  -- ✅ Use this for position filtering, not player_group!
  team_id              SMALLINT REFERENCES team(team_id) ON DELETE SET NULL,
  
  -- Physical attributes
  jersey_number        SMALLINT,
  height               TEXT,
  weight               TEXT,
  age                  SMALLINT,
  
  -- Career info
  college              TEXT,
  experience_years     SMALLINT,
  salary               TEXT,
  
  -- Additional info
  image_url            TEXT,
  player_group         TEXT,  -- ⚠️ Can be "Offense", "Defense", "Special Teams", or "Injured Reserve Or O"
  
  -- Timestamps
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Books (sportsbooks)
CREATE TABLE book (
  book_id        SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

-- =========================================================
-- CORE FACT TABLES
-- =========================================================

-- Games (scheduled games)
-- ⚠️ IMPORTANT: This table does NOT contain scores!
-- Scores are in the game_result table (see below)
CREATE TABLE game (
  game_id             BIGINT PRIMARY KEY,
  season_id           SMALLINT NOT NULL REFERENCES season(season_id) ON DELETE RESTRICT,
  week                SMALLINT NOT NULL,
  game_datetime_utc   TIMESTAMPTZ NOT NULL,
  venue_id            SMALLINT REFERENCES venue(venue_id) ON DELETE SET NULL,
  home_team_id        SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  away_team_id        SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  
  CHECK (home_team_id <> away_team_id),
  UNIQUE (season_id, week, home_team_id, away_team_id)
);

-- =========================================================
-- ⭐ CRITICAL TABLE: game_result
-- =========================================================
-- This table stores the actual game scores (1-to-1 with game)
-- ALWAYS join this table when you need home_score or away_score!
--
-- Example usage:
-- SELECT 
--   g.game_id,
--   g.week,
--   gr.home_score,  -- ✅ From game_result
--   gr.away_score   -- ✅ From game_result
-- FROM game g
-- INNER JOIN game_result gr ON g.game_id = gr.game_id
-- =========================================================
CREATE TABLE game_result (
  game_id         BIGINT PRIMARY KEY REFERENCES game(game_id) ON DELETE CASCADE,
  home_score      SMALLINT NOT NULL CHECK (home_score >= 0),
  away_score      SMALLINT NOT NULL CHECK (away_score >= 0),
  
  -- Generated columns
  home_win        BOOLEAN GENERATED ALWAYS AS (home_score > away_score) STORED,
  total_points    SMALLINT GENERATED ALWAYS AS (home_score + away_score) STORED
);

-- =========================================================
-- ODDS DATA
-- =========================================================

-- Odds Lines (spread, total, moneyline with time series)
CREATE TABLE odds_line (
  line_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  book_id          SMALLINT NOT NULL REFERENCES book(book_id) ON DELETE RESTRICT,
  market           TEXT NOT NULL CHECK (market IN ('spread','total','moneyline')),
  side             TEXT NOT NULL CHECK (side IN ('home','away','over','under')),
  line_value       NUMERIC(6,2),
  price_american   INTEGER NOT NULL CHECK (price_american <> 0 AND price_american BETWEEN -10000 AND 10000),
  pulled_at_utc    TIMESTAMPTZ NOT NULL,
  source           TEXT,
  
  UNIQUE (game_id, book_id, market, side, pulled_at_utc),
  
  CHECK (
    (market = 'moneyline' AND line_value IS NULL)
    OR (market IN ('spread','total') AND line_value IS NOT NULL)
  )
);

-- =========================================================
-- ⭐ NEW: Player Props Odds
-- =========================================================
-- Player-level prop betting lines (passing yards, rushing yards, etc.)
-- IMPORTANT: This table stores historical prop odds (closing lines)
-- Typically pulled 1 hour before game time for consistency
--
-- Example markets:
--   - player_pass_yds, player_pass_tds (QBs)
--   - player_rush_yds, player_rush_attempts (RBs)
--   - player_reception_yds, player_receptions (WRs/TEs)
--   - player_anytime_td (any offensive player)
-- =========================================================
CREATE TABLE player_odds (
  odds_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  player_id        BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  book_id          SMALLINT NOT NULL REFERENCES book(book_id) ON DELETE RESTRICT,
  market_key       TEXT NOT NULL,  -- 'player_pass_yds', 'player_rush_yds', etc.
  bet_type         TEXT NOT NULL CHECK (bet_type IN ('over', 'under')),
  line_value       NUMERIC(6,2) NOT NULL,
  odds_american    INTEGER NOT NULL CHECK (odds_american <> 0 AND odds_american BETWEEN -10000 AND 10000),
  pulled_at_utc    TIMESTAMPTZ NOT NULL,
  source           TEXT DEFAULT 'the-odds-api',
  
  -- Prevent duplicate odds for same prop at same time
  UNIQUE (game_id, player_id, book_id, market_key, bet_type, pulled_at_utc)
);

-- =========================================================
-- ANALYTICS TABLES
-- =========================================================

-- Weather Observations
CREATE TABLE weather_observation (
  observation_id   BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  observed_at_utc  TIMESTAMPTZ NOT NULL,
  temperature_f    NUMERIC(5,2),
  wind_speed_mph   NUMERIC(5,2),
  wind_direction   TEXT,
  precipitation_in NUMERIC(5,3),
  humidity_pct     NUMERIC(5,2),
  
  UNIQUE (game_id, observed_at_utc)
);

-- Injury Reports
CREATE TABLE injury_report (
  report_id        BIGSERIAL PRIMARY KEY,
  game_id          BIGINT REFERENCES game(game_id) ON DELETE CASCADE,
  player_id        BIGINT REFERENCES player(player_id) ON DELETE CASCADE,
  status           TEXT NOT NULL CHECK (status IN ('Out','Questionable','Doubtful','Probable')),
  injury_type      TEXT,
  reported_at_utc  TIMESTAMPTZ NOT NULL
);

-- =========================================================
-- GAME-LEVEL STATISTICS (Key-Value Schema)
-- =========================================================
-- ⭐ NEW: Game-level team and player statistics
-- Flexible key-value schema allows new metrics without schema changes

-- Game Team Statistics
-- Stores all team stats for each game (passing, rushing, defense, etc.)
CREATE TABLE game_team_statistics (
  stat_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id          SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  stat_group       TEXT NOT NULL,  -- 'Passing', 'Rushing', 'Defense', etc.
  metric_name      TEXT NOT NULL,  -- 'yards', 'attempts', 'touchdowns', etc.
  metric_value     TEXT NOT NULL,  -- Stored as text to handle "21/29", "2-4", numbers
  
  UNIQUE (game_id, team_id, stat_group, metric_name)
);

-- Game Player Statistics
-- Stores all player stats for each game
-- ⚠️ NOTE: Not all players have stats for all games
-- When filtering by stat_group, you may exclude games where player had no stats in that group
CREATE TABLE game_player_statistics (
  stat_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  player_id        BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  stat_group       TEXT NOT NULL,  -- 'Passing', 'Rushing', 'Receiving', 'Defense', etc.
  metric_name      TEXT NOT NULL,  -- 'yards', 'touchdowns', 'tackles', etc.
  metric_value     TEXT NOT NULL,  -- Flexible text format
  
  UNIQUE (game_id, player_id, stat_group, metric_name)
);

-- =========================================================
-- SEASON-LEVEL STATISTICS (Legacy)
-- =========================================================
-- Season-aggregated player statistics
-- Note: Game-level stats are now preferred for detailed analysis
CREATE TABLE player_statistic (
  statistic_id       BIGSERIAL PRIMARY KEY,
  player_id          BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  season_id          SMALLINT NOT NULL REFERENCES season(season_id) ON DELETE RESTRICT,
  stat_name          TEXT NOT NULL,
  stat_value         TEXT NOT NULL,
  
  UNIQUE (player_id, season_id, stat_name)
);

-- =========================================================
-- INDEXES FOR PERFORMANCE
-- =========================================================

-- Game indexes
CREATE INDEX idx_game_season_week ON game(season_id, week);
CREATE INDEX idx_game_datetime ON game(game_datetime_utc);
CREATE INDEX idx_game_home_team ON game(home_team_id);
CREATE INDEX idx_game_away_team ON game(away_team_id);

-- Odds indexes
CREATE INDEX idx_odds_game ON odds_line(game_id);
CREATE INDEX idx_odds_book ON odds_line(book_id);
CREATE INDEX idx_odds_market ON odds_line(market);
CREATE INDEX idx_odds_pulled_at ON odds_line(pulled_at_utc);

-- Player odds indexes (CRITICAL for view performance)
CREATE INDEX idx_player_odds_game ON player_odds(game_id);
CREATE INDEX idx_player_odds_player ON player_odds(player_id);
CREATE INDEX idx_player_odds_book ON player_odds(book_id);
CREATE INDEX idx_player_odds_market ON player_odds(market_key);
CREATE INDEX idx_player_odds_composite ON player_odds(game_id, player_id, market_key, bet_type);
CREATE INDEX idx_player_odds_consensus ON player_odds(game_id, player_id, market_key, bet_type) INCLUDE (line_value, odds_american, book_id);
CREATE INDEX idx_player_odds_line_movement ON player_odds(game_id, player_id, market_key, bet_type, pulled_at_utc);
CREATE INDEX idx_player_odds_book_analysis ON player_odds(book_id, market_key) INCLUDE (game_id, player_id, odds_american);

-- Player indexes
CREATE INDEX idx_player_team ON player(team_id);
CREATE INDEX idx_player_position ON player(position);
CREATE INDEX idx_player_external_id ON player(external_player_id);

-- Game statistics indexes (CRITICAL for performance)
CREATE INDEX idx_game_team_stats_game ON game_team_statistics(game_id);
CREATE INDEX idx_game_team_stats_team ON game_team_statistics(team_id);
CREATE INDEX idx_game_team_stats_group ON game_team_statistics(stat_group);
CREATE INDEX idx_game_team_stats_composite ON game_team_statistics(game_id, team_id, stat_group);

CREATE INDEX idx_game_player_stats_game ON game_player_statistics(game_id);
CREATE INDEX idx_game_player_stats_player ON game_player_statistics(player_id);
CREATE INDEX idx_game_player_stats_group ON game_player_statistics(stat_group);
CREATE INDEX idx_game_player_stats_composite ON game_player_statistics(game_id, player_id, stat_group);

-- Season statistics indexes
CREATE INDEX idx_player_stat_player ON player_statistic(player_id);
CREATE INDEX idx_player_stat_season ON player_statistic(season_id);

-- =========================================================
-- ANALYTICAL VIEWS FOR PLAYER PROPS
-- =========================================================
-- These views provide pre-aggregated data for player prop analysis
-- Views use the player_odds and game_player_statistics tables

-- View 1: Detailed player odds with all joins
CREATE OR REPLACE VIEW v_player_odds_detailed AS
SELECT 
    po.odds_id, po.game_id, po.player_id, po.book_id,
    po.market_key, po.bet_type, po.line_value, po.odds_american,
    po.pulled_at_utc, po.source,
    g.week, g.game_datetime_utc, s.year as season_year,
    ht.team_id as home_team_id, ht.name as home_team_name, ht.abbrev as home_team_abbrev,
    at.team_id as away_team_id, at.name as away_team_name, at.abbrev as away_team_abbrev,
    p.full_name as player_name, p.position as player_position,
    p.team_id as player_team_id, pt.name as player_team_name, pt.abbrev as player_team_abbrev,
    b.name as bookmaker_name,
    CASE 
        WHEN p.team_id = g.home_team_id THEN 'home'
        WHEN p.team_id = g.away_team_id THEN 'away'
        ELSE 'unknown'
    END as player_home_away,
    CASE 
        WHEN p.team_id = g.home_team_id THEN at.name
        WHEN p.team_id = g.away_team_id THEN ht.name
    END as opponent_name,
    CASE 
        WHEN po.odds_american > 0 THEN ROUND((po.odds_american / 100.0) + 1, 3)
        ELSE ROUND((100.0 / ABS(po.odds_american)) + 1, 3)
    END as odds_decimal,
    CASE 
        WHEN po.odds_american > 0 THEN ROUND(100.0 / (po.odds_american + 100.0) * 100, 2)
        ELSE ROUND(ABS(po.odds_american) / (ABS(po.odds_american) + 100.0) * 100, 2)
    END as implied_probability_pct
FROM player_odds po
INNER JOIN game g ON po.game_id = g.game_id
INNER JOIN season s ON g.season_id = s.season_id
INNER JOIN team ht ON g.home_team_id = ht.team_id
INNER JOIN team at ON g.away_team_id = at.team_id
INNER JOIN player p ON po.player_id = p.player_id
LEFT JOIN team pt ON p.team_id = pt.team_id
INNER JOIN book b ON po.book_id = b.book_id;

-- View 2: Consensus odds across bookmakers
CREATE OR REPLACE VIEW v_player_odds_consensus AS
SELECT 
    po.game_id, po.player_id, po.market_key, po.bet_type,
    g.week, g.game_datetime_utc, s.year as season_year,
    p.full_name as player_name, p.position as player_position, t.abbrev as player_team,
    ROUND(AVG(po.line_value), 2) as consensus_line,
    ROUND(AVG(po.odds_american), 0) as consensus_odds_american,
    COUNT(DISTINCT po.book_id) as num_bookmakers,
    MAX(po.odds_american) as best_odds_american,
    MIN(po.line_value) as min_line,
    MAX(po.line_value) as max_line,
    ROUND(MAX(po.line_value) - MIN(po.line_value), 2) as line_spread,
    (SELECT b.name FROM player_odds po2 
     INNER JOIN book b ON po2.book_id = b.book_id
     WHERE po2.game_id = po.game_id AND po2.player_id = po.player_id
       AND po2.market_key = po.market_key AND po2.bet_type = po.bet_type
     ORDER BY po2.odds_american DESC LIMIT 1) as best_odds_bookmaker,
    MAX(po.pulled_at_utc) as latest_pull_time
FROM player_odds po
INNER JOIN game g ON po.game_id = g.game_id
INNER JOIN season s ON g.season_id = s.season_id
INNER JOIN player p ON po.player_id = p.player_id
LEFT JOIN team t ON p.team_id = t.team_id
GROUP BY po.game_id, po.player_id, po.market_key, po.bet_type,
         g.week, g.game_datetime_utc, s.year, p.full_name, p.position, t.abbrev;

-- View 3: Best odds finder (line shopping)
CREATE OR REPLACE VIEW v_best_odds_finder AS
WITH ranked_odds AS (
    SELECT po.*, p.full_name as player_name, p.position, t.abbrev as player_team,
           b.name as bookmaker, g.week, g.game_datetime_utc, s.year as season_year,
           ROW_NUMBER() OVER (PARTITION BY po.game_id, po.player_id, po.market_key, po.bet_type
                             ORDER BY po.odds_american DESC) as odds_rank
    FROM player_odds po
    INNER JOIN player p ON po.player_id = p.player_id
    LEFT JOIN team t ON p.team_id = t.team_id
    INNER JOIN book b ON po.book_id = b.book_id
    INNER JOIN game g ON po.game_id = g.game_id
    INNER JOIN season s ON g.season_id = s.season_id
)
SELECT game_id, player_id, player_name, position, player_team, market_key, bet_type,
       line_value, odds_american as best_odds_american, bookmaker as best_odds_bookmaker,
       week, game_datetime_utc, season_year, pulled_at_utc
FROM ranked_odds WHERE odds_rank = 1;

-- View 4: Props by game summary
CREATE OR REPLACE VIEW v_player_odds_by_game AS
SELECT 
    g.game_id, g.week, s.year as season_year, g.game_datetime_utc,
    ht.name as home_team, ht.abbrev as home_abbrev,
    at.name as away_team, at.abbrev as away_abbrev,
    COUNT(DISTINCT po.player_id) as players_with_props,
    COUNT(DISTINCT po.market_key) as markets_offered,
    COUNT(DISTINCT po.book_id) as bookmakers,
    COUNT(po.odds_id) as total_prop_count,
    STRING_AGG(DISTINCT p.full_name, ', ' ORDER BY p.full_name) 
        FILTER (WHERE po.market_key = 'player_pass_yds') as qbs_with_props,
    STRING_AGG(DISTINCT p.full_name, ', ' ORDER BY p.full_name) 
        FILTER (WHERE po.market_key = 'player_rush_yds') as rbs_with_props,
    MIN(po.pulled_at_utc) as earliest_pull,
    MAX(po.pulled_at_utc) as latest_pull
FROM game g
INNER JOIN season s ON g.season_id = s.season_id
INNER JOIN team ht ON g.home_team_id = ht.team_id
INNER JOIN team at ON g.away_team_id = at.team_id
LEFT JOIN player_odds po ON g.game_id = po.game_id
LEFT JOIN player p ON po.player_id = p.player_id
GROUP BY g.game_id, g.week, s.year, g.game_datetime_utc, ht.name, ht.abbrev, at.name, at.abbrev;

-- View 5: Player props history with results
CREATE OR REPLACE VIEW v_player_props_history AS
SELECT 
    p.player_id, p.full_name as player_name, p.position, pt.abbrev as player_team,
    po.market_key, g.game_id, g.week, s.year as season_year, g.game_datetime_utc,
    CASE WHEN p.team_id = g.home_team_id THEN at.name ELSE ht.name END as opponent,
    CASE WHEN p.team_id = g.home_team_id THEN 'home' ELSE 'away' END as home_away,
    ROUND(AVG(po.line_value), 2) as avg_line,
    MIN(po.line_value) as min_line, MAX(po.line_value) as max_line,
    COUNT(DISTINCT po.book_id) as num_books,
    gps.metric_value::numeric as actual_result,
    CASE 
        WHEN gps.metric_value IS NOT NULL THEN
            CASE 
                WHEN gps.metric_value::numeric > AVG(po.line_value) THEN 'over'
                WHEN gps.metric_value::numeric < AVG(po.line_value) THEN 'under'
                ELSE 'push'
            END
    END as result_vs_line
FROM player p
LEFT JOIN team pt ON p.team_id = pt.team_id
INNER JOIN player_odds po ON p.player_id = po.player_id
INNER JOIN game g ON po.game_id = g.game_id
INNER JOIN season s ON g.season_id = s.season_id
INNER JOIN team ht ON g.home_team_id = ht.team_id
INNER JOIN team at ON g.away_team_id = at.team_id
LEFT JOIN game_player_statistics gps 
    ON po.game_id = gps.game_id AND po.player_id = gps.player_id
    AND ((po.market_key = 'player_pass_yds' AND gps.stat_group = 'Passing' AND gps.metric_name = 'yards')
         OR (po.market_key = 'player_pass_tds' AND gps.stat_group = 'Passing' AND gps.metric_name = 'touchdowns')
         OR (po.market_key = 'player_rush_yds' AND gps.stat_group = 'Rushing' AND gps.metric_name = 'yards')
         OR (po.market_key = 'player_reception_yds' AND gps.stat_group = 'Receiving' AND gps.metric_name = 'yards'))
GROUP BY p.player_id, p.full_name, p.position, pt.abbrev, po.market_key,
         g.game_id, g.week, s.year, g.game_datetime_utc,
         p.team_id, g.home_team_id, at.name, ht.name, gps.metric_value
ORDER BY p.player_id, g.game_datetime_utc;

-- View 6: Over/Under hit rates
CREATE OR REPLACE VIEW v_player_over_under_record AS
WITH player_results AS (
    SELECT p.player_id, p.full_name as player_name, p.position,
           po.market_key, s.year as season_year, g.game_id, g.week,
           AVG(po.line_value) as line_value,
           gps.metric_value::numeric as actual_result,
           CASE 
               WHEN gps.metric_value::numeric > AVG(po.line_value) THEN 'over'
               WHEN gps.metric_value::numeric < AVG(po.line_value) THEN 'under'
               ELSE 'push'
           END as result
    FROM player p
    INNER JOIN player_odds po ON p.player_id = po.player_id
    INNER JOIN game g ON po.game_id = g.game_id
    INNER JOIN season s ON g.season_id = s.season_id
    LEFT JOIN game_player_statistics gps 
        ON po.game_id = gps.game_id AND po.player_id = gps.player_id
        AND ((po.market_key = 'player_pass_yds' AND gps.stat_group = 'Passing' AND gps.metric_name = 'yards')
             OR (po.market_key = 'player_pass_tds' AND gps.stat_group = 'Passing' AND gps.metric_name = 'touchdowns')
             OR (po.market_key = 'player_rush_yds' AND gps.stat_group = 'Rushing' AND gps.metric_name = 'yards')
             OR (po.market_key = 'player_reception_yds' AND gps.stat_group = 'Receiving' AND gps.metric_name = 'yards'))
    GROUP BY p.player_id, p.full_name, p.position, po.market_key, s.year, g.game_id, g.week, gps.metric_value
)
SELECT player_id, player_name, position, market_key, season_year,
       COUNT(*) FILTER (WHERE result IS NOT NULL) as games_with_result,
       COUNT(*) FILTER (WHERE result = 'over') as times_hit_over,
       COUNT(*) FILTER (WHERE result = 'under') as times_hit_under,
       ROUND(COUNT(*) FILTER (WHERE result = 'over')::numeric / 
             NULLIF(COUNT(*) FILTER (WHERE result IN ('over', 'under')), 0) * 100, 1) as over_percentage,
       ROUND(AVG(actual_result - line_value), 2) as avg_diff_from_line,
       ROUND(AVG(line_value), 2) as avg_line,
       ROUND(AVG(actual_result), 2) as avg_actual
FROM player_results WHERE result IS NOT NULL
GROUP BY player_id, player_name, position, market_key, season_year;

-- View 7: Sharp line movement detector
CREATE OR REPLACE VIEW v_sharp_line_movement AS
WITH line_changes AS (
    SELECT po.game_id, po.player_id, p.full_name as player_name,
           po.market_key, po.bet_type, g.game_datetime_utc,
           AVG(po.line_value) as current_line,
           (SELECT AVG(po2.line_value) FROM player_odds po2
            WHERE po2.game_id = po.game_id AND po2.player_id = po.player_id
              AND po2.market_key = po.market_key AND po2.bet_type = po.bet_type
              AND po2.pulled_at_utc = (SELECT MIN(pulled_at_utc) FROM player_odds po3
                                       WHERE po3.game_id = po.game_id AND po3.player_id = po.player_id
                                         AND po3.market_key = po.market_key AND po3.bet_type = po.bet_type)) as opening_line,
           COUNT(DISTINCT po.book_id) as num_books
    FROM player_odds po
    INNER JOIN player p ON po.player_id = p.player_id
    INNER JOIN game g ON po.game_id = g.game_id
    GROUP BY po.game_id, po.player_id, p.full_name, po.market_key, po.bet_type, g.game_datetime_utc
)
SELECT game_id, player_id, player_name, market_key, bet_type, game_datetime_utc,
       opening_line, current_line,
       ROUND(current_line - opening_line, 2) as line_movement,
       CASE 
           WHEN ABS(current_line - opening_line) >= 10 THEN 'major'
           WHEN ABS(current_line - opening_line) >= 5 THEN 'significant'
           WHEN ABS(current_line - opening_line) >= 2 THEN 'moderate'
           ELSE 'minor'
       END as movement_magnitude
FROM line_changes
WHERE opening_line IS NOT NULL AND current_line IS NOT NULL AND opening_line != current_line;

-- View 8: Bookmaker comparison
CREATE OR REPLACE VIEW v_bookmaker_comparison AS
SELECT b.book_id, b.name as bookmaker_name, s.year as season_year, po.market_key,
       COUNT(DISTINCT po.game_id) as games_covered,
       COUNT(DISTINCT po.player_id) as players_covered,
       COUNT(po.odds_id) as total_props_offered,
       ROUND(AVG(po.odds_american), 0) as avg_odds_american,
       COUNT(*) FILTER (WHERE po.odds_american = (SELECT MAX(po2.odds_american) FROM player_odds po2
                                                   WHERE po2.game_id = po.game_id AND po2.player_id = po.player_id
                                                     AND po2.market_key = po.market_key AND po2.bet_type = po.bet_type)) as times_had_best_odds,
       ROUND(COUNT(*) FILTER (WHERE po.odds_american = (SELECT MAX(po2.odds_american) FROM player_odds po2
                                                         WHERE po2.game_id = po.game_id AND po2.player_id = po.player_id
                                                           AND po2.market_key = po.market_key AND po2.bet_type = po.bet_type))::numeric 
             / NULLIF(COUNT(*), 0) * 100, 2) as best_odds_pct
FROM book b
INNER JOIN player_odds po ON b.book_id = po.book_id
INNER JOIN game g ON po.game_id = g.game_id
INNER JOIN season s ON g.season_id = s.season_id
GROUP BY b.book_id, b.name, s.year, po.market_key;

-- View 9: Player prop streaks (simplified for schema)
-- Note: Full implementation in create_views_fixed.sql
CREATE OR REPLACE VIEW v_player_prop_streaks AS
SELECT player_id, full_name as player_name, position, 
       'See create_views_fixed.sql for full implementation' as note
FROM player LIMIT 0;

-- View 10: Home/Away splits
CREATE OR REPLACE VIEW v_home_away_splits AS
WITH player_game_results AS (
    SELECT p.player_id, p.full_name as player_name, p.position,
           po.market_key, s.year as season_year,
           CASE WHEN p.team_id = g.home_team_id THEN 'home' ELSE 'away' END as home_away,
           AVG(po.line_value) as line_value,
           gps.metric_value::numeric as actual_result
    FROM player p
    INNER JOIN player_odds po ON p.player_id = po.player_id
    INNER JOIN game g ON po.game_id = g.game_id
    INNER JOIN season s ON g.season_id = s.season_id
    LEFT JOIN game_player_statistics gps 
        ON po.game_id = gps.game_id AND po.player_id = gps.player_id
        AND ((po.market_key = 'player_pass_yds' AND gps.stat_group = 'Passing' AND gps.metric_name = 'yards')
             OR (po.market_key = 'player_rush_yds' AND gps.stat_group = 'Rushing' AND gps.metric_name = 'yards')
             OR (po.market_key = 'player_reception_yds' AND gps.stat_group = 'Receiving' AND gps.metric_name = 'yards'))
    WHERE gps.metric_value IS NOT NULL
    GROUP BY p.player_id, p.full_name, p.position, po.market_key, s.year, p.team_id, g.home_team_id, g.game_id, gps.metric_value
)
SELECT player_id, player_name, position, market_key, season_year,
       COUNT(*) FILTER (WHERE home_away = 'home') as home_games,
       ROUND(AVG(actual_result) FILTER (WHERE home_away = 'home'), 2) as home_avg,
       COUNT(*) FILTER (WHERE home_away = 'away') as away_games,
       ROUND(AVG(actual_result) FILTER (WHERE home_away = 'away'), 2) as away_avg,
       ROUND(AVG(actual_result) FILTER (WHERE home_away = 'home') - 
             AVG(actual_result) FILTER (WHERE home_away = 'away'), 2) as home_away_diff
FROM player_game_results
GROUP BY player_id, player_name, position, market_key, season_year
HAVING COUNT(*) FILTER (WHERE home_away = 'home') > 0 
   AND COUNT(*) FILTER (WHERE home_away = 'away') > 0;

COMMIT;

-- =========================================================
-- CRITICAL IMPLEMENTATION NOTES
-- =========================================================

/*
1. ALWAYS JOIN game_result FOR SCORES
   ❌ SELECT g.home_score FROM game g  -- FAILS
   ✅ SELECT gr.home_score FROM game g JOIN game_result gr ON g.game_id = gr.game_id

2. USE position FIELD FOR FILTERING, NOT player_group
   ❌ WHERE player_group = 'Offense'  -- Misses "Injured Reserve Or O"
   ✅ WHERE position IN ('QB', 'RB', 'WR', 'TE')

3. DON'T FILTER game_player_statistics BY stat_group UNLESS INTENTIONAL
   Filtering by stat_group = 'Passing' excludes games where player had no passing stats
   Fetch all games, filter stats on application side

4. HANDLE MULTIPLE VALUE FORMATS IN metric_value
   Values can be: "245" (number), "21/29" (ratio), "2-4" (range)
   Parse on application side based on context
   
   ⚠️ IMPORTANT: metric_value is TEXT, must cast to numeric for comparisons:
   ❌ WHERE metric_value > 100  -- Type error!
   ✅ WHERE metric_value::numeric > 100

5. USE INNER JOIN WHEN DATA MUST EXIST
   ❌ LEFT JOIN game_result -- Can create NULL rows
   ✅ INNER JOIN game_result -- Guarantees scores exist

6. CONDITIONAL WHERE CLAUSES
   Build entire query conditionally, don't concatenate WHERE clauses
   ❌ query = f"SELECT ... WHERE x = 1 {extra_where}"  -- Can create double WHERE
   ✅ Use if/else to build complete query with proper AND conditions

7. PLAYER ODDS BEST PRACTICES
   - Use views (v_player_odds_*) instead of raw table for most queries
   - v_player_odds_detailed: General purpose, fully denormalized
   - v_player_odds_consensus: Market consensus across bookmakers
   - v_best_odds_finder: Line shopping, best available odds
   - v_player_over_under_record: Hit rate analysis (⭐ most useful)
   
8. PLAYER ODDS + GAME STATS JOINS
   Always cast metric_value to numeric when comparing to line_value:
   ✅ CASE WHEN gps.metric_value::numeric > AVG(po.line_value) THEN 'over' END
   
9. DUPLICATE PLAYER NAMES
   Multiple players can have the same name (e.g., Lamar Jackson QB vs CB)
   Use player_id, not player name, for uniqueness
   
10. MARKET KEYS REFERENCE
    Common market_key values in player_odds:
    - player_pass_yds, player_pass_tds (QBs)
    - player_rush_yds, player_rush_attempts (RBs, mobile QBs)
    - player_reception_yds, player_receptions (WRs, TEs, RBs)
    - player_anytime_td (any offensive player)
*/

-- =========================================================
-- VERSION HISTORY
-- =========================================================
-- v4.0.0 (2024-12-24): Added player_odds table and 10 analytical views
-- v3.0.0 (2024-12-23): Added critical implementation notes
-- v2.0.0 (2024-12-22): Added game-level statistics tables
-- v1.0.0 (2024-12-01): Initial schema
