-- Query 6: User Analytics (Total spent on transfers by users registered in 2023)
SELECT u.username, EXTRACT(MONTH FROM u.registration_date) AS reg_month, SUM(t.price_paid) AS total_spent_on_transfers
FROM USERS u
JOIN FANTASY_TEAM ft ON u.user_id = ft.user_id
JOIN TRANSFER t ON ft.team_id = t.team_id
WHERE EXTRACT(YEAR FROM u.registration_date) = 2023
GROUP BY u.username, u.registration_date
ORDER BY total_spent_on_transfers DESC;