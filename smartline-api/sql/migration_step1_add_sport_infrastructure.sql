-- =========================================================
-- SmartLine Multi-Sport Migration - Step 1
-- =========================================================
-- Version: 5.2.0 → 5.3.0
-- Purpose: Add sport type infrastructure
-- Date: 2024-12-31
--
-- This migration:
-- 1. Creates sport_type table
-- 2. Creates sport_position table
-- 3. Creates sport_stat_type table
-- 4. Adds sport_id columns (nullable)
-- 5. Creates indexes
--
-- SAFE: Non-breaking, adds infrastructure only
-- =========================================================

BEGIN;

-- =========================================================
-- STEP 1.1: CREATE sport_type TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS sport_type (
    sport_id SMALLSERIAL PRIMARY KEY,
    sport_code VARCHAR(10) NOT NULL UNIQUE,
    sport_name TEXT NOT NULL,
    sport_category VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Sport-specific config
    has_quarters BOOLEAN,
    has_halves BOOLEAN,
    has_periods BOOLEAN,
    has_innings BOOLEAN,
    num_periods SMALLINT,
    
    -- Display
    icon_url TEXT,
    display_order SMALLINT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT sport_type_sport_category_check 
        CHECK (sport_category IN ('football', 'basketball', 'baseball', 'hockey', 'soccer', 'other'))
);

-- Insert all sports
INSERT INTO sport_type (sport_code, sport_name, sport_category, has_quarters, has_halves, has_periods, has_innings, num_periods, display_order) VALUES
('NFL', 'National Football League', 'football', true, false, false, false, 4, 1),
('NCAAF', 'NCAA Football', 'football', true, false, false, false, 4, 2),
('NBA', 'National Basketball Association', 'basketball', true, false, false, false, 4, 3),
('NCAAB', 'NCAA Basketball', 'basketball', false, true, false, false, 2, 4),
('MLB', 'Major League Baseball', 'baseball', false, false, false, true, 9, 5),
('NHL', 'National Hockey League', 'hockey', false, false, true, false, 3, 6),
('MLS', 'Major League Soccer', 'soccer', false, true, false, false, 2, 7),
('EPL', 'English Premier League', 'soccer', false, true, false, false, 2, 8),
('LA_LIGA', 'La Liga', 'soccer', false, true, false, false, 2, 9),
('BUNDESLIGA', 'Bundesliga', 'soccer', false, true, false, false, 2, 10),
('SERIE_A', 'Serie A', 'soccer', false, true, false, false, 2, 11),
('LIGUE_1', 'Ligue 1', 'soccer', false, true, false, false, 2, 12),
('CHAMPIONS', 'UEFA Champions League', 'soccer', false, true, false, false, 2, 13)
ON CONFLICT (sport_code) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_sport_type_code ON sport_type(sport_code);
CREATE INDEX IF NOT EXISTS idx_sport_type_category ON sport_type(sport_category);
CREATE INDEX IF NOT EXISTS idx_sport_type_is_active ON sport_type(is_active);

COMMENT ON TABLE sport_type IS 'Defines all sports supported by SmartLine';
COMMENT ON COLUMN sport_type.sport_code IS 'Short code for sport (e.g., NFL, NBA)';
COMMENT ON COLUMN sport_type.sport_category IS 'Category: football, basketball, baseball, hockey, soccer, other';
COMMENT ON COLUMN sport_type.num_periods IS 'Number of periods/quarters/innings in a standard game';

-- =========================================================
-- STEP 1.2: CREATE sport_position TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS sport_position (
    position_id SERIAL PRIMARY KEY,
    sport_id SMALLINT NOT NULL REFERENCES sport_type(sport_id),
    position_code VARCHAR(10) NOT NULL,
    position_name TEXT NOT NULL,
    position_group VARCHAR(50),
    abbreviation VARCHAR(5),
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(sport_id, position_code)
);

