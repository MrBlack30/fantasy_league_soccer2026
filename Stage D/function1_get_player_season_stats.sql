-- ============================================================
-- function1_get_player_season_stats.sql
-- Function: fn_get_player_season_stats(p_player_id INT)
--
-- Description:
--   Returns a named REF CURSOR containing all gameweek performance
--   rows for a given player, joined with match and team info.
--   Validates the player exists first (implicit cursor / SELECT INTO).
--   Raises an exception if the player ID is not found.
--
-- Elements used:
--   * Implicit cursor  (SELECT INTO for validation)
--   * REF CURSOR       (returned to the caller)
--   * Record variable  (v_player RECORD)
--   * Branching        (IF NOT FOUND)
--   * Exception        (RAISE EXCEPTION + WHEN OTHERS)
-- ============================================================

CREATE OR REPLACE FUNCTION fn_get_player_season_stats(p_player_id INT)
RETURNS refcursor
LANGUAGE plpgsql
AS $$
DECLARE
    v_cursor refcursor := 'player_stats_cursor';
    v_player RECORD;
BEGIN
    -- Implicit cursor: fetch player details for validation
    SELECT player_id,
           first_name || ' ' || last_name AS full_name,
           price,
           total_points
    INTO   v_player
    FROM   PLAYER
    WHERE  player_id = p_player_id;

    -- Branch: abort if player not found
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player with ID % does not exist in the database.', p_player_id;
    END IF;

    RAISE NOTICE 'Opening season stats cursor for: % (ID: %, Price: £%m, Total pts: %)',
        v_player.full_name, v_player.player_id, v_player.price, v_player.total_points;

    -- Open the named REF CURSOR with a multi-join query
    OPEN v_cursor FOR
        SELECT
            gw.season_year,
            gw.gameweek_number,
            m.match_date,
            ht.team_name    AS home_team,
            at_t.team_name  AS away_team,
            m.home_score,
            m.away_score,
            pgs.minutes_played,
            pgs.goals_scored,
            pgs.assists,
            pgs.clean_sheet,
            pgs.yellow_cards,
            pgs.red_cards,
            pgs.saves,
            pgs.bonus_points,
            pgs.total_points AS gw_points
        FROM   PLAYER_GAMEWEEK_STATS pgs
        JOIN   MATCH       m    ON pgs.match_id    = m.match_id
        JOIN   GAMEWEEK    gw   ON pgs.gameweek_id = gw.gameweek_id
        JOIN   REAL_TEAM   ht   ON m.home_team_id  = ht.real_team_id
        JOIN   REAL_TEAM   at_t ON m.away_team_id  = at_t.real_team_id
        WHERE  pgs.player_id = p_player_id
        ORDER  BY gw.season_year, gw.gameweek_number;

    RETURN v_cursor;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'fn_get_player_season_stats failed for player ID %: %',
            p_player_id, SQLERRM;
END;
$$;
