-- Delete 2: Remove Selections for Cancelled Matches (Assuming status_id 5 is Cancelled)
DELETE FROM FANTASY_TEAM_SELECTION
WHERE (player_id, gameweek_id) IN (
    SELECT pgs.player_id, pgs.gameweek_id
    FROM PLAYER_GAMEWEEK_STATS pgs
    JOIN MATCH m ON pgs.match_id = m.match_id
    WHERE m.status_id = 5
);