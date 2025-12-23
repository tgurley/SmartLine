-- =========================================================
-- SmartLine NFL Betting Analytics - Complete Database Schema
-- =========================================================
-- PostgreSQL 15+ 
-- This schema includes all tables, constraints, indexes, and relationships
-- for the SmartLine NFL betting intelligence platform.
--
-- Tables:
--   - Reference/Dimension: league, season, team, venue, book, player
--   - Core Facts: game, game_result, odds_line
--   - Analytics: weather_observation, injury_report, team_game_stat
--   - Game Statistics: game_team_statistics, game_player_statistics (NEW)
--   - Season Statistics: player_statistic
--
-- Last Updated: 2024-12-22
-- =========================================================

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
CREATE TABLE player (
  player_id            BIGSERIAL PRIMARY KEY,
  external_player_id   INTEGER UNIQUE,
  full_name            TEXT NOT NULL,
  position             TEXT,
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
  player_group         TEXT,  -- 'Offense', 'Defense', 'Special Teams'
  
  -- Timestamps
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Sportsbooks
CREATE TABLE book (
  book_id        SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

-- =========================================================
-- CORE FACT TABLES
-- =========================================================

-- Games (scheduled, in progress, final)
CREATE TABLE game (
  game_id              BIGSERIAL PRIMARY KEY,
  season_id            SMALLINT NOT NULL REFERENCES season(season_id) ON DELETE RESTRICT,
  week                 SMALLINT NOT NULL CHECK (week >= 0 AND week <= 25),
  game_datetime_utc    TIMESTAMPTZ NOT NULL,
  home_team_id         SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  away_team_id         SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  venue_id             SMALLINT REFERENCES venue(venue_id) ON DELETE SET NULL,
  status               TEXT NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled','in_progress','final','postponed','canceled')),
  external_game_key    INTEGER UNIQUE,
  
  CHECK (home_team_id <> away_team_id)
);

CREATE INDEX idx_game_season_week ON game(season_id, week);
CREATE INDEX idx_game_datetime ON game(game_datetime_utc);
CREATE INDEX idx_game_home_team ON game(home_team_id);
CREATE INDEX idx_game_away_team ON game(away_team_id);
CREATE INDEX idx_game_status ON game(status);

-- Game Results (scores and outcomes)
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
  ),
  CHECK (
    (market <> 'total') OR (line_value >= 0)
  )
);

CREATE INDEX idx_odds_game_market_side_time
  ON odds_line(game_id, market, side, pulled_at_utc);

CREATE INDEX idx_odds_book_time
  ON odds_line(book_id, pulled_at_utc);

CREATE INDEX idx_odds_game_book
  ON odds_line(game_id, book_id);

-- =========================================================
-- INJURY DATA
-- =========================================================

-- Injury Reports
CREATE TABLE injury_report (
  report_id        BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id          SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  player_id        BIGINT NOT NULL REFERENCES player(player_id) ON DELETE RESTRICT,
  status           TEXT NOT NULL CHECK (status IN ('out','doubtful','questionable','probable','active','inactive','unknown')),
  designation      TEXT,
  updated_at_utc   TIMESTAMPTZ NOT NULL,
  source           TEXT,
  
  UNIQUE (game_id, player_id, updated_at_utc)
);

CREATE INDEX idx_injury_game ON injury_report(game_id);
CREATE INDEX idx_injury_player ON injury_report(player_id);
CREATE INDEX idx_injury_team ON injury_report(team_id);
CREATE INDEX idx_injury_status ON injury_report(status);

-- =========================================================
-- WEATHER DATA
-- =========================================================

-- Weather Observations (venue conditions during games)
CREATE TABLE weather_observation (
  observation_id   BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  observed_at_utc  TIMESTAMPTZ NOT NULL,
  
  -- Weather conditions
  temperature_f    NUMERIC(5,2),
  humidity_pct     NUMERIC(5,2),
  wind_speed_mph   NUMERIC(5,2),
  wind_direction   TEXT,
  precipitation    TEXT,
  condition        TEXT,
  
  source           TEXT,
  
  UNIQUE (game_id, observed_at_utc)
);

