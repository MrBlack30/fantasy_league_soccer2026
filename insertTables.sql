-- ============================================================
-- Fantasy Soccer League Database
-- File: insertTables.sql
-- Description: Master data insertion file.
--
-- METHOD 1 (this file): Manual INSERT for all lookup/reference tables.
--   Tables covered: POSITION, MATCH_STATUS
--
-- METHOD 2 (see Programming/generate_data.py):
--   Python script generates bulk INSERT statements.
--   Output file: Programming/python_inserts.sql
--   Tables covered: REAL_TEAM, USERS, PLAYER, GAMEWEEK, MATCH,
--                   FANTASY_LEAGUE, FANTASY_TEAM,
--                   PLAYER_GAMEWEEK_STATS (22,800+ rows),
--                   FANTASY_TEAM_SELECTION (22,500+ rows),
--                   TRANSFER, LEAGUE_STANDING
--
-- METHOD 3 (see DataImportFiles/):
--   CSV import for USERS table.
--   File: DataImportFiles/users.csv
--   Import command: DataImportFiles/import_users.sql
--
-- Execution order:
--   1. Run createTables.sql
--   2. Run this file (insertTables.sql)
--   3. Import CSV: DataImportFiles/import_users.sql
--   4. Run Programming/python_inserts.sql
-- ============================================================


-- ============================================================
-- METHOD 1: Manual INSERT statements
-- ============================================================

-- ------------------------------------------------------------
-- POSITION (4 rows)
-- The 4 positions in soccer fantasy: Goalkeeper, Defender, Midfielder, Forward
-- ------------------------------------------------------------
INSERT INTO POSITION (position_id, position_name, short_name) VALUES
(1, 'Goalkeeper',  'GKP'),
(2, 'Defender',    'DEF'),
(3, 'Midfielder',  'MID'),
(4, 'Forward',     'FWD');


-- ------------------------------------------------------------
-- MATCH_STATUS (5 rows)
-- All possible states a real-world match can be in
-- ------------------------------------------------------------
INSERT INTO MATCH_STATUS (status_id, status_name) VALUES
(1, 'Scheduled'),   -- Match has not started yet
(2, 'Live'),        -- Match is currently in progress
(3, 'Finished'),    -- Match has ended, stats are final
(4, 'Postponed'),   -- Match was delayed to a future date
(5, 'Cancelled');   -- Match was cancelled (not rescheduled)
