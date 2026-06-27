"""
metadata.py - Declarative description of every table in the integrated database
(Fantasy Premier League + FIFA World Cup) and helpers that turn that description
into SQL.

Each table entry holds:
  title    - human friendly name shown in the UI
  group    - section used to group tables in the sidebar
  icon     - small emoji used in the UI
  pk       - list of primary-key column names
  label    - SQL expression (using "{a}" as the table alias) that produces a
             friendly one-line label for a row. Used wherever this table is the
             *target* of a foreign key, so the user sees a name, never an id.
  columns  - ordered list of column descriptors:
                name      column name in the DB
                label     header shown in the UI
                type      one of: int, num, text, date, time, bool
                fk        (optional) name of the table this column references
                sensitive (optional) True -> value is masked in the grid
                readonly  (optional) True -> never editable (e.g. trigger-managed)

The KEY UX rule from the assignment is implemented in build_browse_sql():
foreign-key columns are NOT shown as raw ids - they are LEFT JOINed to their
target table and the target's friendly label is displayed instead.
"""

# --------------------------------------------------------------------------- #
# Table definitions
# --------------------------------------------------------------------------- #
TABLES = {
    # ===================== Lookup tables =====================
    "position": {
        "title": "Positions", "group": "Fantasy League", "icon": "🧭",
        "pk": ["position_id"],
        "label": "{a}.position_name",
        "columns": [
            {"name": "position_id",   "label": "ID",            "type": "int"},
            {"name": "position_name", "label": "Position Name", "type": "text"},
            {"name": "short_name",    "label": "Short",         "type": "text"},
        ],
    },
    "match_status": {
        "title": "Match Statuses", "group": "Fantasy League", "icon": "🚦",
        "pk": ["status_id"],
        "label": "{a}.status_name",
        "columns": [
            {"name": "status_id",   "label": "ID",     "type": "int"},
            {"name": "status_name", "label": "Status", "type": "text"},
        ],
    },

    # ===================== Core entities =====================
    "users": {
        "title": "Users", "group": "Fantasy League", "icon": "👤",
        "pk": ["user_id"],
        "label": "{a}.username",
        "columns": [
            {"name": "user_id",           "label": "ID",       "type": "int"},
            {"name": "username",          "label": "Username", "type": "text"},
            {"name": "email",             "label": "Email",    "type": "text"},
            {"name": "password_hash",     "label": "Password", "type": "text", "sensitive": True},
            {"name": "country",           "label": "Country",  "type": "text"},
            {"name": "registration_date", "label": "Registered", "type": "date"},
            {"name": "birth_date",        "label": "Birth Date", "type": "date"},
        ],
    },
    "real_team": {
        "title": "Real Clubs", "group": "Fantasy League", "icon": "🏟️",
        "pk": ["real_team_id"],
        "label": "{a}.team_name",
        "columns": [
            {"name": "real_team_id", "label": "ID",      "type": "int"},
            {"name": "team_name",    "label": "Club",    "type": "text"},
            {"name": "short_name",   "label": "Short",   "type": "text"},
            {"name": "stadium",      "label": "Stadium", "type": "text"},
            {"name": "city",         "label": "City",    "type": "text"},
            {"name": "country",      "label": "Country", "type": "text"},
            {"name": "founded_year", "label": "Founded", "type": "int"},
        ],
    },
    "player": {
        "title": "Players", "group": "Fantasy League", "icon": "⚽",
        "pk": ["player_id"],
        "label": "{a}.first_name || ' ' || {a}.last_name",
        "columns": [
            {"name": "player_id",           "label": "ID",         "type": "int"},
            {"name": "first_name",          "label": "First Name", "type": "text"},
            {"name": "last_name",           "label": "Last Name",  "type": "text"},
            {"name": "nationality",         "label": "Nationality","type": "text"},
            {"name": "price",               "label": "Price (£m)", "type": "num"},
            {"name": "total_points",        "label": "Points",     "type": "int"},
            {"name": "selected_by_percent", "label": "Owned %",    "type": "num"},
            {"name": "birth_date",          "label": "Birth Date", "type": "date"},
            {"name": "contract_start_date", "label": "Contract",   "type": "date"},
            {"name": "real_team_id",        "label": "Club",       "type": "int", "fk": "real_team"},
            {"name": "position_id",         "label": "Position",   "type": "int", "fk": "position"},
            {"name": "person_id",           "label": "World-Cup Person", "type": "text", "fk": "person"},
            {"name": "previous_price",      "label": "Prev Price", "type": "num", "readonly": True},
        ],
    },
    "fantasy_league": {
        "title": "Fantasy Leagues", "group": "Fantasy League", "icon": "🏆",
        "pk": ["league_id"],
        "label": "{a}.league_name",
        "columns": [
            {"name": "league_id",    "label": "ID",          "type": "int"},
            {"name": "league_name",  "label": "League Name",  "type": "text"},
            {"name": "description",  "label": "Description",  "type": "text"},
            {"name": "max_teams",    "label": "Max Teams",    "type": "int"},
            {"name": "budget_limit", "label": "Budget Limit", "type": "num"},
            {"name": "start_date",   "label": "Start",        "type": "date"},
            {"name": "end_date",     "label": "End",          "type": "date"},
            {"name": "created_by",   "label": "Created By",    "type": "int", "fk": "users"},
        ],
    },
    "fantasy_team": {
        "title": "Fantasy Teams", "group": "Fantasy League", "icon": "🛡️",
        "pk": ["team_id"],
        "label": "{a}.team_name",
        "columns": [
            {"name": "team_id",              "label": "ID",          "type": "int"},
            {"name": "team_name",            "label": "Team Name",   "type": "text"},
            {"name": "formation",            "label": "Formation",   "type": "text"},
            {"name": "total_points",         "label": "Points",      "type": "int"},
            {"name": "budget_remaining",     "label": "Budget Left", "type": "num"},
            {"name": "user_id",              "label": "Manager",     "type": "int", "fk": "users"},
            {"name": "league_id",            "label": "League",      "type": "int", "fk": "fantasy_league"},
            {"name": "total_transfers_cost", "label": "Transfers Cost", "type": "num", "readonly": True},
        ],
    },
    "gameweek": {
        "title": "Gameweeks", "group": "Fantasy League", "icon": "📅",
        "pk": ["gameweek_id"],
        "label": "'S' || {a}.season_year || ' GW' || {a}.gameweek_number",
        "columns": [
            {"name": "gameweek_id",     "label": "ID",       "type": "int"},
            {"name": "season_year",     "label": "Season",   "type": "int"},
            {"name": "gameweek_number", "label": "GW #",     "type": "int"},
            {"name": "start_date",      "label": "Start",    "type": "date"},
            {"name": "end_date",        "label": "End",      "type": "date"},
            {"name": "is_finished",     "label": "Finished", "type": "bool"},
        ],
    },
    "match": {
        "title": "Matches (PL)", "group": "Fantasy League", "icon": "🥅",
        "pk": ["match_id"],
        "label": ("(SELECT r.short_name FROM real_team r WHERE r.real_team_id = {a}.home_team_id)"
                  " || ' vs ' || "
                  "(SELECT r.short_name FROM real_team r WHERE r.real_team_id = {a}.away_team_id)"),
        "columns": [
            {"name": "match_id",     "label": "ID",        "type": "int"},
            {"name": "match_date",   "label": "Date",      "type": "date"},
            {"name": "home_team_id", "label": "Home",      "type": "int", "fk": "real_team"},
            {"name": "away_team_id", "label": "Away",      "type": "int", "fk": "real_team"},
            {"name": "home_score",   "label": "Home Goals","type": "int"},
            {"name": "away_score",   "label": "Away Goals","type": "int"},
            {"name": "gameweek_id",  "label": "Gameweek",  "type": "int", "fk": "gameweek"},
            {"name": "status_id",    "label": "Status",    "type": "int", "fk": "match_status"},
        ],
    },
    "player_gameweek_stats": {
        "title": "Player GW Stats", "group": "Fantasy League", "icon": "📊",
        "pk": ["stat_id"],
        "label": "'Stat #' || {a}.stat_id",
        "columns": [
            {"name": "stat_id",        "label": "ID",      "type": "int"},
            {"name": "player_id",      "label": "Player",  "type": "int", "fk": "player"},
            {"name": "match_id",       "label": "Match",   "type": "int", "fk": "match"},
            {"name": "gameweek_id",    "label": "Gameweek","type": "int", "fk": "gameweek"},
            {"name": "minutes_played", "label": "Minutes", "type": "int"},
            {"name": "goals_scored",   "label": "Goals",   "type": "int"},
            {"name": "assists",        "label": "Assists", "type": "int"},
            {"name": "clean_sheet",    "label": "Clean Sheet", "type": "bool"},
            {"name": "yellow_cards",   "label": "Yellow",  "type": "int"},
            {"name": "red_cards",      "label": "Red",     "type": "int"},
            {"name": "saves",          "label": "Saves",   "type": "int"},
            {"name": "bonus_points",   "label": "Bonus",   "type": "int"},
            {"name": "total_points",   "label": "Points",  "type": "int"},
        ],
    },
    "fantasy_team_selection": {
        "title": "Squad Selections", "group": "Fantasy League", "icon": "📋",
        "pk": ["selection_id"],
        "label": "'Selection #' || {a}.selection_id",
        "columns": [
            {"name": "selection_id",    "label": "ID",        "type": "int"},
            {"name": "team_id",         "label": "Team",      "type": "int", "fk": "fantasy_team"},
            {"name": "player_id",       "label": "Player",    "type": "int", "fk": "player"},
            {"name": "gameweek_id",     "label": "Gameweek",  "type": "int", "fk": "gameweek"},
            {"name": "is_captain",      "label": "Captain",   "type": "bool"},
            {"name": "is_vice_captain", "label": "Vice",      "type": "bool"},
            {"name": "is_on_bench",     "label": "On Bench",  "type": "bool"},
            {"name": "bench_order",     "label": "Bench Order","type": "int"},
            {"name": "points_scored",   "label": "Points",    "type": "int"},
        ],
    },
    "transfer": {
        "title": "Transfers", "group": "Fantasy League", "icon": "🔁",
        "pk": ["transfer_id"],
        "label": "'Transfer #' || {a}.transfer_id",
        "columns": [
            {"name": "transfer_id",   "label": "ID",          "type": "int"},
            {"name": "team_id",       "label": "Team",        "type": "int", "fk": "fantasy_team"},
            {"name": "player_out_id", "label": "Player Out",  "type": "int", "fk": "player"},
            {"name": "player_in_id",  "label": "Player In",   "type": "int", "fk": "player"},
            {"name": "gameweek_id",   "label": "Gameweek",    "type": "int", "fk": "gameweek"},
            {"name": "price_paid",    "label": "Price Paid",  "type": "num"},
            {"name": "transfer_date", "label": "Date",        "type": "date"},
        ],
    },
    "league_standing": {
        "title": "League Standings", "group": "Fantasy League", "icon": "🥇",
        "pk": ["standing_id"],
        "label": "'Standing #' || {a}.standing_id",
        "columns": [
            {"name": "standing_id", "label": "ID",       "type": "int"},
            {"name": "league_id",   "label": "League",   "type": "int", "fk": "fantasy_league"},
            {"name": "team_id",     "label": "Team",     "type": "int", "fk": "fantasy_team"},
            {"name": "gameweek_id", "label": "Gameweek", "type": "int", "fk": "gameweek"},
            {"name": "points",      "label": "Points",   "type": "int"},
            {"name": "rank",        "label": "Rank",     "type": "int"},
        ],
    },

    # ===================== FIFA World Cup (integrated) =====================
    "person": {
        "title": "Persons", "group": "World Cup", "icon": "🌍",
        "pk": ["id"],
        "label": "{a}.givenname || ' ' || COALESCE({a}.familyname, '')",
        "columns": [
            {"name": "id",            "label": "ID",          "type": "text"},
            {"name": "givenname",     "label": "Given Name",  "type": "text"},
            {"name": "familyname",    "label": "Family Name", "type": "text"},
            {"name": "wikipediapage", "label": "Wikipedia",   "type": "text"},
        ],
    },
    "intl_team": {
        "title": "National Teams", "group": "World Cup", "icon": "🚩",
        "pk": ["teamcode"],
        "label": "{a}.countryname",
        "columns": [
            {"name": "teamcode",          "label": "Code",          "type": "text"},
            {"name": "countryname",       "label": "Country",       "type": "text"},
            {"name": "confederationname", "label": "Confederation", "type": "text"},
            {"name": "confederationcode", "label": "Conf. Code",    "type": "text"},
            {"name": "wikipediapage",     "label": "Wikipedia",     "type": "text"},
        ],
    },
    "stadium": {
        "title": "Stadiums", "group": "World Cup", "icon": "🏛️",
        "pk": ["stadiumid"],
        "label": "{a}.name",
        "columns": [
            {"name": "stadiumid",     "label": "ID",        "type": "text"},
            {"name": "name",          "label": "Stadium",   "type": "text"},
            {"name": "city",          "label": "City",      "type": "text"},
            {"name": "country",       "label": "Country",   "type": "text"},
            {"name": "capacity",      "label": "Capacity",  "type": "int"},
            {"name": "wikipediapage", "label": "Wikipedia", "type": "text"},
        ],
    },
    "referee": {
        "title": "Referees", "group": "World Cup", "icon": "🧑‍⚖️",
        "pk": ["id"],
        "label": "(SELECT pe.givenname || ' ' || COALESCE(pe.familyname,'') FROM person pe WHERE pe.id = {a}.id)",
        "columns": [
            {"name": "id",                "label": "Person",        "type": "text", "fk": "person", "pk_is_fk": True},
            {"name": "country",           "label": "Country",       "type": "text"},
            {"name": "confederationname", "label": "Confederation", "type": "text"},
            {"name": "confederationcode", "label": "Conf. Code",    "type": "text"},
        ],
    },
    "intl_player": {
        "title": "World-Cup Players", "group": "World Cup", "icon": "🎽",
        "pk": ["id"],
        "label": "(SELECT pe.givenname || ' ' || COALESCE(pe.familyname,'') FROM person pe WHERE pe.id = {a}.id)",
        "columns": [
            {"name": "id",          "label": "Person",   "type": "text", "fk": "person", "pk_is_fk": True},
            {"name": "dateofbirth", "label": "Birth Date","type": "date"},
            {"name": "teamcode",    "label": "Team",     "type": "text", "fk": "intl_team"},
        ],
    },
    "intl_match": {
        "title": "World-Cup Matches", "group": "World Cup", "icon": "🌐",
        "pk": ["matchid"],
        "label": "{a}.tournament || ' - ' || {a}.stage",
        "columns": [
            {"name": "matchid",       "label": "ID",         "type": "text"},
            {"name": "tournament",    "label": "Tournament", "type": "text"},
            {"name": "stage",         "label": "Stage",      "type": "text"},
            {"name": "matchdate",     "label": "Date",       "type": "date"},
            {"name": "matchtime",     "label": "Time",       "type": "time"},
            {"name": "hometeamcode",  "label": "Home",       "type": "text", "fk": "intl_team"},
            {"name": "guestteamcode", "label": "Guest",      "type": "text", "fk": "intl_team"},
            {"name": "stadiumid",     "label": "Stadium",    "type": "text", "fk": "stadium"},
            {"name": "refereeid",     "label": "Referee",    "type": "text", "fk": "referee"},
        ],
    },
    "match_event": {
        "title": "Match Events", "group": "World Cup", "icon": "⏱️",
        "pk": ["matcheventid"],
        "label": "{a}.eventtype || ' @' || {a}.minute",
        "columns": [
            {"name": "matcheventid", "label": "ID",      "type": "text"},
            {"name": "matchid",      "label": "Match",   "type": "text", "fk": "intl_match"},
            {"name": "id",           "label": "Player",  "type": "text", "fk": "intl_player"},
            {"name": "eventtype",    "label": "Event",   "type": "text"},
            {"name": "minute",       "label": "Minute",  "type": "text"},
        ],
    },
    "intl_player_match_stats": {
        "title": "WC Player Match Stats", "group": "World Cup", "icon": "📈",
        "pk": ["matchid", "playerid"],
        "label": "{a}.matchid || ' / ' || {a}.playerid",
        "columns": [
            {"name": "matchid",     "label": "Match",   "type": "text", "fk": "intl_match"},
            {"name": "playerid",    "label": "Player",  "type": "text", "fk": "intl_player"},
            {"name": "position",    "label": "Position","type": "text"},
            {"name": "shirtnumber", "label": "Shirt #", "type": "int"},
        ],
    },
}

