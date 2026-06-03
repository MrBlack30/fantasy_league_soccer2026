-- Update 1: Dynamic Price Update (Increase price by 0.5 for highly selected captains)
UPDATE PLAYER
SET price = price + 0.5
WHERE player_id IN (
    SELECT player_id
    FROM FANTASY_TEAM_SELECTION
    WHERE is_captain = 1
    GROUP BY player_id
    HAVING COUNT(*) > 100
);