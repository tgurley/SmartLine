-- =========================================================
-- SmartLine (NFL) - PostgreSQL Schema v1
-- =========================================================

BEGIN;

-- ---------- Reference / Dimension Tables ----------

CREATE TABLE league (
  league_id      SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL UNIQUE
);

-- Seed later with: NFL
-- INSERT INTO league(name) VALUES ('NFL');

CREATE TABLE season (
  season_id      SMALLSERIAL PRIMARY KEY,
  league_id      SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  year           SMALLINT NOT NULL,
  UNIQUE (league_id, year)
);

CREATE TABLE team (
  team_id        SMALLSERIAL PRIMARY KEY,
  league_id      SMALLINT NOT NULL REFERENCES league(league_id) ON DELETE RESTRICT,
  name           TEXT NOT NULL,
  abbrev         TEXT NOT NULL,
  city           TEXT,
  UNIQUE (league_id, abbrev),
  UNIQUE (league_id, name)
);

CREATE TABLE venue (
  venue_id       SMALLSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  city           TEXT,
  state          TEXT,
  is_dome        BOOLEAN NOT NULL DEFAULT FALSE,
  surface        TEXT
);

CREATE TABLE player (
  player_id      BIGSERIAL PRIMARY KEY,
  full_name      TEXT NOT NULL,
  position       TEXT,
  -- current team (rosters change; later you can add a player_team_history table)
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
  external_game_key    TEXT, -- id from an API provider
  UNIQUE (external_game_key),
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

-- ---------- Odds (Time-Series Snapshots) ----------

CREATE TABLE odds_line (
  line_id          BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  book_id          SMALLINT NOT NULL REFERENCES book(book_id) ON DELETE RESTRICT,

  market           TEXT NOT NULL CHECK (market IN ('spread','total','moneyline')),
  side             TEXT NOT NULL CHECK (side IN ('home','away','over','under')),

  -- For spread/total: line_value is the points (e.g., -3.5, 47.0)
  -- For moneyline: line_value can be NULL and use price_american only
  line_value       NUMERIC(6,2),

  -- American odds, e.g., -110, +135
  price_american   INTEGER NOT NULL CHECK (price_american <> 0 AND price_american BETWEEN -10000 AND 10000),

  pulled_at_utc    TIMESTAMPTZ NOT NULL,
  source           TEXT, -- which API/scraper produced it

  -- Practical uniqueness: one snapshot per timestamp per book/market/side
  UNIQUE (game_id, book_id, market, side, pulled_at_utc),

  -- basic sanity: totals should be non-negative; moneyline usually no line_value
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

-- ---------- Injuries (Time-Series) ----------

CREATE TABLE injury_report (
  report_id        BIGSERIAL PRIMARY KEY,
  game_id          BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id          SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  player_id        BIGINT NOT NULL REFERENCES player(player_id) ON DELETE RESTRICT,

  status           TEXT NOT NULL CHECK (status IN ('out','doubtful','questionable','probable','active','inactive','unknown')),
  designation      TEXT, -- e.g., "Hamstring", "Concussion"
  updated_at_utc   TIMESTAMPTZ NOT NULL,
  source           TEXT,

  -- one status per player per update timestamp for a game
  UNIQUE (game_id, player_id, updated_at_utc)
);

CREATE INDEX idx_injury_game_team_time
  ON injury_report(game_id, team_id, updated_at_utc);

CREATE INDEX idx_injury_player_time
  ON injury_report(player_id, updated_at_utc);

-- ---------- Weather (Time-Series / Observations) ----------

CREATE TABLE weather_observation (
  obs_id          BIGSERIAL PRIMARY KEY,
  game_id         BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,

  temp_f          NUMERIC(5,2),
  wind_mph        NUMERIC(5,2),
  precip_prob     NUMERIC(5,2) CHECK (precip_prob IS NULL OR (precip_prob >= 0 AND precip_prob <= 100)),
  conditions      TEXT,

  observed_at_utc TIMESTAMPTZ NOT NULL,
  source          TEXT,

  UNIQUE (game_id, observed_at_utc)
);

CREATE INDEX idx_weather_game_time
  ON weather_observation(game_id, observed_at_utc);

-- ---------- Team Game Stats (Flexible Metrics) ----------

CREATE TABLE team_game_stat (
  game_id        BIGINT NOT NULL REFERENCES game(game_id) ON DELETE CASCADE,
  team_id        SMALLINT NOT NULL REFERENCES team(team_id) ON DELETE RESTRICT,
  metric         TEXT NOT NULL,            -- e.g., 'yards', 'turnovers', 'epa', 'success_rate'
  value          NUMERIC(12,4) NOT NULL,
  PRIMARY KEY (game_id, team_id, metric)
);

CREATE INDEX idx_team_game_stat_metric
  ON team_game_stat(metric);

CREATE INDEX idx_team_game_stat_team
  ON team_game_stat(team_id);

COMMIT;
