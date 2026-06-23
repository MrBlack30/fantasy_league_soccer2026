# Stage D – PL/pgSQL Programming

## Overview

This stage adds procedural logic on top of the integrated Fantasy Soccer + FIFA World Cup database built in the previous stages. Eight programs were written in PL/pgSQL and deployed to the `mydatabase` PostgreSQL database running in Docker. Two columns were also added to existing tables to support the new logic.

The programs cover the full lifecycle of a fantasy football gameweek: fetching player stats, evaluating squad health, processing points, adjusting prices, and enforcing budget rules on transfers — all with exception handling, cursors, loops, records, and DML throughout.

---

## Database Changes — `AlterTable.sql`

Two columns were added to support the trigger and procedure logic:

| Table | New Column | Type | Purpose |
|---|---|---|---|
| `PLAYER` | `previous_price` | `NUMERIC(5,1)` | Stores the price before the last change, written by Trigger 1 |
| `FANTASY_TEAM` | `total_transfers_cost` | `NUMERIC(8,1)` | Accumulates total spending on transfers across the season, updated by Trigger 2 |

```sql
ALTER TABLE PLAYER
    ADD COLUMN IF NOT EXISTS previous_price NUMERIC(5,1);

ALTER TABLE FANTASY_TEAM
    ADD COLUMN IF NOT EXISTS total_transfers_cost NUMERIC(8,1) DEFAULT 0;
```

<img width="1366" height="1394" alt="image" src="https://github.com/user-attachments/assets/db7a0ff5-cf8b-4ffc-8f8b-367963f7d6a3" />

---

## Function 1 — `fn_get_player_season_stats`

**File:** `function1_get_player_season_stats.sql`

A fantasy manager needs to review a player's full season history before deciding whether to buy them. This function accepts a player ID and returns a named REF CURSOR containing one row per gameweek the player appeared in, joined with match and team information. Before opening the cursor it validates the player exists using an implicit cursor (SELECT INTO), and raises an exception if not found.

**Programming elements:** implicit cursor, REF CURSOR, record variable, branching (IF NOT FOUND), exception handling (RAISE EXCEPTION + WHEN OTHERS).

```sql
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
```

The function is called from Main Program 1, which fetches every row from the returned cursor and prints it. Below is proof that it ran successfully for player 423 (Harry Ederson), who had stats in all 38 gameweeks of the 2023/24 season.

<img width="2716" height="1442" alt="image" src="https://github.com/user-attachments/assets/88f8c803-51dc-4b8c-8baf-edaa0c704dd4" />


------------ Enter a screenshot of the final summary line: "Total gameweeks: 38 | Season points total: ..." ------------

---

## Function 2 — `fn_evaluate_fantasy_team`

**File:** `function2_evaluate_fantasy_team.sql`

After a gameweek, a manager wants a single-glance summary of their squad's performance and value. This function takes a team ID and gameweek ID and returns a one-row report containing the team name, formation, total squad value, budget remaining, starting XI total points, average points per player, the captain's name and position, and a health rating. It validates the team with an implicit cursor, then uses an explicit cursor with an open/fetch/close loop to iterate over all 15 selected players, accumulating value and points and identifying the captain. The health rating (Excellent / Good / Average / Poor) is assigned with IF/ELSIF branching on the average points figure.

**Programming elements:** implicit cursor, explicit cursor with OPEN/FETCH/CLOSE, record variables, loop (LOOP … EXIT WHEN NOT FOUND), branching (IF/ELSIF), exception handling.

```sql
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

        v_total_val := v_total_val + v_sel_rec.price;

        IF v_sel_rec.is_on_bench = 0 THEN
            v_total_pts := v_total_pts + COALESCE(v_sel_rec.points_scored, 0);
            v_xi_count  := v_xi_count + 1;
        END IF;

        IF v_sel_rec.is_captain = 1 THEN
            v_captain := v_sel_rec.player_name || ' (' || v_sel_rec.pos_short || ')';
        END IF;
    END LOOP;
    CLOSE cur_squad;

    IF v_xi_count = 0 THEN
        RAISE EXCEPTION
            'No starting XI selection found for team % in gameweek %.',
            p_team_id, p_gameweek_id;
    END IF;

    v_avg := ROUND(v_total_pts::NUMERIC / v_xi_count, 2);

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
```

The function is called from Main Program 2 and printed as a formatted report. The output below shows "Roberto FC 1" in a 4-1-4-1 formation, squad value £122.3m, captain Nicolas Martin (FWD), average 9.55 points per player, health rating **Excellent**.