CREATE INDEX idx_weather_game ON weather_observation(game_id);
CREATE INDEX idx_weather_time ON weather_observation(observed_at_utc);

-- =========================================================
-- TEAM GAME STATISTICS (Added 2024-12-22)
-- =========================================================

-- Team Game Statistics (individual game performance)
CREATE TABLE team_game_stat (
  stat_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id          SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  
  -- Offensive Stats
  points           SMALLINT,
  first_downs      SMALLINT,
  total_yards      SMALLINT,
  passing_yards    SMALLINT,
  rushing_yards    SMALLINT,
  turnovers        SMALLINT,
  
  -- Defensive Stats
  sacks            NUMERIC(4,1),
  interceptions    SMALLINT,
  fumbles_recovered SMALLINT,
  
  -- Special Teams
  punt_returns     SMALLINT,
  kick_returns     SMALLINT,
  
  -- Metadata
  source           TEXT DEFAULT 'manual',
  pulled_at_utc    TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (game_id, team_id)
);

CREATE INDEX idx_team_game_stat_game ON team_game_stat(game_id);
CREATE INDEX idx_team_game_stat_team ON team_game_stat(team_id);

-- =========================================================
-- GAME TEAM STATISTICS - DETAILED (Added 2024-12-22)
-- =========================================================

-- Detailed Team Statistics per Game (from API-Sports)
CREATE TABLE game_team_statistics (
  stat_id              BIGSERIAL PRIMARY KEY,
  game_id              BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id              SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  
  -- First Downs
  first_downs_total           SMALLINT,
  first_downs_passing         SMALLINT,
  first_downs_rushing         SMALLINT,
  first_downs_from_penalties  SMALLINT,
  third_down_efficiency       TEXT,  -- e.g., "2-12"
  fourth_down_efficiency      TEXT,  -- e.g., "0-0"
  
  -- Plays & Yards
  plays_total                 SMALLINT,
  yards_total                 SMALLINT,
  yards_per_play              NUMERIC(4,1),
  total_drives                NUMERIC(4,1),
  
  -- Passing
  passing_yards               SMALLINT,
  passing_comp_att            TEXT,  -- e.g., "15-26"
  passing_yards_per_pass      NUMERIC(4,1),
  passing_interceptions_thrown SMALLINT,
  passing_sacks_yards_lost    TEXT,  -- e.g., "4-25"
  
  -- Rushing
  rushing_yards               SMALLINT,
  rushing_attempts            SMALLINT,
  rushing_yards_per_rush      NUMERIC(4,1),
  
  -- Red Zone
  red_zone_made_att           TEXT,  -- e.g., "0-1"
  
  -- Penalties
  penalties_total             TEXT,  -- e.g., "9-72"
  
  -- Turnovers
  turnovers_total             SMALLINT,
  turnovers_lost_fumbles      SMALLINT,
  turnovers_interceptions     SMALLINT,
  
  -- Possession
  possession_total            TEXT,  -- e.g., "25:58"
  
  -- Defensive Stats
  interceptions_total         SMALLINT,
  fumbles_recovered_total     SMALLINT,
  sacks_total                 SMALLINT,
  safeties_total              SMALLINT,
  int_touchdowns_total        SMALLINT,
  points_against_total        SMALLINT,
  
  -- Metadata
  source                      TEXT DEFAULT 'api-sports',
  pulled_at_utc               TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT uq_game_team_stat UNIQUE (game_id, team_id)
);

CREATE INDEX idx_game_team_stat_game ON game_team_statistics(game_id);
CREATE INDEX idx_game_team_stat_team ON game_team_statistics(team_id);
CREATE INDEX idx_game_team_stat_game_team ON game_team_statistics(game_id, team_id);
CREATE INDEX idx_game_team_stat_pulled_at ON game_team_statistics(pulled_at_utc);

-- =========================================================
-- GAME PLAYER STATISTICS - DETAILED (Added 2024-12-22)
-- =========================================================

