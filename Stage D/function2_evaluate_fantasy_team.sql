-- ============================================================
-- function2_evaluate_fantasy_team.sql
-- Function: fn_evaluate_fantasy_team(p_team_id INT, p_gameweek_id INT)
--
-- Description:
--   Evaluates a fantasy team's squad for a specific gameweek.
--   Uses an explicit cursor to iterate over all selected players,
--   sums up squad value and starting-XI points, identifies the captain,
--   and assigns a health rating based on average points per player.
--   Returns a single-row TABLE with the team summary.
--
-- Elements used:
--   * Implicit cursor  (SELECT INTO for team validation)
--   * Explicit cursor  (OPEN / FETCH / CLOSE over squad selections)
--   * Record variable  (v_team_rec, v_sel_rec)
--   * Loop             (LOOP ... EXIT WHEN NOT FOUND)
--   * Branching        (IF / ELSIF for bench flag, captain, health rating)
--   * Exception        (RAISE EXCEPTION on missing team/squad + WHEN OTHERS)
-- ============================================================

CREATE OR REPLACE FUNCTION fn_evaluate_fantasy_team(p_team_id INT, p_gameweek_id INT)
RETURNS TABLE(
    team_name_out         VARCHAR(100),
    formation_out         VARCHAR(10),
    total_squad_value     NUMERIC,
    budget_remaining      NUMERIC,
    starting_xi_points    INT,
    avg_points_per_player NUMERIC,
    captain_name          TEXT,
    health_rating         TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_team_rec   RECORD;
    v_sel_rec    RECORD;
    v_total_val  NUMERIC(8,1) := 0;
    v_total_pts  INT          := 0;
    v_xi_count   INT          := 0;
    v_captain    TEXT         := 'Unknown';
    v_avg        NUMERIC;
    v_health     TEXT;

    -- Explicit cursor: all 15 squad players for this team / gameweek
    cur_squad CURSOR FOR
        SELECT
            fts.is_captain,
            fts.is_on_bench,
            fts.points_scored,
            p.price,
            p.first_name || ' ' || p.last_name AS player_name,
            pos.short_name                      AS pos_short
        FROM   FANTASY_TEAM_SELECTION fts
        JOIN   PLAYER   p   ON fts.player_id  = p.player_id
        JOIN   POSITION pos ON p.position_id  = pos.position_id
        WHERE  fts.team_id    = p_team_id
          AND  fts.gameweek_id = p_gameweek_id
        ORDER  BY fts.is_on_bench, pos.position_id;
BEGIN
    -- Implicit cursor: validate the fantasy team exists
    SELECT ft.team_name, ft.budget_remaining, ft.formation
    INTO   v_team_rec
    FROM   FANTASY_TEAM ft
    WHERE  ft.team_id = p_team_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Fantasy team with ID % does not exist.', p_team_id;
    END IF;

    -- Iterate the squad using the explicit cursor
    OPEN cur_squad;
    LOOP
        FETCH cur_squad INTO v_sel_rec;
        EXIT WHEN NOT FOUND;

        -- Every player (including bench) counts toward squad value
        v_total_val := v_total_val + v_sel_rec.price;

        -- Only starting XI contributes to points average
        IF v_sel_rec.is_on_bench = 0 THEN
            v_total_pts := v_total_pts + COALESCE(v_sel_rec.points_scored, 0);
            v_xi_count  := v_xi_count + 1;
        END IF;

        -- Identify captain
        IF v_sel_rec.is_captain = 1 THEN
            v_captain := v_sel_rec.player_name || ' (' || v_sel_rec.pos_short || ')';
        END IF;
    END LOOP;
    CLOSE cur_squad;

    -- Guard: no starting XI found
    IF v_xi_count = 0 THEN
        RAISE EXCEPTION
            'No starting XI selection found for team % in gameweek %.',
            p_team_id, p_gameweek_id;
    END IF;

    v_avg := ROUND(v_total_pts::NUMERIC / v_xi_count, 2);

    -- Classify team health based on average points per starting player
    IF v_avg >= 8 THEN
        v_health := 'Excellent';
    ELSIF v_avg >= 5 THEN
        v_health := 'Good';
    ELSIF v_avg >= 3 THEN
        v_health := 'Average';
    ELSE
        v_health := 'Poor';
    END IF;

    RETURN QUERY
        SELECT
            v_team_rec.team_name::VARCHAR(100),
            v_team_rec.formation::VARCHAR(10),
            v_total_val,
            v_team_rec.budget_remaining,
            v_total_pts,
            v_avg,
            v_captain,
            v_health;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION
            'fn_evaluate_fantasy_team error (team %, GW %): %',
            p_team_id, p_gameweek_id, SQLERRM;
END;
$$;
