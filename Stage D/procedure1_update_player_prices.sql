-- ============================================================
-- procedure1_update_player_prices.sql
-- Procedure: pr_update_player_prices()
--
-- Description:
--   Iterates over every player and adjusts their fantasy price
--   based on season performance and ownership percentage,
--   mirroring the real FPL price-change algorithm:
--     RISE  (+0.1): total_points > 100 AND selected_by_percent > 20
--     FALL  (-0.1): total_points < 30  AND selected_by_percent < 5
--   Price is clamped to the range [0.1, 20.0].
--   Saves the old price into previous_price before each UPDATE
--   (the column was added in AlterTable.sql).
--
-- Elements used:
--   * Implicit cursor  (SELECT COUNT(*) INTO to validate data exists)
--   * Explicit cursor  (OPEN / FETCH / CLOSE over all players)
--   * Record variable  (v_player RECORD)
--   * Loop             (LOOP ... EXIT WHEN NOT FOUND)
--   * Branching        (IF / ELSIF for rise / fall / no change)
--   * DML              (UPDATE PLAYER)
--   * Exception        (RAISE EXCEPTION + WHEN OTHERS)
-- ============================================================

CREATE OR REPLACE PROCEDURE pr_update_player_prices()
LANGUAGE plpgsql
AS $$
DECLARE
    v_player      RECORD;
    v_new_price   NUMERIC(5,1);
    v_total       INT := 0;
    v_updated     INT := 0;
    v_raised      INT := 0;
    v_dropped     INT := 0;

    -- Explicit cursor: all players ordered for deterministic processing
    cur_players CURSOR FOR
        SELECT
            player_id,
            first_name || ' ' || last_name AS full_name,
            price,
            total_points,
            selected_by_percent,
            position_id
        FROM   PLAYER
        ORDER  BY player_id;
BEGIN
    -- Implicit cursor: confirm there are players to process
    SELECT COUNT(*) INTO v_total FROM PLAYER;

    IF v_total = 0 THEN
        RAISE EXCEPTION 'No players found in the database — nothing to update.';
    END IF;

    RAISE NOTICE 'Starting price update for % players...', v_total;

    OPEN cur_players;
    LOOP
        FETCH cur_players INTO v_player;
        EXIT WHEN NOT FOUND;

        v_new_price := v_player.price;  -- default: no change

        -- Price-rise: strong performance + high demand
        IF v_player.total_points > 100
           AND COALESCE(v_player.selected_by_percent, 0) > 20
        THEN
            v_new_price := LEAST(v_player.price + 0.1, 20.0);
            v_raised    := v_raised + 1;

        -- Price-drop: poor performance + low demand
        ELSIF v_player.total_points < 30
              AND COALESCE(v_player.selected_by_percent, 0) < 5
        THEN
            v_new_price := GREATEST(v_player.price - 0.1, 0.1);
            v_dropped   := v_dropped + 1;
        END IF;

        -- Only write to DB if price actually changes
        IF v_new_price <> v_player.price THEN
            UPDATE PLAYER
            SET    previous_price = v_player.price,
                   price          = v_new_price
            WHERE  player_id = v_player.player_id;

            v_updated := v_updated + 1;

            RAISE NOTICE 'Player %-% (ID %): £%m → £%m',
                v_player.full_name,
                CASE WHEN v_new_price > v_player.price THEN '▲' ELSE '▼' END,
                v_player.player_id,
                v_player.price,
                v_new_price;
        END IF;

    END LOOP;
    CLOSE cur_players;

    RAISE NOTICE '--- Price update complete ---';
    RAISE NOTICE 'Players checked: %  |  Updated: %  |  Raised: %  |  Dropped: %',
        v_total, v_updated, v_raised, v_dropped;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'pr_update_player_prices failed: %', SQLERRM;
END;
$$;
