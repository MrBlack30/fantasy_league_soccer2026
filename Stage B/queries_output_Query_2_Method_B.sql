-- Query 2: Admin Screen (Teams with budget > average budget of August leagues)
-- Method B: Using Virtual Table (Derived Table) in FROM clause
SELECT ft.team_name, ft.budget_remaining, u.username
FROM FANTASY_TEAM ft
JOIN USERS u ON ft.user_id = u.user_id
JOIN (
    SELECT AVG(budget_remaining) AS avg_budget
    FROM FANTASY_TEAM ft_sub
    JOIN FANTASY_LEAGUE fl_sub ON ft_sub.league_id = fl_sub.league_id
    WHERE EXTRACT(MONTH FROM fl_sub.start_date) = 8
) avg_table ON ft.budget_remaining > avg_table.avg_budget
ORDER BY ft.budget_remaining DESC;