-- Delete 3: Transfer History Archive (Delete transfers from leagues ended before 2023)
DELETE FROM TRANSFER
WHERE team_id IN (
    SELECT ft.team_id
    FROM FANTASY_TEAM ft
    JOIN FANTASY_LEAGUE fl ON ft.league_id = fl.league_id
    WHERE EXTRACT(YEAR FROM fl.end_date) < 2023
);