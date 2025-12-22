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

-- =========================================================
-- WEATHER DATA
-- =========================================================

-- Weather Observations (with severity scoring)
CREATE TABLE weather_observation (
  obs_id                    BIGSERIAL PRIMARY KEY,
  game_id                   BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  
  -- Core weather data
  temp_f                    NUMERIC(5,2) CHECK (temp_f IS NULL OR (temp_f > -40 AND temp_f < 130)),
  temp_c                    NUMERIC(5,2),
  wind_mph                  NUMERIC(5,2),
  precip_prob               NUMERIC(5,2) CHECK (precip_prob IS NULL OR (precip_prob BETWEEN 0 AND 100)),
  precip_mm                 NUMERIC,
  conditions                TEXT,
  
  -- Metadata
  observed_at_utc           TIMESTAMPTZ NOT NULL,
  source                    TEXT,
  
  -- Computed flags
  is_cold                   BOOLEAN,
  is_hot                    BOOLEAN,
  is_windy                  BOOLEAN,
  is_heavy_wind             BOOLEAN,
  is_rain_risk              BOOLEAN,
  is_storm_risk             BOOLEAN,
  weather_severity_score    SMALLINT CHECK (weather_severity_score IS NULL OR (weather_severity_score BETWEEN 0 AND 100)),
  
  UNIQUE (game_id, observed_at_utc)
);

CREATE INDEX idx_weather_game_time
  ON weather_observation(game_id, observed_at_utc);

CREATE INDEX idx_weather_severity
  ON weather_observation(weather_severity_score)
  WHERE weather_severity_score IS NOT NULL;

-- =========================================================
-- TEAM STATISTICS
-- =========================================================

-- Team Game Stats (flexible key-value for any metric)
CREATE TABLE team_game_stat (
  game_id        BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id        SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  metric         TEXT NOT NULL,
  value          NUMERIC(12,4) NOT NULL,
  
  PRIMARY KEY (game_id, team_id, metric)
);

CREATE INDEX idx_team_game_stat_metric
  ON team_game_stat(metric);

CREATE INDEX idx_team_game_stat_team
  ON team_game_stat(team_id);

-- =========================================================
-- ADDITIONAL PERFORMANCE INDEXES
-- =========================================================

-- Player indexes for search and filtering
CREATE INDEX idx_player_full_name ON player(full_name);
CREATE INDEX idx_player_team ON player(team_id);
CREATE INDEX idx_player_position ON player(position);
CREATE INDEX idx_player_external ON player(external_player_id);

-- Team indexes for search
CREATE INDEX idx_team_name ON team(name);
CREATE INDEX idx_team_abbrev ON team(abbrev);
CREATE INDEX idx_team_external ON team(external_team_key);

-- =========================================================
-- COMMENTS (Documentation)
-- =========================================================

COMMENT ON TABLE league IS 'Sports leagues (NFL)';
COMMENT ON TABLE season IS 'Season years for each league';
COMMENT ON TABLE team IS 'NFL teams with extended information including logos, coaches, and stadiums';
COMMENT ON TABLE venue IS 'Stadiums where games are played';
COMMENT ON TABLE player IS 'Complete player roster data with physical attributes and career info';
COMMENT ON TABLE book IS 'Sportsbooks providing odds';
COMMENT ON TABLE game IS 'Scheduled NFL games';
COMMENT ON TABLE game_result IS 'Final scores and computed outcomes';
COMMENT ON TABLE odds_line IS 'Time-series odds data from multiple sportsbooks';
COMMENT ON TABLE injury_report IS 'Player injury status reports';
COMMENT ON TABLE weather_observation IS 'Weather conditions at game time with severity scoring';
COMMENT ON TABLE team_game_stat IS 'Flexible team performance metrics';

COMMENT ON COLUMN team.external_team_key IS 'API sports team ID (1-32 for NFL)';
COMMENT ON COLUMN team.logo_url IS 'URL to team logo image from API';
COMMENT ON COLUMN team.coach IS 'Current head coach name';
COMMENT ON COLUMN team.owner IS 'Team owner(s)';
COMMENT ON COLUMN team.stadium IS 'Home stadium name';
COMMENT ON COLUMN team.established IS 'Year team was established';

COMMENT ON COLUMN player.external_player_id IS 'API sports player ID';
COMMENT ON COLUMN player.player_group IS 'Position group: Offense, Defense, or Special Teams';
COMMENT ON COLUMN player.image_url IS 'URL to player headshot from API';

COMMENT ON COLUMN game.week IS 'Week number (0-25, including playoffs)';
COMMENT ON COLUMN game.status IS 'Game status: scheduled, in_progress, final, postponed, canceled';
COMMENT ON COLUMN game.external_game_key IS 'API sports game ID';

COMMENT ON COLUMN game_result.home_win IS 'Generated: TRUE if home team won';
COMMENT ON COLUMN game_result.total_points IS 'Generated: Sum of home and away scores';

COMMENT ON COLUMN odds_line.market IS 'Bet type: spread, total, or moneyline';
COMMENT ON COLUMN odds_line.side IS 'Bet side: home, away, over, under';
COMMENT ON COLUMN odds_line.line_value IS 'Point spread or total line (NULL for moneyline)';
COMMENT ON COLUMN odds_line.price_american IS 'American odds format (e.g., -110, +150)';
COMMENT ON COLUMN odds_line.pulled_at_utc IS 'Timestamp when odds were captured';

COMMENT ON COLUMN weather_observation.weather_severity_score IS 'Computed severity (0-100): 0=clear, 1-2=light, 3-4=moderate, 5+=severe';
COMMENT ON COLUMN weather_observation.is_cold IS 'Temperature < 32°F';
COMMENT ON COLUMN weather_observation.is_hot IS 'Temperature > 85°F';
COMMENT ON COLUMN weather_observation.is_windy IS 'Wind > 15 mph';
COMMENT ON COLUMN weather_observation.is_heavy_wind IS 'Wind > 25 mph';

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

COMMIT;

-- =========================================================
-- POST-CREATION NOTES
-- =========================================================
/*

DATABASE STATISTICS (as of extraction):
- Tables: 12
- Total Size: ~3.9 MB
- Largest Tables: 
  * odds_line: 1.5 MB (44,411 rows)
  * player: 1.3 MB (2,559 rows)
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

ETL PIPELINES:
- nfl_player_etl.py: Loads ~1,700 players per season (32 API requests)
- nfl_team_etl.py: Loads 32 teams with logos (1 API request)
- Filters out Pro Bowl teams (AFC, NFC)

FRONTEND INTEGRATION:
- Player search: /players/search?q={query}
- Player detail: /players/{player_id}
- Team search: /teams/search?q={query}
- Team detail: /teams/{team_id}
- Team roster: /teams/{team_id}/roster

*/