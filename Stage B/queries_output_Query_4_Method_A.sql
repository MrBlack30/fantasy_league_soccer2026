-- Query 4: Global Leaderboard (Teams with > 50 points in 2024 leagues)
-- Method A: Explicit INNER JOIN (ANSI Standard, Best Practice)
SELECT ft.team_name, ft.total_points, fl.league_name
FROM FANTASY_TEAM ft
JOIN FANTASY_LEAGUE fl ON ft.league_id = fl.league_id
WHERE ft.total_points > 50
AND EXTRACT(YEAR FROM fl.end_date) = 2024;