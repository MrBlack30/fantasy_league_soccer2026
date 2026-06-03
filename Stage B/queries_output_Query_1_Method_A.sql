-- Query 1: Scouting Screen (Players born in 2002 playing in England)
-- Method A: Using IN clause
SELECT p.first_name, p.last_name, p.price, EXTRACT(YEAR FROM p.birth_date) AS birth_year
FROM PLAYER p
WHERE EXTRACT(YEAR FROM p.birth_date) = 2002
AND p.real_team_id IN (
    SELECT real_team_id
    FROM REAL_TEAM
    WHERE country = 'England'
);