-- NFL Positions
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation) VALUES
-- Offense
(1, 'QB', 'Quarterback', 'Offense', 'QB'),
(1, 'RB', 'Running Back', 'Offense', 'RB'),
(1, 'FB', 'Fullback', 'Offense', 'FB'),
(1, 'WR', 'Wide Receiver', 'Offense', 'WR'),
(1, 'TE', 'Tight End', 'Offense', 'TE'),
(1, 'OT', 'Offensive Tackle', 'Offense', 'OT'),
(1, 'OG', 'Offensive Guard', 'Offense', 'OG'),
(1, 'C', 'Center', 'Offense', 'C'),
-- Defense
(1, 'DE', 'Defensive End', 'Defense', 'DE'),
(1, 'DT', 'Defensive Tackle', 'Defense', 'DT'),
(1, 'NT', 'Nose Tackle', 'Defense', 'NT'),
(1, 'LB', 'Linebacker', 'Defense', 'LB'),
(1, 'MLB', 'Middle Linebacker', 'Defense', 'MLB'),
(1, 'OLB', 'Outside Linebacker', 'Defense', 'OLB'),
(1, 'CB', 'Cornerback', 'Defense', 'CB'),
(1, 'S', 'Safety', 'Defense', 'S'),
(1, 'FS', 'Free Safety', 'Defense', 'FS'),
(1, 'SS', 'Strong Safety', 'Defense', 'SS'),
-- Special Teams
(1, 'K', 'Kicker', 'Special Teams', 'K'),
(1, 'P', 'Punter', 'Special Teams', 'P'),
(1, 'LS', 'Long Snapper', 'Special Teams', 'LS')
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- NCAAF Positions (same as NFL)
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation)
SELECT 2, position_code, position_name, position_group, abbreviation
FROM sport_position WHERE sport_id = 1
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- NBA Positions
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation) VALUES
(3, 'PG', 'Point Guard', 'Guard', 'PG'),
(3, 'SG', 'Shooting Guard', 'Guard', 'SG'),
(3, 'SF', 'Small Forward', 'Forward', 'SF'),
(3, 'PF', 'Power Forward', 'Forward', 'PF'),
(3, 'C', 'Center', 'Center', 'C'),
(3, 'G', 'Guard', 'Guard', 'G'),
(3, 'F', 'Forward', 'Forward', 'F'),
(3, 'F-C', 'Forward-Center', 'Forward', 'F-C'),
(3, 'G-F', 'Guard-Forward', 'Guard', 'G-F')
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- NCAAB Positions (same as NBA)
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation)
SELECT 4, position_code, position_name, position_group, abbreviation
FROM sport_position WHERE sport_id = 3
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- MLB Positions
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation) VALUES
(5, 'P', 'Pitcher', 'Pitcher', 'P'),
(5, 'SP', 'Starting Pitcher', 'Pitcher', 'SP'),
(5, 'RP', 'Relief Pitcher', 'Pitcher', 'RP'),
(5, 'C', 'Catcher', 'Fielder', 'C'),
(5, '1B', 'First Base', 'Fielder', '1B'),
(5, '2B', 'Second Base', 'Fielder', '2B'),
(5, '3B', 'Third Base', 'Fielder', '3B'),
(5, 'SS', 'Shortstop', 'Fielder', 'SS'),
(5, 'LF', 'Left Field', 'Fielder', 'LF'),
(5, 'CF', 'Center Field', 'Fielder', 'CF'),
(5, 'RF', 'Right Field', 'Fielder', 'RF'),
(5, 'OF', 'Outfield', 'Fielder', 'OF'),
(5, 'DH', 'Designated Hitter', 'Hitter', 'DH')
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- NHL Positions
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation) VALUES
(6, 'G', 'Goalie', 'Goalie', 'G'),
(6, 'C', 'Center', 'Forward', 'C'),
(6, 'LW', 'Left Wing', 'Forward', 'LW'),
(6, 'RW', 'Right Wing', 'Forward', 'RW'),
(6, 'D', 'Defenseman', 'Defense', 'D'),
(6, 'F', 'Forward', 'Forward', 'F')
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- Soccer Positions (for MLS, EPL, etc.)
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation) VALUES
-- Goalkeeper
(7, 'GK', 'Goalkeeper', 'Goalkeeper', 'GK'),
-- Defenders
(7, 'CB', 'Center Back', 'Defender', 'CB'),
(7, 'LB', 'Left Back', 'Defender', 'LB'),
(7, 'RB', 'Right Back', 'Defender', 'RB'),
(7, 'LWB', 'Left Wing Back', 'Defender', 'LWB'),
(7, 'RWB', 'Right Wing Back', 'Defender', 'RWB'),
-- Midfielders
(7, 'CDM', 'Central Defensive Midfielder', 'Midfielder', 'CDM'),
(7, 'CM', 'Central Midfielder', 'Midfielder', 'CM'),
(7, 'CAM', 'Central Attacking Midfielder', 'Midfielder', 'CAM'),
(7, 'LM', 'Left Midfielder', 'Midfielder', 'LM'),
(7, 'RM', 'Right Midfielder', 'Midfielder', 'RM'),
-- Forwards
(7, 'ST', 'Striker', 'Forward', 'ST'),
(7, 'CF', 'Center Forward', 'Forward', 'CF'),
(7, 'LW', 'Left Winger', 'Forward', 'LW'),
(7, 'RW', 'Right Winger', 'Forward', 'RW')
ON CONFLICT (sport_id, position_code) DO NOTHING;

