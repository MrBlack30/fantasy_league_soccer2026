"""
programs.py - Definitions for the "Queries" and "Programs" screens.

QUERIES  : a curated set of the Stage B queries (some made interactive with
           parameters) that run on the integrated database.
PROGRAMS : the Stage D PL/pgSQL sub-programs - 2 functions and 2 procedures -
           callable from the GUI, exceeding the assignment's minimum of 2 + 2.
"""

# --------------------------------------------------------------------------- #
# Stage B queries
# --------------------------------------------------------------------------- #
# Each query: id, title, description, sql (with %s placeholders), and params.
# A param: name, label, type (int/text), default.
QUERIES = [
    {
        "id": "q1",
        "title": "Young Scouting Report",
        "desc": "Players born in a chosen year who play for clubs in a chosen country.",
        "params": [
            {"name": "year",    "label": "Birth Year", "type": "int",  "default": "2002"},
            {"name": "country", "label": "Club Country","type": "text", "default": "England"},
        ],
        "sql": """
            SELECT p.first_name AS "First Name",
                   p.last_name  AS "Last Name",
                   p.price      AS "Price (£m)",
                   EXTRACT(YEAR FROM p.birth_date)::int AS "Birth Year"
            FROM   player p
            WHERE  EXTRACT(YEAR FROM p.birth_date) = %s
              AND  p.real_team_id IN (SELECT real_team_id FROM real_team WHERE country = %s)
            ORDER  BY p.price DESC
        """,
    },
    {
        "id": "q2",
        "title": "Rich Teams (above August average)",
        "desc": "Fantasy teams whose remaining budget is above the average budget "
                "of teams in leagues that started in August.",
        "params": [],
        "sql": """
            SELECT ft.team_name        AS "Team",
                   ft.budget_remaining AS "Budget Left",
                   u.username          AS "Manager"
            FROM   fantasy_team ft
            JOIN   users u ON ft.user_id = u.user_id
            JOIN  (SELECT AVG(budget_remaining) AS avg_budget
                   FROM   fantasy_team ft_sub
                   JOIN   fantasy_league fl_sub ON ft_sub.league_id = fl_sub.league_id
                   WHERE  EXTRACT(MONTH FROM fl_sub.start_date) = 8) avg_table
                   ON ft.budget_remaining > avg_table.avg_budget
            ORDER  BY ft.budget_remaining DESC
        """,
    },
    {
        "id": "q4",
        "title": "Global Leaderboard",
        "desc": "Teams that scored more than a chosen number of points, in leagues "
                "whose season ended in a chosen year.",
        "params": [
            {"name": "min_points", "label": "Min Points", "type": "int", "default": "50"},
            {"name": "year",       "label": "Season End Year", "type": "int", "default": "2024"},
        ],
        "sql": """
            SELECT ft.team_name    AS "Team",
                   ft.total_points AS "Points",
                   fl.league_name  AS "League"
            FROM   fantasy_team ft
            JOIN   fantasy_league fl ON ft.league_id = fl.league_id
            WHERE  ft.total_points > %s
              AND  EXTRACT(YEAR FROM fl.end_date) = %s
            ORDER  BY ft.total_points DESC
        """,
    },
    {
        "id": "q5",
        "title": "Goals by Nationality (by month)",
        "desc": "Total goals scored, grouped by player nationality, in a chosen "
                "calendar month - only nationalities above a goal threshold.",
        "params": [
            {"name": "month",     "label": "Month (1-12)", "type": "int", "default": "12"},
            {"name": "min_goals", "label": "Min Goals",    "type": "int", "default": "10"},
        ],
        "sql": """
            SELECT p.nationality          AS "Nationality",
                   SUM(pgs.goals_scored)  AS "Total Goals",
                   COUNT(DISTINCT p.player_id) AS "Players"
            FROM   player p
            JOIN   player_gameweek_stats pgs ON p.player_id = pgs.player_id
            JOIN   match m ON pgs.match_id = m.match_id
            WHERE  EXTRACT(MONTH FROM m.match_date) = %s
            GROUP  BY p.nationality
            HAVING SUM(pgs.goals_scored) > %s
            ORDER  BY "Total Goals" DESC
        """,
    },
    {
        "id": "q8",
        "title": "Historic Clubs & Star Player",
        "desc": "Clubs founded before a chosen year, with their squad size and most "
                "expensive player price.",
        "params": [
            {"name": "before_year", "label": "Founded Before", "type": "int", "default": "1900"},
        ],
        "sql": """
            SELECT rt.team_name        AS "Club",
                   rt.founded_year     AS "Founded",
                   COUNT(p.player_id)  AS "Squad Size",
                   MAX(p.price)        AS "Top Price (£m)"
            FROM   real_team rt
            JOIN   player p ON rt.real_team_id = p.real_team_id
            WHERE  rt.founded_year < %s
            GROUP  BY rt.team_name, rt.founded_year
            ORDER  BY "Top Price (£m)" DESC
        """,
    },
    {
        "id": "qwc",
        "title": "World Cup Finals (integrated DB)",
        "desc": "All Final-stage World Cup matches with the two teams and host city "
                "- runs across the integrated FIFA tables.",
        "params": [],
        "sql": """
            SELECT im.tournament              AS "Tournament",
                   im.matchdate               AS "Date",
                   home_t.countryname         AS "Home",
                   guest_t.countryname        AS "Guest",
                   s.name                     AS "Stadium",
                   s.city                     AS "City"
            FROM   intl_match im
            JOIN   intl_team home_t  ON im.hometeamcode  = home_t.teamcode
            JOIN   intl_team guest_t ON im.guestteamcode = guest_t.teamcode
            JOIN   stadium   s       ON im.stadiumid     = s.stadiumid
            WHERE  im.stage = 'final'
            ORDER  BY im.matchdate
        """,
    },
]


