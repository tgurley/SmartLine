-- =========================================================
-- SmartLine (NFL) - PostgreSQL Schema v2
-- =========================================================

BEGIN;

-- ---------- Reference / Dimension Tables ----------

CREATE TABLE league (
  league_id      SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

CREATE TABLE season (
  season_id      SMALLSERIAL PRIMARY KEY,
  league_id      SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  year           SMALLINT NOT NULL,
  UNIQUE (league_id, year)
);

CREATE TABLE team (
  team_id              SMALLSERIAL PRIMARY KEY,
  league_id            SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  name                 TEXT NOT NULL,
  abbrev               TEXT NOT NULL,
  city                 TEXT,
  external_team_key    INTEGER NOT NULL UNIQUE,

  UNIQUE (league_id, abbrev),
  UNIQUE (league_id, name)
);

CREATE TABLE venue (
  venue_id       SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  city           TEXT,
  state          TEXT,
  is_dome        BOOLEAN NOT NULL DEFAULT FALSE,
  surface        TEXT,

  UNIQUE (name, city, state)
);

CREATE TABLE player (
  player_id      BIGSERIAL PRIMARY KEY,
  full_name      TEXT NOT NULL,
  position       TEXT,
  team_id        SMALLINT REFERENCES team(team_id) ON DELETE SET NULL
);

CREATE TABLE book (
  book_id        SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

-- ---------- Core Facts ----------

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

CREATE TABLE game_result (
  game_id         BIGINT PRIMARY KEY REFERENCES game(game_id) ON DELETE CASCADE,
  home_score      SMALLINT NOT NULL CHECK (home_score >= 0),
  away_score      SMALLINT NOT NULL CHECK (away_score >= 0),
  home_win        BOOLEAN GENERATED ALWAYS AS (home_score > away_score) STORED,
  total_points    SMALLINT GENERATED ALWAYS AS (home_score + away_score) STORED
);

-- ---------- Odds ----------

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

-- ---------- Injuries ----------

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

-- ---------- Weather ----------

CREATE TABLE weather_observation (
  obs_id                    BIGSERIAL PRIMARY KEY,
  game_id                   BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  temp_c                    NUMERIC(5,2),
  temp_f                    NUMERIC(5,2),
  wind_mph                  NUMERIC(5,2),
  precip_prob               NUMERIC(5,2) CHECK (precip_prob IS NULL OR (precip_prob BETWEEN 0 AND 100)),
  conditions                TEXT,
  observed_at_utc           TIMESTAMPTZ NOT NULL,
  source                    TEXT,

  is_cold                   BOOLEAN,
  is_hot                    BOOLEAN,
  is_windy                  BOOLEAN,
  is_heavy_wind             BOOLEAN,
  is_rain_risk              BOOLEAN,
  is_storm_risk             BOOLEAN,
  weather_severity_score    SMALLINT CHECK (weather_severity_score BETWEEN 0 AND 100),

  UNIQUE (game_id, observed_at_utc)
);

CREATE INDEX idx_weather_game_time
  ON weather_observation(game_id, observed_at_utc);

-- ---------- Team Game Stats ----------

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

COMMIT;
