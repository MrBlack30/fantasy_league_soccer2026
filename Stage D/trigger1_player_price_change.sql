-- ============================================================
-- trigger1_player_price_change.sql
-- Trigger: trg_player_price_change
-- Fires:   BEFORE UPDATE OF price ON PLAYER (for each row)
--
-- Description:
--   Whenever a player's fantasy price is modified this trigger:
--     1. Detects whether the price actually changed.
--     2. Records the old price into the previous_price column
--        (column added in AlterTable.sql) so auditing is possible.
--     3. Raises a NOTICE showing the direction and magnitude of the change.
--     4. Prevents a price from being set below 0.1 or above 20.0 by
--        raising an EXCEPTION (hard guardrail on top of the CHECK constraint).
--
-- Elements used:
--   * Branching    (IF price changed, IF rise vs fall, IF out-of-range)
--   * Exception    (RAISE EXCEPTION for invalid price range)
--   * NEW / OLD    (trigger-specific record variables)
-- ============================================================

CREATE OR REPLACE FUNCTION trg_fn_log_price_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_diff      NUMERIC(5,1);
    v_direction TEXT;
BEGIN
    -- Hard guardrail: reject prices outside the allowed fantasy range
    IF NEW.price < 0.1 OR NEW.price > 20.0 THEN
        RAISE EXCEPTION
            'Invalid price % for player % % (ID %): must be between 0.1 and 20.0.',
            NEW.price, NEW.first_name, NEW.last_name, NEW.player_id;
    END IF;

    -- Only act when the price value actually changed
    IF NEW.price IS DISTINCT FROM OLD.price THEN
        v_diff := ROUND(NEW.price - OLD.price, 1);

        IF v_diff > 0 THEN
            v_direction := 'RISE';
        ELSE
            v_direction := 'FALL';
        END IF;

        -- Persist the old price for audit purposes
        NEW.previous_price := OLD.price;

        RAISE NOTICE 'Price % — % % (ID %): £%m → £%m (change: %)',
            v_direction,
            NEW.first_name, NEW.last_name, NEW.player_id,
            OLD.price, NEW.price, v_diff;
    END IF;

    RETURN NEW;
END;
$$;

-- Drop and recreate the trigger to ensure a clean state
DROP TRIGGER IF EXISTS trg_player_price_change ON PLAYER;

CREATE TRIGGER trg_player_price_change
    BEFORE UPDATE OF price ON PLAYER
    FOR EACH ROW
    EXECUTE FUNCTION trg_fn_log_price_change();