# Order tables appear in the sidebar.
TABLE_ORDER = [
    "users", "real_team", "player", "position", "match_status",
    "fantasy_league", "fantasy_team", "gameweek", "match",
    "player_gameweek_stats", "fantasy_team_selection", "transfer", "league_standing",
    "person", "intl_team", "stadium", "referee", "intl_player",
    "intl_match", "match_event", "intl_player_match_stats",
]


# --------------------------------------------------------------------------- #
# SQL builders
# --------------------------------------------------------------------------- #
def _is_resolvable_fk(meta, col):
    """A FK column is shown as a name unless it is (also) the table's own PK."""
    return bool(col.get("fk")) and not col.get("pk_is_fk") and col["name"] not in meta["pk"]


def build_browse_sql(table, search_term=None, limit=500):
    """
    Build a SELECT that lists rows with foreign keys resolved to friendly names.
    Returns (sql, params, headers).
    """
    meta = TABLES[table]
    a = "t"
    selects, joins, headers = [], [], []
    jn = 0
    for col in meta["columns"]:
        # A literal '%' in an alias must be escaped because psycopg2 interprets
        # '%' as a parameter marker in the query string.
        alias = col["label"].replace("%", "%%")
        if _is_resolvable_fk(meta, col):
            tgt = TABLES[col["fk"]]
            ja = "j%d" % jn
            jn += 1
            tgt_pk = tgt["pk"][0]
            selects.append('%s AS "%s"' % (tgt["label"].format(a=ja), alias))
            joins.append("LEFT JOIN %s %s ON %s.%s = %s.%s"
                         % (col["fk"], ja, ja, tgt_pk, a, col["name"]))
        elif col.get("sensitive"):
            selects.append('\'••••••\' AS "%s"' % alias)
        else:
            selects.append('%s.%s AS "%s"' % (a, col["name"], alias))
        headers.append(col["label"])

    order = ", ".join("%s.%s" % (a, p) for p in meta["pk"])
    inner = "SELECT %s FROM %s %s %s ORDER BY %s" % (
        ", ".join(selects), table, a, " ".join(joins), order)

    params = []
    if search_term:
        sql = "SELECT * FROM (%s) q WHERE q::text ILIKE %%s LIMIT %d" % (inner, limit)
        params.append("%%%s%%" % search_term)
    else:
        sql = "%s LIMIT %d" % (inner, limit)
    return sql, params, headers