# --------------------------------------------------------------------------- #
# Stage D programs (functions + procedures)
# --------------------------------------------------------------------------- #
# kind: "function_table" | "refcursor" | "procedure"
PROGRAMS = [
    {
        "id": "fn_eval",
        "kind": "function_table",
        "icon": "🧮",
        "title": "Function: Evaluate Fantasy Team",
        "fn": "fn_evaluate_fantasy_team",
        "desc": "Returns a one-row health report for a team in a gameweek: squad "
                "value, starting-XI points, average, captain and a health rating "
                "(Excellent / Good / Average / Poor).",
        "params": [
            {"name": "team_id",     "label": "Team ID",     "type": "int", "default": "1"},
            {"name": "gameweek_id", "label": "Gameweek ID", "type": "int", "default": "1"},
        ],
        "sql": "SELECT * FROM fn_evaluate_fantasy_team(%s, %s)",
    },
    {
        "id": "fn_stats",
        "kind": "refcursor",
        "icon": "📜",
        "title": "Function: Player Season Stats",
        "fn": "fn_get_player_season_stats",
        "desc": "Returns a REF CURSOR with one row per gameweek the player appeared "
                "in, joined with match and team info. Raises an error if the player "
                "id does not exist.",
        "params": [
            {"name": "player_id", "label": "Player ID", "type": "int", "default": "423"},
        ],
        "sql": "SELECT fn_get_player_season_stats(%s)",
        "cursor_name": "player_stats_cursor",
    },
    {
        "id": "pr_prices",
        "kind": "procedure",
        "icon": "💰",
        "title": "Procedure: Update Player Prices",
        "fn": "pr_update_player_prices",
        "desc": "Walks every player and applies weekly price rises/falls based on "
                "points and ownership (fires the price-change trigger). Shows the "
                "NOTICE log and the players whose price changed.",
        "params": [],
        "call": "CALL pr_update_player_prices()",
        "post_sql": """
            SELECT first_name || ' ' || last_name AS "Player",
                   previous_price                 AS "Old Price",
                   price                          AS "New Price",
                   ROUND(price - previous_price, 1) AS "Change"
            FROM   player
            WHERE  previous_price IS NOT NULL
            ORDER  BY ABS(price - previous_price) DESC, "Player"
            LIMIT  100
        """,
    },
    {
        "id": "pr_points",
        "kind": "procedure",
        "icon": "🏅",
        "title": "Procedure: Process Gameweek Points",
        "fn": "pr_process_gameweek_points",
        "desc": "Scores every squad selection for a gameweek (captain x2, bench 0), "
                "rolls totals into the teams, and snapshots the league standings. "
                "Shows the resulting standings.",
        "params": [
            {"name": "gameweek_id", "label": "Gameweek ID", "type": "int", "default": "1"},
        ],
        "call": "CALL pr_process_gameweek_points(%s)",
        "post_sql": """
            SELECT ls.rank          AS "Rank",
                   ft.team_name     AS "Team",
                   ls.points        AS "Points"
            FROM   league_standing ls
            JOIN   fantasy_team ft ON ls.team_id = ft.team_id
            WHERE  ls.gameweek_id = %s
            ORDER  BY ls.rank
            LIMIT  100
        """,
    },
]
