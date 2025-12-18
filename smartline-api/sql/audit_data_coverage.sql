--HIGH LEVEL ROW COUNTS
SELECT 'league' AS table_name, COUNT(*) AS rows FROM league
UNION ALL
SELECT 'season', COUNT(*) FROM season
UNION ALL
SELECT 'team', COUNT(*) FROM team
UNION ALL
SELECT 'venue', COUNT(*) FROM venue
UNION ALL
SELECT 'player', COUNT(*) FROM player
UNION ALL
SELECT 'book', COUNT(*) FROM book
UNION ALL
SELECT 'game', COUNT(*) FROM game
UNION ALL
SELECT 'game_result', COUNT(*) FROM game_result
UNION ALL
SELECT 'team_game_stat', COUNT(*) FROM team_game_stat
UNION ALL
SELECT 'odds_line', COUNT(*) FROM odds_line
UNION ALL
SELECT 'injury_report', COUNT(*) FROM injury_report
UNION ALL
SELECT 'weather_observation', COUNT(*) FROM weather_observation
ORDER BY table_name;

--CORE INTEGRITY CHECKS (MUST ALL BE ZERO)
SELECT COUNT(*) AS games_missing_results
FROM game g
LEFT JOIN game_result r ON r.game_id = g.game_id
WHERE r.game_id IS NULL;

--GAMES MISSING TEAM STATS
SELECT COUNT(DISTINCT g.game_id) AS games_missing_team_stats
FROM game g
LEFT JOIN team_game_stat tgs ON tgs.game_id = g.game_id
WHERE tgs.game_id IS NULL;

--TEAM STATS COMPLETENESS CHECK
SELECT
  game_id,
  COUNT(DISTINCT team_id) AS teams_with_stats
FROM team_game_stat
GROUP BY game_id
HAVING COUNT(DISTINCT team_id) <> 2
ORDER BY game_id;

--METRIC COVERAGE
SELECT
  metric,
  COUNT(*) AS rows,
  COUNT(DISTINCT game_id) AS games_covered
FROM team_game_stat
GROUP BY metric
ORDER BY metric;

--SEASON COVERAGE AUDIT
SELECT
  s.year,
  COUNT(DISTINCT g.game_id) AS games,
  COUNT(DISTINCT r.game_id) AS games_with_results,
  COUNT(DISTINCT tgs.game_id) AS games_with_team_stats
FROM season s
LEFT JOIN game g ON g.season_id = s.season_id
LEFT JOIN game_result r ON r.game_id = g.game_id
LEFT JOIN team_game_stat tgs ON tgs.game_id = g.game_id
GROUP BY s.year
ORDER BY s.year;