-- Detailed Player Statistics per Game (from API-Sports)
CREATE TABLE game_player_statistics (
  stat_id              BIGSERIAL PRIMARY KEY,
  game_id              BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  player_id            BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  team_id              SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  
  -- Stat grouping (matches API groups)
  stat_group           TEXT NOT NULL CHECK (stat_group IN (
    'Passing', 'Rushing', 'Receiving', 'Defense',
    'Fumbles', 'Interceptions', 'Kicking', 'Punting',
    'Kick Returns', 'Punt Returns'
  )),
  
  -- Flexible metric storage (key-value pairs)
  metric_name          TEXT NOT NULL,
  metric_value         TEXT,  -- Stores numbers, ratios (e.g., "6/12"), or NULL
  
  -- Metadata
  source               TEXT DEFAULT 'api-sports',
  pulled_at_utc        TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT uq_game_player_stat UNIQUE (game_id, player_id, team_id, stat_group, metric_name)
);

CREATE INDEX idx_game_player_stat_game ON game_player_statistics(game_id);
CREATE INDEX idx_game_player_stat_player ON game_player_statistics(player_id);
CREATE INDEX idx_game_player_stat_team ON game_player_statistics(team_id);
CREATE INDEX idx_game_player_stat_game_player ON game_player_statistics(game_id, player_id);
CREATE INDEX idx_game_player_stat_player_group ON game_player_statistics(player_id, stat_group);
CREATE INDEX idx_game_player_stat_group ON game_player_statistics(stat_group);
CREATE INDEX idx_game_player_stat_metric ON game_player_statistics(metric_name);
CREATE INDEX idx_game_player_stat_pulled_at ON game_player_statistics(pulled_at_utc);

-- =========================================================
-- SAMPLE DATA (Optional - for development)
-- =========================================================

-- Insert NFL league
INSERT INTO league (name) VALUES ('NFL') ON CONFLICT (name) DO NOTHING;

-- Insert sample seasons
INSERT INTO season (league_id, year)
SELECT league_id, year
FROM (VALUES
  ((SELECT league_id FROM league WHERE name = 'NFL'), 2023),
  ((SELECT league_id FROM league WHERE name = 'NFL'), 2024)
) AS v(league_id, year)
ON CONFLICT (league_id, year) DO NOTHING;

-- Insert sample sportsbooks
INSERT INTO book (name) VALUES
  ('DraftKings'),
  ('FanDuel'),
  ('BetMGM'),
  ('Caesars'),
  ('PointsBet'),
  ('BetRivers'),
  ('Unibet'),
  ('WynnBet'),
  ('Barstool'),
  ('Bet365')
ON CONFLICT (name) DO NOTHING;

-- =========================================================
-- PLAYER SEASON STATISTICS (Added 2024-12-22)
-- =========================================================

-- Player Statistics (flexible key-value storage for season stats)
CREATE TABLE player_statistic (
  statistic_id    BIGSERIAL PRIMARY KEY,
  player_id       BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  team_id         SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  season_id       SMALLINT NOT NULL REFERENCES season(season_id) ON DELETE CASCADE,
  
  -- Stat categorization
  stat_group      TEXT NOT NULL CHECK (stat_group IN (
    'Passing', 'Rushing', 'Receiving', 'Defense',
    'Kicking', 'Punting', 'Returning', 'Scoring'
  )),
  
  -- Flexible metric storage
  metric_name     TEXT NOT NULL,
  metric_value    TEXT,  -- Stores numbers, percentages, or NULL
  
  -- Metadata
  source          TEXT DEFAULT 'api-sports',
  pulled_at_utc   TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT uq_player_stat UNIQUE (player_id, team_id, season_id, stat_group, metric_name)
);

CREATE INDEX idx_player_stat_player_season ON player_statistic(player_id, season_id);
CREATE INDEX idx_player_stat_player_season_group ON player_statistic(player_id, season_id, stat_group);
CREATE INDEX idx_player_stat_season ON player_statistic(season_id);
CREATE INDEX idx_player_stat_stat_group ON player_statistic(stat_group);
CREATE INDEX idx_player_stat_metric_name ON player_statistic(metric_name);
CREATE INDEX idx_player_stat_pulled_at ON player_statistic(pulled_at_utc);

