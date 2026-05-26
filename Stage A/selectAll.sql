-- ============================================================
-- Fantasy Soccer League Database
-- File: selectAll.sql
-- Description: SELECT all rows from every table for verification.
-- ============================================================

-- Lookup tables
SELECT * FROM POSITION;
SELECT * FROM MATCH_STATUS;

-- Core entity tables
SELECT * FROM USERS;
SELECT * FROM REAL_TEAM;
SELECT * FROM PLAYER;
SELECT * FROM FANTASY_LEAGUE;
SELECT * FROM FANTASY_TEAM;
SELECT * FROM GAMEWEEK;
SELECT * FROM MATCH;

-- High-volume tables
SELECT * FROM PLAYER_GAMEWEEK_STATS;
SELECT * FROM FANTASY_TEAM_SELECTION;
SELECT * FROM TRANSFER;
SELECT * FROM LEAGUE_STANDING;

-- ============================================================
-- Useful summary counts
-- ============================================================
SELECT 'POSITION'               AS table_name, COUNT(*) AS row_count FROM POSITION
UNION ALL
SELECT 'MATCH_STATUS',           COUNT(*) FROM MATCH_STATUS
UNION ALL
SELECT 'USERS',                  COUNT(*) FROM USERS
UNION ALL
SELECT 'REAL_TEAM',              COUNT(*) FROM REAL_TEAM
UNION ALL
SELECT 'PLAYER',                 COUNT(*) FROM PLAYER
UNION ALL
SELECT 'FANTASY_LEAGUE',         COUNT(*) FROM FANTASY_LEAGUE
UNION ALL
SELECT 'FANTASY_TEAM',           COUNT(*) FROM FANTASY_TEAM
UNION ALL
SELECT 'GAMEWEEK',               COUNT(*) FROM GAMEWEEK
UNION ALL
SELECT 'MATCH',                  COUNT(*) FROM MATCH
UNION ALL
SELECT 'PLAYER_GAMEWEEK_STATS',  COUNT(*) FROM PLAYER_GAMEWEEK_STATS
UNION ALL
SELECT 'FANTASY_TEAM_SELECTION', COUNT(*) FROM FANTASY_TEAM_SELECTION
UNION ALL
SELECT 'TRANSFER',               COUNT(*) FROM TRANSFER
UNION ALL
SELECT 'LEAGUE_STANDING',        COUNT(*) FROM LEAGUE_STANDING;
