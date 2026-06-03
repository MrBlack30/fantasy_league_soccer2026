-- Query 7: Live League Table (Rankings for League ID 1, matches played on days 1-15)
SELECT ls.rank, ft.team_name, u.username, ls.points, EXTRACT(DAY FROM gw.start_date) AS gw_start_day
FROM LEAGUE_STANDING ls
JOIN FANTASY_TEAM ft ON ls.team_id = ft.team_id
JOIN USERS u ON ft.user_id = u.user_id
JOIN GAMEWEEK gw ON ls.gameweek_id = gw.gameweek_id
WHERE ls.league_id = 1
AND EXTRACT(DAY FROM gw.start_date) BETWEEN 1 AND 15
ORDER BY ls.rank ASC;