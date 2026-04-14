-- ============================================================
-- Fantasy Soccer League Database
-- File: dropTables.sql
-- Description: Drops all tables in reverse FK dependency order
--              so no constraint violations occur.
-- Run this to completely reset the database schema.
-- ============================================================

-- Leaf tables first (no other tables depend on them)
DROP TABLE IF EXISTS LEAGUE_STANDING;
DROP TABLE IF EXISTS TRANSFER;
DROP TABLE IF EXISTS FANTASY_TEAM_SELECTION;
DROP TABLE IF EXISTS PLAYER_GAMEWEEK_STATS;

-- Mid-level tables
DROP TABLE IF EXISTS MATCH;
DROP TABLE IF EXISTS GAMEWEEK;
DROP TABLE IF EXISTS FANTASY_TEAM;
DROP TABLE IF EXISTS FANTASY_LEAGUE;
DROP TABLE IF EXISTS PLAYER;

-- Root tables
DROP TABLE IF EXISTS REAL_TEAM;
DROP TABLE IF EXISTS USERS;

-- Lookup / ENUM tables
DROP TABLE IF EXISTS MATCH_STATUS;
DROP TABLE IF EXISTS POSITION;
