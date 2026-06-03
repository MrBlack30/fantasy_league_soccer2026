-- Update 2: Budget Penalty (Deduct 5 points if spent > 10.0 in January)
UPDATE FANTASY_TEAM
SET total_points = total_points - 5
WHERE team_id IN (
    SELECT t.team_id
    FROM TRANSFER t
    WHERE EXTRACT(MONTH FROM t.transfer_date) = 1
    GROUP BY t.team_id
    HAVING SUM(t.price_paid) > 10.0
);