-- Materialized View: Pre-aggregated season summaries for common queries
CREATE MATERIALIZED VIEW player_season_summary AS
SELECT 
  ps.player_id,
  p.full_name,
  p.position,
  p.player_group,
  s.year as season_year,
  t.name as team_name,
  t.abbrev as team_abbrev,
  
  -- Passing stats
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'yards' THEN ps.metric_value END) as passing_yards,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'passing touchdowns' THEN ps.metric_value END) as passing_tds,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'passing attempts' THEN ps.metric_value END) as passing_attempts,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'completions' THEN ps.metric_value END) as completions,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'interceptions' THEN ps.metric_value END) as interceptions,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'completion pct' THEN ps.metric_value END) as completion_pct,
  MAX(CASE WHEN ps.stat_group = 'Passing' AND ps.metric_name = 'quaterback rating' THEN ps.metric_value END) as qb_rating,
  
  -- Rushing stats
  MAX(CASE WHEN ps.stat_group = 'Rushing' AND ps.metric_name = 'yards' THEN ps.metric_value END) as rushing_yards,
  MAX(CASE WHEN ps.stat_group = 'Rushing' AND ps.metric_name = 'rushing touchdowns' THEN ps.metric_value END) as rushing_tds,
  MAX(CASE WHEN ps.stat_group = 'Rushing' AND ps.metric_name = 'rushing attempts' THEN ps.metric_value END) as rushing_attempts,
  MAX(CASE WHEN ps.stat_group = 'Rushing' AND ps.metric_name = 'yards per rush avg' THEN ps.metric_value END) as yards_per_rush,
  
  -- Receiving stats
  MAX(CASE WHEN ps.stat_group = 'Receiving' AND ps.metric_name = 'receiving yards' THEN ps.metric_value END) as receiving_yards,
  MAX(CASE WHEN ps.stat_group = 'Receiving' AND ps.metric_name = 'receiving touchdowns' THEN ps.metric_value END) as receiving_tds,
  MAX(CASE WHEN ps.stat_group = 'Receiving' AND ps.metric_name = 'receptions' THEN ps.metric_value END) as receptions,
  MAX(CASE WHEN ps.stat_group = 'Receiving' AND ps.metric_name = 'receiving targets' THEN ps.metric_value END) as targets,
  MAX(CASE WHEN ps.stat_group = 'Receiving' AND ps.metric_name = 'yards per reception avg' THEN ps.metric_value END) as yards_per_reception,
  
  -- Defense stats
  MAX(CASE WHEN ps.stat_group = 'Defense' AND ps.metric_name = 'total tackles' THEN ps.metric_value END) as total_tackles,
  MAX(CASE WHEN ps.stat_group = 'Defense' AND ps.metric_name = 'sacks' THEN ps.metric_value END) as sacks,
  MAX(CASE WHEN ps.stat_group = 'Defense' AND ps.metric_name = 'interceptions' THEN ps.metric_value END) as def_interceptions,
  MAX(CASE WHEN ps.stat_group = 'Defense' AND ps.metric_name = 'passes defended' THEN ps.metric_value END) as passes_defended,
  
  -- Metadata
  MAX(ps.pulled_at_utc) as last_updated
  
FROM player_statistic ps
JOIN player p ON ps.player_id = p.player_id
JOIN team t ON ps.team_id = t.team_id
JOIN season s ON ps.season_id = s.season_id
GROUP BY ps.player_id, p.full_name, p.position, p.player_group, s.year, t.name, t.abbrev;

CREATE UNIQUE INDEX idx_player_season_summary_unique ON player_season_summary(player_id, season_year);
CREATE INDEX idx_player_season_summary_season ON player_season_summary(season_year);
CREATE INDEX idx_player_season_summary_position ON player_season_summary(position);

COMMIT;

