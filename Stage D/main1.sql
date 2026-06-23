-- ============================================================
-- main1.sql
-- Main Program 1
--
-- Calls:
--   1. fn_get_player_season_stats(p_player_id)  [Function 1]
--      Opens the REF CURSOR, fetches every row, and prints a
--      per-gameweek performance table via RAISE NOTICE.
--
--   2. pr_update_player_prices()                [Procedure 1]
--      Applies price rises / falls to every player based on
--      performance and ownership data.
--
-- *** Change v_player_id to any valid player_id in your database ***
-- ============================================================

DO $$
DECLARE
    v_cursor    refcursor;
    v_row       RECORD;
    v_player_id INT     := 423; -- Harry Ederson, 38 GW stats
    v_row_count INT     := 0;
    v_total_pts INT     := 0;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 1';
    RAISE NOTICE '============================================================';

    -- ── Step 1: call function 1 and display season stats ─────────────────
    RAISE NOTICE '';
    RAISE NOTICE 'STEP 1 — Season stats for player ID %', v_player_id;
    RAISE NOTICE '------------------------------------------------------------';

    BEGIN
        -- fn_get_player_season_stats returns a named ref cursor
        v_cursor := fn_get_player_season_stats(v_player_id);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Could not open stats cursor: %', SQLERRM;
            RETURN;
    END;

    -- Fetch all rows from the ref cursor
    LOOP
        FETCH v_cursor INTO v_row;
        EXIT WHEN NOT FOUND;

        v_row_count := v_row_count + 1;
        v_total_pts := v_total_pts + v_row.gw_points;

        RAISE NOTICE 'GW %-% (%)  |  % vs %  |  Min: %  G: %  A: %  CS: %  Yel: %  Red: %  Saves: %  Bonus: %  Pts: %',
            v_row.season_year,
            v_row.season_year + 1,
            v_row.gameweek_number,
            v_row.home_team,
            v_row.away_team,
            v_row.minutes_played,
            v_row.goals_scored,
            v_row.assists,
            v_row.clean_sheet,
            v_row.yellow_cards,
            v_row.red_cards,
            v_row.saves,
            v_row.bonus_points,
            v_row.gw_points;
    END LOOP;
    CLOSE v_cursor;

    IF v_row_count = 0 THEN
        RAISE NOTICE 'No gameweek stats found for player %.', v_player_id;
    ELSE
        RAISE NOTICE '------------------------------------------------------------';
        RAISE NOTICE 'Total gameweeks: %   |   Season points total: %',
            v_row_count, v_total_pts;
    END IF;

    -- ── Step 2: call procedure 1 – update all player prices ──────────────
    RAISE NOTICE '';
    RAISE NOTICE 'STEP 2 — Updating player prices';
    RAISE NOTICE '------------------------------------------------------------';
    CALL pr_update_player_prices();

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 1 — complete';
    RAISE NOTICE '============================================================';
END;
$$;
