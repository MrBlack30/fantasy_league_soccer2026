-- Query 4: Global Leaderboard (Teams with > 50 points in 2024 leagues)
-- Method B: Implicit JOIN in WHERE clause (Old style)
SELECT ft.team_name, ft.total_points, fl.league_name
FROM FANTASY_TEAM ft, FANTASY_LEAGUE fl
WHERE ft.league_id = fl.league_id
AND ft.total_points > 50
AND EXTRACT(YEAR FROM fl.end_date) = 2024;