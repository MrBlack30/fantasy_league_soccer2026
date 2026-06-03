-- Query 5: Team of the Month (Total goals by nationality in December, >10 goals)
SELECT p.nationality, SUM(pgs.goals_scored) AS total_goals_december, COUNT(p.player_id) AS players_involved
FROM PLAYER p
JOIN PLAYER_GAMEWEEK_STATS pgs ON p.player_id = pgs.player_id
JOIN MATCH m ON pgs.match_id = m.match_id
WHERE EXTRACT(MONTH FROM m.match_date) = 12
GROUP BY p.nationality
HAVING SUM(pgs.goals_scored) > 10
ORDER BY total_goals_december DESC;