-- ============================================================
-- main2.sql
-- Main Program 2
--
-- Calls:
--   1. fn_evaluate_fantasy_team(p_team_id, p_gameweek_id)  [Function 2]
--      Prints a full squad evaluation report: value, captain,
--      average points, and a health rating.
--
--   2. pr_process_gameweek_points(p_gameweek_id)            [Procedure 2]
--      Scores every selection in the gameweek, updates team
--      totals, and snapshots league standings.
--
-- *** Change v_team_id and v_gameweek_id to valid IDs in your database ***
-- ============================================================

DO $$
DECLARE
    v_row         RECORD;
    v_team_id     INT     := 1;   -- Roberto FC 1
    v_gameweek_id INT     := 1;   -- Season 2023 GW1
    v_found       BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 2';
    RAISE NOTICE '============================================================';

    -- ── Step 1: call function 2 – team evaluation report ─────────────────
    RAISE NOTICE '';
    RAISE NOTICE 'STEP 1 — Evaluating team % for gameweek %',
        v_team_id, v_gameweek_id;
    RAISE NOTICE '------------------------------------------------------------';

    BEGIN
        FOR v_row IN
            SELECT * FROM fn_evaluate_fantasy_team(v_team_id, v_gameweek_id)
        LOOP
            v_found := TRUE;
            RAISE NOTICE '  Team Name        : %', v_row.team_name_out;
            RAISE NOTICE '  Formation         : %', v_row.formation_out;
            RAISE NOTICE '  Squad Value       : £% m', v_row.total_squad_value;
            RAISE NOTICE '  Budget Remaining  : £% m', v_row.budget_remaining;
            RAISE NOTICE '  Starting XI Pts   : %',   v_row.starting_xi_points;
            RAISE NOTICE '  Avg Pts / Player  : %',   v_row.avg_points_per_player;
            RAISE NOTICE '  Captain           : %',   v_row.captain_name;
            RAISE NOTICE '  Health Rating     : %',   v_row.health_rating;
        END LOOP;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Error during team evaluation: %', SQLERRM;
    END;

    IF NOT v_found THEN
        RAISE NOTICE 'No evaluation data returned for team % / GW %.',
            v_team_id, v_gameweek_id;
    END IF;

    -- ── Step 2: call procedure 2 – process gameweek points ───────────────
    RAISE NOTICE '';
    RAISE NOTICE 'STEP 2 — Processing points for gameweek %', v_gameweek_id;
    RAISE NOTICE '------------------------------------------------------------';

    BEGIN
        CALL pr_process_gameweek_points(v_gameweek_id);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Error during points processing: %', SQLERRM;
    END;

    -- Show updated team totals after processing
    RAISE NOTICE '';
    RAISE NOTICE 'Updated league standings after GW %:', v_gameweek_id;
    FOR v_row IN
        SELECT
            ft.team_name,
            ft.total_points,
            ls.rank
        FROM   LEAGUE_STANDING ls
        JOIN   FANTASY_TEAM    ft ON ls.team_id = ft.team_id
        WHERE  ls.gameweek_id = v_gameweek_id
        ORDER  BY ls.rank
        LIMIT  10
    LOOP
        RAISE NOTICE '  Rank %  |  %  |  % pts',
            v_row.rank, v_row.team_name, v_row.total_points;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 2 — complete';
    RAISE NOTICE '============================================================';
END;
$$;