------------ Enter a screenshot of the NOTICE output from Main Program 2 Step 1 showing the full team evaluation report (Team Name, Formation, Squad Value, Budget Remaining, Starting XI Pts, Avg Pts/Player, Captain, Health Rating) ------------

---

## Procedure 1 — `pr_update_player_prices`

**File:** `procedure1_update_player_prices.sql`

Fantasy football games adjust player prices weekly based on demand and performance — popular, high-scoring players rise; obscure, poor-performing ones fall. This procedure replicates that logic across the entire player database. It first confirms players exist via an implicit cursor (SELECT COUNT INTO), then opens an explicit cursor over every player and applies the following rules inside a loop:

- **Rise (+£0.1m):** `total_points > 100` AND `selected_by_percent > 20` — price capped at £20.0m
- **Fall (−£0.1m):** `total_points < 30` AND `selected_by_percent < 5` — price floored at £0.1m

Only players whose price actually changes trigger an UPDATE. Each UPDATE also saves the old price to `previous_price` (which in turn fires Trigger 1). A summary counter is printed at the end.

**Programming elements:** implicit cursor, explicit cursor with OPEN/FETCH/CLOSE, record variable, loop, branching (IF/ELSIF), DML (UPDATE), exception handling.

```sql
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

        v_new_price := v_player.price;

        IF v_player.total_points > 100
           AND COALESCE(v_player.selected_by_percent, 0) > 20
        THEN
            v_new_price := LEAST(v_player.price + 0.1, 20.0);
            v_raised    := v_raised + 1;

        ELSIF v_player.total_points < 30
              AND COALESCE(v_player.selected_by_percent, 0) < 5
        THEN
            v_new_price := GREATEST(v_player.price - 0.1, 0.1);
            v_dropped   := v_dropped + 1;
        END IF;

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
```

When run against the 600-player database it processed all players and updated 216 prices (212 rises, 4 drops). Each UPDATE also silently fired Trigger 1, which saved the old price into `previous_price`.

------------ Enter a screenshot of the NOTICE output from Main Program 1 Step 2, showing individual price changes (e.g. "Player Harry Ederson-▲ (ID 423): £9.1m → £9.2m") ------------

------------ Enter a screenshot of the final summary line: "Players checked: 600 | Updated: 216 | Raised: 212 | Dropped: 4" ------------

------------ Enter a screenshot of a SELECT on PLAYER showing the previous_price column populated (e.g. `SELECT player_id, first_name, last_name, previous_price, price FROM player WHERE previous_price IS NOT NULL LIMIT 5`) ------------

---

## Procedure 2 — `pr_process_gameweek_points`

**File:** `procedure2_process_gameweek_points.sql`

At the end of every real-world gameweek the platform must score every fantasy team: look up how many points each selected player earned, double the captain's score, write the result back to `FANTASY_TEAM_SELECTION`, roll up totals into `FANTASY_TEAM`, and record a ranked snapshot in `LEAGUE_STANDING`. This procedure does all of that in three sequential steps.

**Step 1** — an explicit cursor loops over every row in `FANTASY_TEAM_SELECTION` for the given gameweek. For each row it looks up `PLAYER_GAMEWEEK_STATS` with an implicit cursor (SELECT INTO). Bench players receive 0; the captain receives double. The result is written back with UPDATE.

**Step 2** — a single UPDATE accumulates each team's GW total into `FANTASY_TEAM.total_points`.

**Step 3** — a FOR implicit-cursor loop ranks teams within their league using a window function and either inserts a new `LEAGUE_STANDING` row or updates an existing one (re-run safety).

**Programming elements:** implicit cursor (two uses), explicit cursor with OPEN/FETCH/CLOSE, FOR cursor loop, record variables, loops, branching (bench/captain/FOUND), DML (UPDATE × 3, INSERT), exception handling.

