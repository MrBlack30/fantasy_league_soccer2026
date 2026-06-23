-- ============================================================
-- AlterTable.sql
-- DDL changes to support Stage D programs
-- ============================================================

-- Add previous_price to PLAYER so the price-change trigger can record
-- the old value before each update (used by trigger1_player_price_change.sql)
ALTER TABLE PLAYER
    ADD COLUMN IF NOT EXISTS previous_price NUMERIC(5,1);

-- Add total_transfers_cost to FANTASY_TEAM to accumulate all transfer
-- spending across the season (used by trigger2_transfer_budget_check.sql)
ALTER TABLE FANTASY_TEAM
    ADD COLUMN IF NOT EXISTS total_transfers_cost NUMERIC(8,1) DEFAULT 0;
