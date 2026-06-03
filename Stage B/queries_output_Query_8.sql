-- Query 8: Real Club Stats (Teams founded before 1900 and their most expensive player)
SELECT rt.team_name, rt.founded_year, COUNT(p.player_id) AS num_of_players, MAX(p.price) AS most_expensive_player
FROM REAL_TEAM rt
JOIN PLAYER p ON rt.real_team_id = p.real_team_id
WHERE rt.founded_year < 1900
GROUP BY rt.team_name, rt.founded_year
ORDER BY most_expensive_player DESC;