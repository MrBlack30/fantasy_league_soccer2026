-- ============================================================
-- procedure2_process_gameweek_points.sql
-- Procedure: pr_process_gameweek_points(p_gameweek_id INT)
--
-- Description:
--   Calculates and records fantasy points for every team selection
--   in a given gameweek.  Three steps:
--
--   1. For each FANTASY_TEAM_SELECTION row in the gameweek:
--        - Look up the player's real PLAYER_GAMEWEEK_STATS points.
--        - Bench players always score 0.
--        - Captain scores double.
--        - UPDATE FANTASY_TEAM_SELECTION.points_scored.
--
--   2. Roll up the GW points into FANTASY_TEAM.total_points (UPDATE).
--
--   3. Insert a new LEAGUE_STANDING snapshot for each team; if a row
--      already exists (re-run scenario) UPDATE it instead (UPSERT pattern).
--
-- Elements used:
--   * Implicit cursor  (SELECT INTO for gameweek validation and stat lookup)
--   * Explicit cursor  (OPEN / FETCH / CLOSE over FANTASY_TEAM_SELECTION)
--   * FOR cursor loop  (implicit cursor FOR loop for league standings)
--   * Record variable  (v_sel_rec, v_team_rec RECORD)
--   * Loop             (LOOP...EXIT on explicit cursor; FOR loop)
--   * Branching        (IF bench / captain / NOT FOUND)
--   * DML              (UPDATE FANTASY_TEAM_SELECTION, UPDATE FANTASY_TEAM,
--                       INSERT / UPDATE LEAGUE_STANDING)
--   * Exception        (RAISE EXCEPTION + WHEN OTHERS)
-- ============================================================

CREATE OR REPLACE PROCEDURE pr_process_gameweek_points(p_gameweek_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_sel_rec      RECORD;
    v_team_rec     RECORD;
    v_stat_pts     INT;
    v_final_pts    INT;
    v_gw_exists    INT;
    v_standing_id  INT;
    v_new_id       INT;

    -- Explicit cursor: all selections for this gameweek
    cur_sel CURSOR FOR
        SELECT
            fts.selection_id,
            fts.team_id,
            fts.player_id,
            fts.is_captain,
            fts.is_on_bench
        FROM   FANTASY_TEAM_SELECTION fts
        WHERE  fts.gameweek_id = p_gameweek_id
        ORDER  BY fts.team_id, fts.is_on_bench;
BEGIN
    -- Implicit cursor: validate gameweek exists
    SELECT COUNT(*) INTO v_gw_exists
    FROM   GAMEWEEK
    WHERE  gameweek_id = p_gameweek_id;

    IF v_gw_exists = 0 THEN
        RAISE EXCEPTION 'Gameweek % does not exist.', p_gameweek_id;
    END IF;

    RAISE NOTICE 'Processing points for gameweek %...', p_gameweek_id;

    -- ─── Step 1: update points_scored for every selection ────────────────
    OPEN cur_sel;
    LOOP
        FETCH cur_sel INTO v_sel_rec;
        EXIT WHEN NOT FOUND;

        IF v_sel_rec.is_on_bench = 1 THEN
            -- Bench players earn 0 fantasy points
            v_final_pts := 0;
        ELSE
            -- Implicit cursor: look up real stats for this player / gameweek
            SELECT COALESCE(pgs.total_points, 0)
            INTO   v_stat_pts
            FROM   PLAYER_GAMEWEEK_STATS pgs
            WHERE  pgs.player_id   = v_sel_rec.player_id
              AND  pgs.gameweek_id = p_gameweek_id
            LIMIT  1;

            IF NOT FOUND THEN
                v_stat_pts := 0;  -- player had no real-world stats (absent)
            END IF;

            -- Captain earns double points
            IF v_sel_rec.is_captain = 1 THEN
                v_final_pts := v_stat_pts * 2;
            ELSE
                v_final_pts := v_stat_pts;
            END IF;
        END IF;

        -- DML 1: write points back to selection row
        UPDATE FANTASY_TEAM_SELECTION
        SET    points_scored = v_final_pts
        WHERE  selection_id  = v_sel_rec.selection_id;

    END LOOP;
    CLOSE cur_sel;

    -- ─── Step 2: roll up into FANTASY_TEAM.total_points ──────────────────
    -- DML 2: accumulate this gameweek's total onto the team's season total
    UPDATE FANTASY_TEAM ft
    SET    total_points = ft.total_points + (
               SELECT COALESCE(SUM(fts.points_scored), 0)
               FROM   FANTASY_TEAM_SELECTION fts
               WHERE  fts.team_id    = ft.team_id
                 AND  fts.gameweek_id = p_gameweek_id
           )
    WHERE  ft.team_id IN (
               SELECT DISTINCT team_id
               FROM   FANTASY_TEAM_SELECTION
               WHERE  gameweek_id = p_gameweek_id
           );

    -- ─── Step 3: snapshot league standings ───────────────────────────────
    -- FOR implicit cursor loop: rank each team within its league
    FOR v_team_rec IN
        SELECT
            ft.team_id,
            ft.league_id,
            ft.total_points,
            RANK() OVER (
                PARTITION BY ft.league_id
                ORDER BY     ft.total_points DESC
            )::INT AS rank_in_league
        FROM FANTASY_TEAM ft
        WHERE ft.team_id IN (
            SELECT DISTINCT team_id
            FROM   FANTASY_TEAM_SELECTION
            WHERE  gameweek_id = p_gameweek_id
        )
    LOOP
        -- Check for existing snapshot (re-run guard)
        SELECT standing_id INTO v_standing_id
        FROM   LEAGUE_STANDING
        WHERE  league_id   = v_team_rec.league_id
          AND  team_id     = v_team_rec.team_id
          AND  gameweek_id = p_gameweek_id;

        IF FOUND THEN
            -- DML 3a: update existing snapshot
            UPDATE LEAGUE_STANDING
            SET    points = v_team_rec.total_points,
                   rank   = v_team_rec.rank_in_league
            WHERE  standing_id = v_standing_id;
        ELSE
            -- DML 3b: insert new snapshot (safe sequential ID)
            SELECT COALESCE(MAX(standing_id), 0) + 1
            INTO   v_new_id
            FROM   LEAGUE_STANDING;

            INSERT INTO LEAGUE_STANDING
                (standing_id, points, rank, league_id, team_id, gameweek_id)
            VALUES
                (v_new_id,
                 v_team_rec.total_points,
                 v_team_rec.rank_in_league,
                 v_team_rec.league_id,
                 v_team_rec.team_id,
                 p_gameweek_id);
        END IF;
    END LOOP;

    RAISE NOTICE 'Gameweek % processing complete.', p_gameweek_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'pr_process_gameweek_points failed for GW %: %',
            p_gameweek_id, SQLERRM;
END;
$$;
