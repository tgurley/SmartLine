-- =========================================================
-- Sport-Specific Team Extension Tables (v2 - FIXED)
-- =========================================================
-- Version: 5.3.0 → 5.4.0
-- Purpose: Add sport-specific team data tables
-- Date: 2024-12-31
--
-- HANDLES:
-- - Existing coach/owner columns in team table
-- - Existing venue table with different structure
-- =========================================================

BEGIN;

\echo ''
\echo '=========================================='
\echo 'Creating Sport Extension Tables'
\echo '=========================================='
\echo ''

-- =========================================================
-- STEP 1: CREATE EXTENSION TABLES
-- =========================================================

-- NFL TEAM EXTENSIONS
CREATE TABLE IF NOT EXISTS nfl_team_data (
    team_id SMALLINT PRIMARY KEY REFERENCES team(team_id) ON DELETE CASCADE,
    head_coach TEXT,
    team_owner TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nfl_team_data_team_id ON nfl_team_data(team_id);
COMMENT ON TABLE nfl_team_data IS 'NFL-specific team data (head coach, owner)';

-- NBA TEAM EXTENSIONS
CREATE TABLE IF NOT EXISTS nba_team_data (
    team_id SMALLINT PRIMARY KEY REFERENCES team(team_id) ON DELETE CASCADE,
    nickname TEXT,
    conference VARCHAR(10),
    division VARCHAR(20),
    all_star BOOLEAN DEFAULT false,
    nba_franchise BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT nba_team_data_conference_check CHECK (conference IN ('East', 'West')),
    CONSTRAINT nba_team_data_division_check CHECK (division IN (
        'Atlantic', 'Central', 'Southeast', 'Northwest', 'Pacific', 'Southwest'
    ))
);

CREATE INDEX IF NOT EXISTS idx_nba_team_data_team_id ON nba_team_data(team_id);
CREATE INDEX IF NOT EXISTS idx_nba_team_data_conference ON nba_team_data(conference);
CREATE INDEX IF NOT EXISTS idx_nba_team_data_division ON nba_team_data(division);
COMMENT ON TABLE nba_team_data IS 'NBA-specific team data';

-- MLB TEAM EXTENSIONS
CREATE TABLE IF NOT EXISTS mlb_team_data (
    team_id SMALLINT PRIMARY KEY REFERENCES team(team_id) ON DELETE CASCADE,
    league VARCHAR(20),
    division VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT mlb_team_data_league_check CHECK (league IN ('American', 'National')),
    CONSTRAINT mlb_team_data_division_check CHECK (division IN ('East', 'Central', 'West'))
);

CREATE INDEX IF NOT EXISTS idx_mlb_team_data_team_id ON mlb_team_data(team_id);
COMMENT ON TABLE mlb_team_data IS 'MLB-specific team data';

-- NHL TEAM EXTENSIONS
CREATE TABLE IF NOT EXISTS nhl_team_data (
    team_id SMALLINT PRIMARY KEY REFERENCES team(team_id) ON DELETE CASCADE,
    conference VARCHAR(20),
    division VARCHAR(20),
    colors TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT nhl_team_data_conference_check CHECK (conference IN ('Eastern', 'Western')),
    CONSTRAINT nhl_team_data_division_check CHECK (division IN ('Atlantic', 'Metropolitan', 'Central', 'Pacific'))
);

CREATE INDEX IF NOT EXISTS idx_nhl_team_data_team_id ON nhl_team_data(team_id);
COMMENT ON TABLE nhl_team_data IS 'NHL-specific team data';

-- SOCCER TEAM EXTENSIONS
CREATE TABLE IF NOT EXISTS soccer_team_data (
    team_id SMALLINT PRIMARY KEY REFERENCES team(team_id) ON DELETE CASCADE,
    is_national BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_soccer_team_data_team_id ON soccer_team_data(team_id);
COMMENT ON TABLE soccer_team_data IS 'Soccer-specific team data';

\echo '[OK] Extension tables created'
\echo ''

-- =========================================================
-- STEP 2: MIGRATE EXISTING NFL DATA
-- =========================================================

\echo 'Migrating existing NFL data to nfl_team_data...'

INSERT INTO nfl_team_data (team_id, head_coach, team_owner, created_at, updated_at)
SELECT 
    team_id,
    coach,
    owner,
    NOW(),
    NOW()
FROM team
WHERE sport_id = 1
  AND (coach IS NOT NULL OR owner IS NOT NULL)
ON CONFLICT (team_id) DO UPDATE SET
    head_coach = EXCLUDED.head_coach,
    team_owner = EXCLUDED.team_owner,
    updated_at = NOW();

\echo '[OK] NFL data migrated'
\echo ''

-- =========================================================
-- STEP 3: UPGRADE EXISTING VENUE TABLE
-- =========================================================

\echo 'Upgrading venue table...'

-- Add new columns to existing venue table
DO $$ 
BEGIN
    -- Add country columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'country_name') THEN
        ALTER TABLE venue ADD COLUMN country_name TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'country_code') THEN
        ALTER TABLE venue ADD COLUMN country_code VARCHAR(3);
    END IF;
    
    -- Add capacity
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'capacity') THEN
        ALTER TABLE venue ADD COLUMN capacity INTEGER;
    END IF;
    
    -- Rename/upgrade existing columns
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'is_dome') THEN
        -- Add new roof_type column
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'roof_type') THEN
            ALTER TABLE venue ADD COLUMN roof_type VARCHAR(50);
            -- Migrate is_dome to roof_type
            UPDATE venue SET roof_type = CASE WHEN is_dome THEN 'dome' ELSE 'open' END;
        END IF;
    END IF;
    
    -- Rename state to state_province
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'state') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'state_province') THEN
            ALTER TABLE venue RENAME COLUMN state TO state_province;
        END IF;
    END IF;
    
    -- Make state_province nullable (not all venues are in US states)
    ALTER TABLE venue ALTER COLUMN state_province DROP NOT NULL;
    
    -- Rename surface to surface_type
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'surface') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'surface_type') THEN
            ALTER TABLE venue RENAME COLUMN surface TO surface_type;
        END IF;
    END IF;
    
    -- Add other useful columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'latitude') THEN
        ALTER TABLE venue ADD COLUMN latitude DECIMAL(10, 8);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'longitude') THEN
        ALTER TABLE venue ADD COLUMN longitude DECIMAL(11, 8);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'address') THEN
        ALTER TABLE venue ADD COLUMN address TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'opened_year') THEN
        ALTER TABLE venue ADD COLUMN opened_year INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'image_url') THEN
        ALTER TABLE venue ADD COLUMN image_url TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'external_venue_id') THEN
        ALTER TABLE venue ADD COLUMN external_venue_id INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'created_at') THEN
        ALTER TABLE venue ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'venue' AND column_name = 'updated_at') THEN
        ALTER TABLE venue ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_venue_name ON venue(name);