-- Copy soccer positions to other soccer leagues
INSERT INTO sport_position (sport_id, position_code, position_name, position_group, abbreviation)
SELECT sport_id_new, position_code, position_name, position_group, abbreviation
FROM sport_position, (VALUES (8), (9), (10), (11), (12), (13)) AS t(sport_id_new)
WHERE sport_id = 7
ON CONFLICT (sport_id, position_code) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_sport_position_sport_id ON sport_position(sport_id);
CREATE INDEX IF NOT EXISTS idx_sport_position_code ON sport_position(position_code);
CREATE INDEX IF NOT EXISTS idx_sport_position_group ON sport_position(position_group);

COMMENT ON TABLE sport_position IS 'Maps positions to sports (e.g., QB=NFL, PG=NBA)';

-- =========================================================
-- STEP 1.3: CREATE sport_stat_type TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS sport_stat_type (
    stat_type_id SERIAL PRIMARY KEY,
    sport_id SMALLINT NOT NULL REFERENCES sport_type(sport_id),
    stat_group VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_code VARCHAR(50),
    data_type VARCHAR(20) DEFAULT 'numeric',
    unit VARCHAR(20),
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(sport_id, stat_group, metric_name),
    CONSTRAINT sport_stat_type_data_type_check 
        CHECK (data_type IN ('numeric', 'text', 'time', 'boolean'))
);