```sql
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
    SELECT COUNT(*) INTO v_gw_exists
    FROM   GAMEWEEK
    WHERE  gameweek_id = p_gameweek_id;

    IF v_gw_exists = 0 THEN
        RAISE EXCEPTION 'Gameweek % does not exist.', p_gameweek_id;
    END IF;

    RAISE NOTICE 'Processing points for gameweek %...', p_gameweek_id;

    -- Step 1: score every selection
    OPEN cur_sel;
    LOOP
        FETCH cur_sel INTO v_sel_rec;
        EXIT WHEN NOT FOUND;

        IF v_sel_rec.is_on_bench = 1 THEN
            v_final_pts := 0;
        ELSE
            SELECT COALESCE(pgs.total_points, 0)
            INTO   v_stat_pts
            FROM   PLAYER_GAMEWEEK_STATS pgs
            WHERE  pgs.player_id   = v_sel_rec.player_id
              AND  pgs.gameweek_id = p_gameweek_id
            LIMIT  1;

            IF NOT FOUND THEN
                v_stat_pts := 0;
            END IF;

            IF v_sel_rec.is_captain = 1 THEN
                v_final_pts := v_stat_pts * 2;
            ELSE
                v_final_pts := v_stat_pts;
            END IF;
        END IF;

        UPDATE FANTASY_TEAM_SELECTION
        SET    points_scored = v_final_pts
        WHERE  selection_id  = v_sel_rec.selection_id;

    END LOOP;
    CLOSE cur_sel;

    -- Step 2: roll up totals
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

    -- Step 3: snapshot league standings
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
        SELECT standing_id INTO v_standing_id
        FROM   LEAGUE_STANDING
        WHERE  league_id   = v_team_rec.league_id
          AND  team_id     = v_team_rec.team_id
          AND  gameweek_id = p_gameweek_id;

        IF FOUND THEN
            UPDATE LEAGUE_STANDING
            SET    points = v_team_rec.total_points,
                   rank   = v_team_rec.rank_in_league
            WHERE  standing_id = v_standing_id;
        ELSE
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
```

------------ Enter a screenshot of the NOTICE output from Main Program 2 Step 2, showing "Processing points for gameweek 1..." and "Gameweek 1 processing complete." ------------

------------ Enter a screenshot of a SELECT on LEAGUE_STANDING showing the inserted rows (e.g. `SELECT * FROM league_standing WHERE gameweek_id = 1 LIMIT 10`) ------------

------------ Enter a screenshot of a SELECT on FANTASY_TEAM showing updated total_points (e.g. `SELECT team_id, team_name, total_points FROM fantasy_team ORDER BY total_points DESC LIMIT 5`) ------------

---

## Trigger 1 — `trg_player_price_change`

**File:** `trigger1_player_price_change.sql`

**Fires:** `BEFORE UPDATE OF price ON PLAYER` (row level)

Any time a player's price is written, this trigger intercepts the change before it hits the table. It first checks that the new price is within the legal fantasy range (£0.1m–£20.0m) and raises an exception to abort the update if not. If the price is valid and actually different from the old value, it saves the old price into `previous_price` (via the `NEW` record) and raises a NOTICE identifying the direction and magnitude of the change. Because it fires BEFORE the update, modifying `NEW.previous_price` in the trigger function is sufficient to persist it — no separate UPDATE is needed.

This trigger fires automatically during `pr_update_player_prices`, so each batch price update is fully audited without the procedure needing to track it.

**Programming elements:** branching (IF out-of-range, IF price changed, IF rise vs fall), exception (RAISE EXCEPTION), NEW/OLD trigger records.

```sql
CREATE OR REPLACE FUNCTION trg_fn_log_price_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_diff      NUMERIC(5,1);
    v_direction TEXT;
BEGIN
    IF NEW.price < 0.1 OR NEW.price > 20.0 THEN
        RAISE EXCEPTION
            'Invalid price % for player % % (ID %): must be between 0.1 and 20.0.',
            NEW.price, NEW.first_name, NEW.last_name, NEW.player_id;
    END IF;

    IF NEW.price IS DISTINCT FROM OLD.price THEN
        v_diff := ROUND(NEW.price - OLD.price, 1);

        IF v_diff > 0 THEN
            v_direction := 'RISE';
        ELSE
            v_direction := 'FALL';
        END IF;

        NEW.previous_price := OLD.price;

        RAISE NOTICE 'Price % — % % (ID %): £%m → £%m (change: %)',
            v_direction,
            NEW.first_name, NEW.last_name, NEW.player_id,
            OLD.price, NEW.price, v_diff;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_player_price_change ON PLAYER;

CREATE TRIGGER trg_player_price_change
    BEFORE UPDATE OF price ON PLAYER
    FOR EACH ROW
    EXECUTE FUNCTION trg_fn_log_price_change();
```

**Test — valid price change (RISE):**

```sql
UPDATE PLAYER SET price = 10.0 WHERE player_id = 423;
SELECT player_id, first_name, last_name, previous_price, price FROM PLAYER WHERE player_id = 423;
```

------------ Enter a screenshot of the above UPDATE statement output showing the NOTICE "Price RISE — Harry Ederson (ID 423): £9.2m → £10.0m (change: 0.8)" and the SELECT result showing previous_price = 9.2, price = 10.0 ------------

**Test — invalid price (rejected):**

