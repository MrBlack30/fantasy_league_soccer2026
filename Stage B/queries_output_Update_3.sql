-- Update 3: Auto Status Update (Set past 2023 matches to 'Finished' - status_id 3)
UPDATE MATCH
SET status_id = 3
WHERE match_date < CURRENT_DATE
AND EXTRACT(YEAR FROM match_date) = 2023;