-- Query 3: Transfer History (Managers who never made a transfer on the 1st of the month)
-- Method B: Using NOT EXISTS (Handles NULLs better, faster execution)
SELECT u.username, u.email
FROM USERS u
WHERE NOT EXISTS (
    SELECT 1
    FROM TRANSFER t
    JOIN FANTASY_TEAM ft ON t.team_id = ft.team_id
    WHERE ft.user_id = u.user_id
    AND EXTRACT(DAY FROM t.transfer_date) = 1
);