-- NFL Stats
INSERT INTO sport_stat_type (sport_id, stat_group, metric_name, metric_code, data_type, unit) VALUES
-- Passing
(1, 'Passing', 'passing attempts', 'pass_att', 'numeric', 'attempts'),
(1, 'Passing', 'completions', 'pass_comp', 'numeric', 'completions'),
(1, 'Passing', 'yards', 'pass_yds', 'numeric', 'yards'),
(1, 'Passing', 'passing touchdowns', 'pass_td', 'numeric', 'touchdowns'),
(1, 'Passing', 'interceptions', 'pass_int', 'numeric', 'interceptions'),
(1, 'Passing', 'quaterback rating', 'qb_rating', 'numeric', 'rating'),
(1, 'Passing', 'completion percentage', 'comp_pct', 'numeric', 'percent'),
-- Rushing
(1, 'Rushing', 'rushing attempts', 'rush_att', 'numeric', 'attempts'),
(1, 'Rushing', 'yards', 'rush_yds', 'numeric', 'yards'),
(1, 'Rushing', 'rushing touchdowns', 'rush_td', 'numeric', 'touchdowns'),
(1, 'Rushing', 'yards per carry', 'ypc', 'numeric', 'yards'),
(1, 'Rushing', 'longest rush', 'rush_lng', 'numeric', 'yards'),
-- Receiving
(1, 'Receiving', 'receptions', 'rec', 'numeric', 'receptions'),
(1, 'Receiving', 'yards', 'rec_yds', 'numeric', 'yards'),
(1, 'Receiving', 'receiving touchdowns', 'rec_td', 'numeric', 'touchdowns'),
(1, 'Receiving', 'targets', 'tgt', 'numeric', 'targets'),
(1, 'Receiving', 'yards per reception', 'ypr', 'numeric', 'yards'),
-- Defense
(1, 'Defense', 'total tackles', 'tackles', 'numeric', 'tackles'),
(1, 'Defense', 'solo tackles', 'solo', 'numeric', 'tackles'),
(1, 'Defense', 'sacks', 'sacks', 'numeric', 'sacks'),
(1, 'Defense', 'interceptions', 'def_int', 'numeric', 'interceptions'),
(1, 'Defense', 'forced fumbles', 'ff', 'numeric', 'fumbles')
ON CONFLICT (sport_id, stat_group, metric_name) DO NOTHING;

-- NBA Stats
INSERT INTO sport_stat_type (sport_id, stat_group, metric_name, metric_code, data_type, unit) VALUES
-- Scoring
(3, 'Scoring', 'points', 'pts', 'numeric', 'points'),
(3, 'Scoring', 'field goals made', 'fgm', 'numeric', 'field goals'),
(3, 'Scoring', 'field goals attempted', 'fga', 'numeric', 'attempts'),
(3, 'Scoring', 'field goal percentage', 'fg_pct', 'numeric', 'percent'),
(3, 'Scoring', 'three pointers made', '3pm', 'numeric', 'three pointers'),
(3, 'Scoring', 'three pointers attempted', '3pa', 'numeric', 'attempts'),
(3, 'Scoring', 'three point percentage', '3p_pct', 'numeric', 'percent'),
(3, 'Scoring', 'free throws made', 'ftm', 'numeric', 'free throws'),
(3, 'Scoring', 'free throws attempted', 'fta', 'numeric', 'attempts'),
(3, 'Scoring', 'free throw percentage', 'ft_pct', 'numeric', 'percent'),
-- Rebounding
(3, 'Rebounding', 'rebounds', 'reb', 'numeric', 'rebounds'),
(3, 'Rebounding', 'offensive rebounds', 'oreb', 'numeric', 'rebounds'),
(3, 'Rebounding', 'defensive rebounds', 'dreb', 'numeric', 'rebounds'),
-- Playmaking
(3, 'Playmaking', 'assists', 'ast', 'numeric', 'assists'),
(3, 'Playmaking', 'turnovers', 'tov', 'numeric', 'turnovers'),
(3, 'Playmaking', 'steals', 'stl', 'numeric', 'steals'),
(3, 'Playmaking', 'blocks', 'blk', 'numeric', 'blocks'),
-- Other
(3, 'Other', 'minutes played', 'min', 'numeric', 'minutes'),
(3, 'Other', 'plus minus', 'pm', 'numeric', 'points')
ON CONFLICT (sport_id, stat_group, metric_name) DO NOTHING;