-- =========================================================
-- POST-CREATION NOTES
-- =========================================================
/*

DATABASE STATISTICS (updated 2024-12-22):
- Tables: 15 (added game_team_statistics, game_player_statistics)
- Materialized Views: 1 (player_season_summary)
- Total Size: ~5 MB base + ~20-30 MB per season with all stats
- Largest Tables (estimated per season): 
  * game_player_statistics: ~100-200 MB per season (100,000-200,000 rows)
  * player_statistic: ~15-20 MB per season (85,000-120,000 rows)
  * odds_line: 1.5 MB (44,411 rows)
  * player: 1.3 MB (2,559 rows)
  * game_team_statistics: ~500 KB per season (~544 rows)
  * team_game_stat: 552 KB
  * game: 136 KB (1,136 rows)

KEY RELATIONSHIPS:
- game references: season, home_team, away_team, venue
- game_result references: game (1:1)
- odds_line references: game, book (many:1)
- weather_observation references: game (many:1)
- player references: team (many:1)
- injury_report references: game, team, player (many:1)
- team_game_stat references: game, team (many:1)
- game_team_statistics references: game, team (many:1) -- NEW
- game_player_statistics references: game, player, team (many:1) -- NEW
- player_statistic references: player, team, season (many:1)

GENERATED COLUMNS:
- game_result.home_win: Computed from home_score > away_score
- game_result.total_points: Computed from home_score + away_score

UNIQUE CONSTRAINTS:
- league.name
- season(league_id, year)
- team.external_team_key
- team(league_id, name)
- team(league_id, abbrev)
- venue(name, city, state)
- player.external_player_id
- game.external_game_key
- book.name
- odds_line(game_id, book_id, market, side, pulled_at_utc)
- weather_observation(game_id, observed_at_utc)
- injury_report(game_id, player_id, updated_at_utc)
- game_team_statistics(game_id, team_id) -- NEW
- game_player_statistics(game_id, player_id, team_id, stat_group, metric_name) -- NEW
- player_statistic(player_id, team_id, season_id, stat_group, metric_name)

ETL PIPELINES:
- nfl_player_etl.py: Loads ~1,700 players per season (32 API requests)
- nfl_team_etl.py: Loads 32 teams with logos (1 API request)
- nfl_player_statistics_etl.py: Loads season player stats (32 API requests per season)
  * Team-based fetching (1 call per team instead of 1 per player)
  * Refreshes materialized view automatically
- nfl_game_team_statistics_etl.py: Loads team game stats (1 API call per game) -- NEW
  * ~272 calls for full regular season
  * Incremental mode only fetches missing games
  * Stores 30+ detailed metrics per team per game
- nfl_game_player_statistics_etl.py: Loads player game stats (1 API call per game) -- NEW
  * ~272 calls for full regular season
  * Flexible key-value schema for any stat type
  * Supports 10 stat groups (Passing, Rushing, Receiving, Defense, etc.)
  * ~100-200K records per full season

STATISTICS COVERAGE:
Season Stats (player_statistic):
- Stat Groups: Passing, Rushing, Receiving, Defense, Kicking, Punting, Returning, Scoring
- Season coverage: 2022+ (API limitation)
- Materialized view for fast queries

Game Team Stats (game_team_statistics):
- Detailed per-game team performance
- 30+ metrics including first downs, yards, turnovers, possession time
- 2 records per game (home + away)

Game Player Stats (game_player_statistics):
- Individual player performance per game
- Flexible schema supports any metric
- 10 stat groups with dynamic metrics
- ~50-80 players per game with stats

FRONTEND INTEGRATION:
Players:
- Player search: /players/search?q={query}
- Player detail: /players/{player_id}
- Season stats: /statistics/players/{player_id}/statistics?season={year}
- Game-by-game: /statistics/players/{player_id}/games?season={year} -- NEW
- Player summary: /statistics/players/{player_id}/summary?season={year} -- NEW
- Leaders: /statistics/players/leaders/{stat_group}/{metric}?season={year} -- NEW

Teams:
- Team search: /teams/search?q={query}
- Team detail: /teams/{team_id}
- Team roster: /teams/{team_id}/roster
- Team game stats: /statistics/teams/{team_id}/games?season={year} -- NEW
- Team leaders: /statistics/teams/leaders/{stat_category}?season={year} -- NEW

Games:
- Game team stats: /statistics/games/{game_id}/teams -- NEW
- Game player stats: /statistics/games/{game_id}/players?stat_group={group} -- NEW

VALIDATION SCRIPTS:
- validate_game_stats.sql: Validates team game statistics
- validate_game_player_stats.sql: Validates player game statistics
- analyze_game_player_stats.sql: Comprehensive analysis with top performers

*/