def build_select_row_sql(table):
    """SELECT all raw columns for one row, located by PK. Returns (sql, colnames)."""
    meta = TABLES[table]
    cols = [c["name"] for c in meta["columns"]]
    where = " AND ".join("%s = %%s" % p for p in meta["pk"])
    sql = "SELECT %s FROM %s WHERE %s" % (", ".join(cols), table, where)
    return sql, cols


def editable_columns(table, mode):
    """
    Columns the user can fill in a form.
      insert -> everything except read-only (trigger-managed) columns
      update -> same, but PK columns become read-only (they are the lookup key)
    """
    meta = TABLES[table]
    out = []
    for col in meta["columns"]:
        if col.get("readonly"):
            continue
        c = dict(col)
        if mode == "update" and col["name"] in meta["pk"]:
            c["locked"] = True
        out.append(c)
    return out


def fk_options_sql(table, search_term=None, limit=200):
    """SQL listing (id, label) options for a foreign-key picker on `table`."""
    meta = TABLES[table]
    a = "t"
    pk = meta["pk"][0]
    label = meta["label"].format(a=a)
    params = []
    where = ""
    if search_term:
        where = "WHERE (%s) ILIKE %%s OR CAST(%s.%s AS text) ILIKE %%s" % (label, a, pk)
        params = ["%%%s%%" % search_term, "%%%s%%" % search_term]
    sql = ('SELECT %s.%s AS id, %s AS label FROM %s %s %s ORDER BY label LIMIT %d'
           % (a, pk, label, table, a, where, limit))
    return sql, params


def label_for_id(table):
    """SQL returning the friendly label for a single PK value (single-col PK)."""
    meta = TABLES[table]
    a = "t"
    pk = meta["pk"][0]
    return 'SELECT %s FROM %s %s WHERE %s.%s = %%s' % (meta["label"].format(a=a), table, a, a, pk)