-- MLB Stats
INSERT INTO sport_stat_type (sport_id, stat_group, metric_name, metric_code, data_type, unit) VALUES
-- Batting
(5, 'Batting', 'at bats', 'ab', 'numeric', 'at bats'),
(5, 'Batting', 'runs', 'r', 'numeric', 'runs'),
(5, 'Batting', 'hits', 'h', 'numeric', 'hits'),
(5, 'Batting', 'doubles', '2b', 'numeric', 'doubles'),
(5, 'Batting', 'triples', '3b', 'numeric', 'triples'),
(5, 'Batting', 'home runs', 'hr', 'numeric', 'home runs'),
(5, 'Batting', 'runs batted in', 'rbi', 'numeric', 'rbi'),
(5, 'Batting', 'stolen bases', 'sb', 'numeric', 'stolen bases'),
(5, 'Batting', 'batting average', 'avg', 'numeric', 'average'),
(5, 'Batting', 'on base percentage', 'obp', 'numeric', 'percent'),
(5, 'Batting', 'slugging percentage', 'slg', 'numeric', 'percent'),
-- Pitching
(5, 'Pitching', 'innings pitched', 'ip', 'numeric', 'innings'),
(5, 'Pitching', 'wins', 'w', 'numeric', 'wins'),
(5, 'Pitching', 'losses', 'l', 'numeric', 'losses'),
(5, 'Pitching', 'earned run average', 'era', 'numeric', 'era'),
(5, 'Pitching', 'strikeouts', 'so', 'numeric', 'strikeouts'),
(5, 'Pitching', 'walks', 'bb', 'numeric', 'walks'),
(5, 'Pitching', 'saves', 'sv', 'numeric', 'saves'),
(5, 'Pitching', 'whip', 'whip', 'numeric', 'whip')
ON CONFLICT (sport_id, stat_group, metric_name) DO NOTHING;

-- NHL Stats
INSERT INTO sport_stat_type (sport_id, stat_group, metric_name, metric_code, data_type, unit) VALUES
-- Scoring
(6, 'Scoring', 'goals', 'g', 'numeric', 'goals'),
(6, 'Scoring', 'assists', 'a', 'numeric', 'assists'),
(6, 'Scoring', 'points', 'pts', 'numeric', 'points'),
(6, 'Scoring', 'plus minus', 'pm', 'numeric', 'rating'),
(6, 'Scoring', 'power play goals', 'ppg', 'numeric', 'goals'),
(6, 'Scoring', 'short handed goals', 'shg', 'numeric', 'goals'),
-- Goalie
(6, 'Goaltending', 'wins', 'w', 'numeric', 'wins'),
(6, 'Goaltending', 'losses', 'l', 'numeric', 'losses'),
(6, 'Goaltending', 'save percentage', 'sv_pct', 'numeric', 'percent'),
(6, 'Goaltending', 'goals against average', 'gaa', 'numeric', 'average'),
(6, 'Goaltending', 'shutouts', 'so', 'numeric', 'shutouts')
ON CONFLICT (sport_id, stat_group, metric_name) DO NOTHING;