CREATE INDEX IF NOT EXISTS idx_venue_city ON venue(city);
CREATE INDEX IF NOT EXISTS idx_venue_country ON venue(country_code);
CREATE INDEX IF NOT EXISTS idx_venue_external_id ON venue(external_venue_id);

COMMENT ON TABLE venue IS 'Sport-agnostic venue/stadium/arena data';

\echo '[OK] Venue table upgraded'
\echo ''

-- =========================================================
-- STEP 4: ADD venue_id TO TEAM TABLE
-- =========================================================

\echo 'Adding venue_id to team table...'

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'team' AND column_name = 'venue_id'
    ) THEN
        ALTER TABLE team ADD COLUMN venue_id INTEGER REFERENCES venue(venue_id) ON DELETE SET NULL;
        CREATE INDEX idx_team_venue_id ON team(venue_id);
    END IF;
END $$;

-- Mark old columns as deprecated
COMMENT ON COLUMN team.stadium IS 'DEPRECATED: Use venue_id. Kept for backward compatibility.';
COMMENT ON COLUMN team.coach IS 'DEPRECATED: Use nfl_team_data.head_coach. Kept for backward compatibility.';
COMMENT ON COLUMN team.owner IS 'DEPRECATED: Use nfl_team_data.team_owner. Kept for backward compatibility.';

\echo '[OK] venue_id added to team table'
\echo ''

-- =========================================================
-- STEP 5: CREATE VIEWS
-- =========================================================

\echo 'Creating convenience views...'

CREATE OR REPLACE VIEW v_nfl_teams AS
SELECT 
    t.*,
    nfl.head_coach,
    nfl.team_owner,
    v.name as venue_name,
    v.capacity as venue_capacity,
    v.surface_type,
    v.roof_type
FROM team t
LEFT JOIN nfl_team_data nfl ON t.team_id = nfl.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 1;

CREATE OR REPLACE VIEW v_nba_teams AS
SELECT 
    t.*,
    nba.nickname,
    nba.conference,
    nba.division,
    nba.all_star,
    nba.nba_franchise,
    v.name as venue_name,
    v.capacity as venue_capacity
FROM team t
LEFT JOIN nba_team_data nba ON t.team_id = nba.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 3;

CREATE OR REPLACE VIEW v_mlb_teams AS
SELECT 
    t.*,
    mlb.league as mlb_league,
    mlb.division,
    v.name as venue_name,
    v.capacity as venue_capacity
FROM team t
LEFT JOIN mlb_team_data mlb ON t.team_id = mlb.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 5;

CREATE OR REPLACE VIEW v_nhl_teams AS
SELECT 
    t.*,
    nhl.conference,
    nhl.division,
    nhl.colors,
    v.name as venue_name,
    v.capacity as venue_capacity
FROM team t
LEFT JOIN nhl_team_data nhl ON t.team_id = nhl.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id = 6;

CREATE OR REPLACE VIEW v_soccer_teams AS
SELECT 
    t.*,
    soc.is_national,
    v.name as venue_name,
    v.capacity as venue_capacity
FROM team t
LEFT JOIN soccer_team_data soc ON t.team_id = soc.team_id
LEFT JOIN venue v ON t.venue_id = v.venue_id
WHERE t.sport_id IN (7, 8, 9, 10, 11, 12, 13);

\echo '[OK] Views created'
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

\echo 'Extension tables:'
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE '%_team_data'
ORDER BY table_name;

\echo ''
\echo 'Views created:'
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
  AND table_name LIKE 'v_%_teams'
ORDER BY table_name;

\echo ''
\echo 'NFL data migrated:'
SELECT COUNT(*) as nfl_teams_with_extensions FROM nfl_team_data;

\echo ''
\echo 'Venue table columns:'
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'venue' 
ORDER BY ordinal_position;

\echo ''
\echo '=========================================='
\echo 'Migration Complete!'
\echo '=========================================='
\echo ''

/*
SUMMARY:
✅ Created 5 sport-specific extension tables
✅ Migrated existing NFL coach/owner data
✅ Upgraded existing venue table with new columns
✅ Added venue_id to team table
✅ Created 5 convenience views

NEXT: Run team_etl.py to load teams for other sports
*/