```sql
UPDATE PLAYER SET price = 25.0 WHERE player_id = 423;
```

------------ Enter a screenshot of the above UPDATE being rejected with the error "Invalid price 25.0 for player Harry Ederson (ID 423): must be between 0.1 and 20.0." ------------

---

## Trigger 2 — `trg_transfer_budget_check`

**File:** `trigger2_transfer_budget_check.sql`

**Fires:** `BEFORE INSERT ON TRANSFER` (row level)

A player transfer costs money. Before any row is inserted into the `TRANSFER` table this trigger enforces that the fantasy team can afford it. It uses three implicit cursors (SELECT INTO) to fetch the team's current budget, the incoming player's name, and the outgoing player's name. If the budget is smaller than the price being paid it raises an exception with a detailed breakdown, which aborts the INSERT entirely. If the budget is sufficient, it deducts the cost from `FANTASY_TEAM.budget_remaining` and adds it to `FANTASY_TEAM.total_transfers_cost` with an UPDATE, then confirms the transfer with a NOTICE.

**Programming elements:** implicit cursor (three SELECT INTO calls), branching (IF NOT FOUND × 3, IF budget insufficient), DML (UPDATE FANTASY_TEAM), exception handling.

```sql
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
    SELECT ft.budget_remaining, ft.team_name
    INTO   v_budget, v_team_name
    FROM   FANTASY_TEAM ft
    WHERE  ft.team_id = NEW.team_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: fantasy team ID % not found.', NEW.team_id;
    END IF;

    SELECT first_name || ' ' || last_name
    INTO   v_player_in
    FROM   PLAYER
    WHERE  player_id = NEW.player_in_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: incoming player ID % not found.', NEW.player_in_id;
    END IF;

    SELECT first_name || ' ' || last_name
    INTO   v_player_out
    FROM   PLAYER
    WHERE  player_id = NEW.player_out_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Transfer rejected: outgoing player ID % not found.', NEW.player_out_id;
    END IF;

    IF v_budget < NEW.price_paid THEN
        RAISE EXCEPTION
            'Transfer rejected: team "%" has insufficient budget. '
            'Available: £%m  |  Required: £%m  |  Shortfall: £%m',
            v_team_name,
            v_budget,
            NEW.price_paid,
            (NEW.price_paid - v_budget);
    END IF;

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

DROP TRIGGER IF EXISTS trg_transfer_budget_check ON TRANSFER;

CREATE TRIGGER trg_transfer_budget_check
    BEFORE INSERT ON TRANSFER
    FOR EACH ROW
    EXECUTE FUNCTION trg_fn_validate_transfer();
```

**Test — valid transfer (approved, budget deducted):**

```sql
INSERT INTO TRANSFER(transfer_id, price_paid, transfer_date, team_id, player_out_id, player_in_id, gameweek_id)
VALUES (1001, 10.6, CURRENT_DATE, 1, 96, 1, 1);

SELECT budget_remaining, total_transfers_cost FROM FANTASY_TEAM WHERE team_id = 1;
```

------------ Enter a screenshot showing the NOTICE "Transfer approved [team "Roberto FC 1"]: OUT Ben Thompson → IN Riyad Maddison for £10.6m (budget left: £60.6m)" and the SELECT result showing budget_remaining = 60.6 and total_transfers_cost = 10.6 ------------

**Test — rejected transfer (over budget):**

```sql
INSERT INTO TRANSFER(transfer_id, price_paid, transfer_date, team_id, player_out_id, player_in_id, gameweek_id)
VALUES (1002, 999.0, CURRENT_DATE, 1, 195, 2, 1);
```

------------ Enter a screenshot of the error "Transfer rejected: team "Roberto FC 1" has insufficient budget. Available: £60.6m | Required: £999.0m | Shortfall: £938.4m" ------------

---

## Main Program 1

**File:** `main1.sql`

An anonymous `DO` block that demonstrates Function 1 and Procedure 1 working together in a single session. It opens the REF CURSOR returned by `fn_get_player_season_stats` for player 423 (Harry Ederson), fetches every row in a loop, prints each gameweek line with all stats columns, then reports the total. After closing the cursor it calls `pr_update_player_prices()` to apply the season's price adjustments across all 600 players.