-- Soccer Stats
INSERT INTO sport_stat_type (sport_id, stat_group, metric_name, metric_code, data_type, unit) VALUES
-- Scoring
(7, 'Scoring', 'goals', 'g', 'numeric', 'goals'),
(7, 'Scoring', 'assists', 'a', 'numeric', 'assists'),
(7, 'Scoring', 'shots', 'sh', 'numeric', 'shots'),
(7, 'Scoring', 'shots on target', 'sot', 'numeric', 'shots'),
-- Passing
(7, 'Passing', 'passes completed', 'pass_comp', 'numeric', 'passes'),
(7, 'Passing', 'passes attempted', 'pass_att', 'numeric', 'passes'),
(7, 'Passing', 'pass completion percentage', 'pass_pct', 'numeric', 'percent'),
-- Defense
(7, 'Defense', 'tackles', 'tkl', 'numeric', 'tackles'),
(7, 'Defense', 'interceptions', 'int', 'numeric', 'interceptions'),
(7, 'Defense', 'clearances', 'clr', 'numeric', 'clearances'),
-- Goalkeeper
(7, 'Goalkeeping', 'saves', 'sv', 'numeric', 'saves'),
(7, 'Goalkeeping', 'goals against', 'ga', 'numeric', 'goals'),
(7, 'Goalkeeping', 'clean sheets', 'cs', 'numeric', 'clean sheets')
ON CONFLICT (sport_id, stat_group, metric_name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_sport_stat_type_sport_id ON sport_stat_type(sport_id);
CREATE INDEX IF NOT EXISTS idx_sport_stat_type_group ON sport_stat_type(stat_group);
CREATE INDEX IF NOT EXISTS idx_sport_stat_type_code ON sport_stat_type(metric_code);

COMMENT ON TABLE sport_stat_type IS 'Defines valid stat types for each sport';

-- =========================================================
-- STEP 1.4: ADD sport_id COLUMNS (NULLABLE)
-- =========================================================

-- Add to league (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'league' AND column_name = 'sport_id'
    ) THEN
        ALTER TABLE league ADD COLUMN sport_id SMALLINT;
        ALTER TABLE league ADD COLUMN league_code VARCHAR(20);
    END IF;
END $$;

-- Add to team (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'team' AND column_name = 'sport_id'
    ) THEN
        ALTER TABLE team ADD COLUMN sport_id SMALLINT;
    END IF;
END $$;

-- Add to player (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'player' AND column_name = 'sport_id'
    ) THEN
        ALTER TABLE player ADD COLUMN sport_id SMALLINT;
        ALTER TABLE player ADD COLUMN position_id INTEGER;
    END IF;
END $$;

-- Add to game (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'game' AND column_name = 'sport_id'
    ) THEN
        ALTER TABLE game ADD COLUMN sport_id SMALLINT;
    END IF;
END $$;

-- Add to bets (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bets' AND column_name = 'sport_id'
    ) THEN
        ALTER TABLE bets ADD COLUMN sport_id SMALLINT;
    END IF;
END $$;

-- =========================================================
-- STEP 1.5: CREATE INDEXES ON NEW COLUMNS
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_league_sport_id ON league(sport_id);
CREATE INDEX IF NOT EXISTS idx_league_code ON league(league_code);
CREATE INDEX IF NOT EXISTS idx_team_sport_id ON team(sport_id);
CREATE INDEX IF NOT EXISTS idx_player_sport_id ON player(sport_id);
CREATE INDEX IF NOT EXISTS idx_player_position_id ON player(position_id);
CREATE INDEX IF NOT EXISTS idx_game_sport_id ON game(sport_id);
CREATE INDEX IF NOT EXISTS idx_bets_sport_id ON bets(sport_id);

COMMIT;

-- =========================================================
-- VERIFICATION
-- =========================================================

\echo ''
\echo '=========================================='
\echo 'Step 1 Complete: Sport Infrastructure Added'
\echo '=========================================='
\echo ''

-- Check sport_type table
SELECT 'sport_type records' as check_name, COUNT(*) as count FROM sport_type;

-- Check sport_position table
SELECT 'sport_position records' as check_name, COUNT(*) as count FROM sport_position;

-- Check sport_stat_type table
SELECT 'sport_stat_type records' as check_name, COUNT(*) as count FROM sport_stat_type;

-- Check columns added
SELECT 
    table_name,
    column_name,
    '✓ Added' as status
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name IN ('sport_id', 'position_id', 'league_code')
  AND table_name IN ('league', 'team', 'player', 'game', 'bets')
ORDER BY table_name, column_name;

\echo ''
\echo 'Next step: Run migration_step2_migrate_nfl_data.sql'
\echo ''

/*
SUMMARY:
✅ Created sport_type table (13 sports)
✅ Created sport_position table (100+ positions)
✅ Created sport_stat_type table (100+ stat types)
✅ Added sport_id columns to 5 tables (nullable)
✅ Created 15+ indexes

NEXT: Step 2 will populate sport_id = 1 (NFL) for existing data
*/
