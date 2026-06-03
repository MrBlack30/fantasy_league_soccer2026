-- Delete 1: Clean Ghost Teams (Delete teams of old users who never selected a squad)
DELETE FROM FANTASY_TEAM
WHERE user_id IN (
    SELECT user_id FROM USERS WHERE EXTRACT(YEAR FROM registration_date) < 2020
)
AND team_id NOT IN (
    SELECT DISTINCT team_id FROM FANTASY_TEAM_SELECTION
);