```sql
DO $$
DECLARE
    v_cursor    refcursor;
    v_row       RECORD;
    v_player_id INT     := 423;
    v_row_count INT     := 0;
    v_total_pts INT     := 0;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 1';
    RAISE NOTICE '============================================================';

    RAISE NOTICE 'STEP 1 — Season stats for player ID %', v_player_id;

    BEGIN
        v_cursor := fn_get_player_season_stats(v_player_id);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Could not open stats cursor: %', SQLERRM;
            RETURN;
    END;

    LOOP
        FETCH v_cursor INTO v_row;
        EXIT WHEN NOT FOUND;

        v_row_count := v_row_count + 1;
        v_total_pts := v_total_pts + v_row.gw_points;

        RAISE NOTICE 'GW %-% (%)  |  % vs %  |  Min: %  G: %  A: %  CS: %  Yel: %  Red: %  Saves: %  Bonus: %  Pts: %',
            v_row.season_year, v_row.season_year + 1, v_row.gameweek_number,
            v_row.home_team, v_row.away_team,
            v_row.minutes_played, v_row.goals_scored, v_row.assists,
            v_row.clean_sheet, v_row.yellow_cards, v_row.red_cards,
            v_row.saves, v_row.bonus_points, v_row.gw_points;
    END LOOP;
    CLOSE v_cursor;

    IF v_row_count = 0 THEN
        RAISE NOTICE 'No gameweek stats found for player %.', v_player_id;
    ELSE
        RAISE NOTICE 'Total gameweeks: %   |   Season points total: %', v_row_count, v_total_pts;
    END IF;

    RAISE NOTICE 'STEP 2 — Updating player prices';
    CALL pr_update_player_prices();

    RAISE NOTICE '  Main Program 1 — complete';
END;
$$;
```

------------ Enter a screenshot of the full Main Program 1 output, showing the header, several GW stat rows, the totals line, and the price update summary at the end ------------

---

## Main Program 2

**File:** `main2.sql`

An anonymous `DO` block that demonstrates Function 2 and Procedure 2. It calls `fn_evaluate_fantasy_team` for team 1 (Roberto FC 1) in gameweek 1 and prints the formatted report, then calls `pr_process_gameweek_points(1)` to score the entire gameweek. After the procedure completes it runs an inline query to display the top 10 updated league standings.

```sql
DO $$
DECLARE
    v_row         RECORD;
    v_team_id     INT     := 1;
    v_gameweek_id INT     := 1;
    v_found       BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Main Program 2';
    RAISE NOTICE '============================================================';

    RAISE NOTICE 'STEP 1 — Evaluating team % for gameweek %', v_team_id, v_gameweek_id;

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

    RAISE NOTICE 'STEP 2 — Processing points for gameweek %', v_gameweek_id;

    BEGIN
        CALL pr_process_gameweek_points(v_gameweek_id);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Error during points processing: %', SQLERRM;
    END;

    RAISE NOTICE 'Updated league standings after GW %:', v_gameweek_id;
    FOR v_row IN
        SELECT ft.team_name, ft.total_points, ls.rank
        FROM   LEAGUE_STANDING ls
        JOIN   FANTASY_TEAM    ft ON ls.team_id = ft.team_id
        WHERE  ls.gameweek_id = v_gameweek_id
        ORDER  BY ls.rank
        LIMIT  10
    LOOP
        RAISE NOTICE '  Rank %  |  %  |  % pts', v_row.rank, v_row.team_name, v_row.total_points;
    END LOOP;

    RAISE NOTICE '  Main Program 2 — complete';
END;
$$;
```

------------ Enter a screenshot of the full Main Program 2 output, showing the team evaluation report, "Gameweek 1 processing complete.", and the league standings table at the end ------------

---

## File Summary

| File | Type | Description |
|---|---|---|
| `AlterTable.sql` | DDL | Adds `previous_price` to PLAYER and `total_transfers_cost` to FANTASY_TEAM |
| `function1_get_player_season_stats.sql` | Function | Returns a REF CURSOR of a player's full season stats |
| `function2_evaluate_fantasy_team.sql` | Function | Returns a squad health report for a team in a given gameweek |
| `procedure1_update_player_prices.sql` | Procedure | Applies weekly price rises and drops to all players |
| `procedure2_process_gameweek_points.sql` | Procedure | Scores all GW selections, updates team totals, snapshots standings |
| `trigger1_player_price_change.sql` | Trigger | BEFORE UPDATE on PLAYER — audits price changes, rejects invalid values |
| `trigger2_transfer_budget_check.sql` | Trigger | BEFORE INSERT on TRANSFER — enforces budget and deducts cost |
| `main1.sql` | Main program | Runs Function 1 + Procedure 1 |
| `main2.sql` | Main program | Runs Function 2 + Procedure 2 |
| `backup4.sql` | Backup | Full pg_dump of `mydatabase` after all Stage D changes were applied |
