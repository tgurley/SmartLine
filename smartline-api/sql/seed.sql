/* ============================
   SmartLine – Reference Seeds
   Phase 2 (Schema-Aware)
   ============================ */

BEGIN;

/* ---------- League ---------- */
INSERT INTO league (name)
SELECT 'NFL'
WHERE NOT EXISTS (
  SELECT 1 FROM league WHERE name = 'NFL'
);

/* ---------- Season ---------- */
INSERT INTO season (league_id, year)
SELECT league_id, 2024
FROM league
WHERE name = 'NFL'
  AND NOT EXISTS (
    SELECT 1 FROM season
    WHERE league_id = league.league_id
      AND year = 2024
  );

/* ---------- Sportsbooks ---------- */
INSERT INTO book (name)
SELECT v.name
FROM (
  VALUES
    ('DraftKings'),
    ('FanDuel'),
    ('BetMGM'),
    ('Caesars'),
    ('PointsBet')
) v(name)
WHERE NOT EXISTS (
  SELECT 1 FROM book b WHERE b.name = v.name
);

/* ---------- Teams ---------- */
INSERT INTO team (league_id, name, abbrev, city)
SELECT l.league_id, t.name, t.abbrev, t.city
FROM (
  VALUES
    ('Kansas City Chiefs', 'KC', 'Kansas City'),
    ('Buffalo Bills', 'BUF', 'Buffalo'),
    ('San Francisco 49ers', 'SF', 'San Francisco'),
    ('Dallas Cowboys', 'DAL', 'Dallas'),
    ('Philadelphia Eagles', 'PHI', 'Philadelphia')
) AS t(name, abbrev, city)
JOIN league l ON l.name = 'NFL'
WHERE NOT EXISTS (
  SELECT 1
  FROM team tm
  WHERE tm.league_id = l.league_id
    AND tm.abbrev = t.abbrev
);

/* ---------- Venues ---------- */
INSERT INTO venue (name, city, state, is_dome, surface)
SELECT v.name, v.city, v.state, v.is_dome, v.surface
FROM (
  VALUES
    ('Arrowhead Stadium', 'Kansas City', 'MO', FALSE, 'grass'),
    ('Highmark Stadium', 'Orchard Park', 'NY', FALSE, 'grass'),
    ('Levi''s Stadium', 'Santa Clara', 'CA', FALSE, 'grass'),
    ('AT&T Stadium', 'Arlington', 'TX', TRUE, 'turf'),
    ('Lincoln Financial Field', 'Philadelphia', 'PA', FALSE, 'grass')
) v(name, city, state, is_dome, surface)
WHERE NOT EXISTS (
  SELECT 1 FROM venue ve WHERE ve.name = v.name
);

COMMIT;
