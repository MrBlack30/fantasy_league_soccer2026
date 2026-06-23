-- ============================================================
-- trigger2_transfer_budget_check.sql
-- Trigger: trg_transfer_budget_check
-- Fires:   BEFORE INSERT ON TRANSFER (for each row)
--
-- Description:
--   Validates that a fantasy team can afford a new transfer before
--   the row is inserted into the TRANSFER table.
--     1. Fetches the team's current budget_remaining (implicit cursor).
--     2. Fetches the incoming player's name (implicit cursor).
--     3. If budget < price_paid → RAISE EXCEPTION to abort the INSERT.
--     4. If budget is sufficient → deducts the cost from budget_remaining
--        and adds it to total_transfers_cost (DML UPDATE).
--     5. Raises a NOTICE confirming the approved transfer.
--
-- Elements used:
--   * Implicit cursor  (SELECT INTO for budget and player lookups)
--   * Branching        (IF NOT FOUND, IF budget insufficient)
--   * DML              (UPDATE FANTASY_TEAM)
--   * Exception        (RAISE EXCEPTION on missing team/player or low budget)
-- ============================================================

CREATE OR REPLACE FUNCTION trg_fn_validate_transfer()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_budget      NUMERIC(6,1);
    v_team_name   VARCHAR(100);
    v_player_in   TEXT;
    v_player_out  TEXT;
BEGIN
    -- Implicit cursor 1: fetch team budget
    SELECT ft.budget_remaining, ft.team_name
    INTO   v_budget, v_team_name
    FROM   FANTASY_TEAM ft
    WHERE  ft.team_id = NEW.team_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: fantasy team ID % not found.', NEW.team_id;
    END IF;

    -- Implicit cursor 2: fetch incoming player name
    SELECT first_name || ' ' || last_name
    INTO   v_player_in
    FROM   PLAYER
    WHERE  player_id = NEW.player_in_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: incoming player ID % not found.', NEW.player_in_id;
    END IF;

    -- Implicit cursor 3: fetch outgoing player name (for the notice message)
    SELECT first_name || ' ' || last_name
    INTO   v_player_out
    FROM   PLAYER
    WHERE  player_id = NEW.player_out_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: outgoing player ID % not found.', NEW.player_out_id;
    END IF;

    -- Budget check: block the transfer if the team cannot afford it
    IF v_budget < NEW.price_paid THEN
        RAISE EXCEPTION
            'Transfer rejected: team "%" has insufficient budget. '
            'Available: £%m  |  Required: £%m  |  Shortfall: £%m',
            v_team_name,
            v_budget,
            NEW.price_paid,
            (NEW.price_paid - v_budget);
    END IF;

    -- DML: deduct cost from budget and accumulate season spend
    UPDATE FANTASY_TEAM
    SET    budget_remaining     = budget_remaining - NEW.price_paid,
           total_transfers_cost = COALESCE(total_transfers_cost, 0) + NEW.price_paid
    WHERE  team_id = NEW.team_id;

    RAISE NOTICE
        'Transfer approved [team "%"]: OUT % → IN % for £%m  (budget left: £%m)',
        v_team_name,
        v_player_out,
        v_player_in,
        NEW.price_paid,
        (v_budget - NEW.price_paid);

    RETURN NEW;
END;
$$;

-- Drop and recreate the trigger to ensure a clean state
DROP TRIGGER IF EXISTS trg_transfer_budget_check ON TRANSFER;

CREATE TRIGGER trg_transfer_budget_check
    BEFORE INSERT ON TRANSFER
    FOR EACH ROW
    EXECUTE FUNCTION trg_fn_validate_transfer();
