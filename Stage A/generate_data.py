#!/usr/bin/env python3
"""
Fantasy Soccer League - Bulk Data Generator
Method 2: Python script generating SQL INSERT statements

Outputs:
  python_inserts.sql  — SQL file with all bulk data
  users.csv           — CSV of USERS table (used by Method 3)

Usage:  python3 generate_data.py
"""

import random
import datetime
import hashlib
import csv
import sys
import os

random.seed(42)

# ============================================================
# Configuration
# ============================================================
PLAYERS_PER_TEAM     = 30       # 30 × 20 teams = 600 players
NUM_USERS            = 500
NUM_FANTASY_LEAGUES  = 500
NUM_FANTASY_TEAMS    = 500
SELECTION_GAMEWEEKS  = 3        # generate selections for GWs 1-3  → 500×3×15 = 22,500
STANDING_GAMEWEEKS   = 5        # generate standings for GWs 1-5
NUM_TRANSFERS        = 1000
SEASON_YEAR          = 2023
BATCH_SIZE           = 500      # rows per INSERT statement

OUTPUT_SQL  = 'python_inserts.sql'
OUTPUT_CSV  = 'users.csv'

# ============================================================
# Data Pools
# ============================================================
REAL_TEAMS = [
    (1,  "Arsenal",                  "ARS", "Emirates Stadium",          "London",        "England", 1886),
    (2,  "Aston Villa",              "AVL", "Villa Park",                 "Birmingham",    "England", 1874),
    (3,  "Brentford",                "BRE", "Gtech Community Stadium",    "London",        "England", 1889),
    (4,  "Brighton",                 "BHA", "Amex Stadium",               "Brighton",      "England", 1901),
    (5,  "Burnley",                  "BUR", "Turf Moor",                  "Burnley",       "England", 1882),
    (6,  "Chelsea",                  "CHE", "Stamford Bridge",            "London",        "England", 1905),
    (7,  "Crystal Palace",           "CRY", "Selhurst Park",              "London",        "England", 1905),
    (8,  "Everton",                  "EVE", "Goodison Park",              "Liverpool",     "England", 1878),
    (9,  "Fulham",                   "FUL", "Craven Cottage",             "London",        "England", 1879),
    (10, "Liverpool",                "LIV", "Anfield",                    "Liverpool",     "England", 1892),
    (11, "Luton Town",               "LUT", "Kenilworth Road",            "Luton",         "England", 1885),
    (12, "Manchester City",          "MCI", "Etihad Stadium",             "Manchester",    "England", 1880),
    (13, "Manchester United",        "MUN", "Old Trafford",               "Manchester",    "England", 1878),
    (14, "Newcastle United",         "NEW", "St. James Park",             "Newcastle",     "England", 1892),
    (15, "Nottingham Forest",        "NFO", "City Ground",                "Nottingham",    "England", 1865),
    (16, "Sheffield United",         "SHU", "Bramall Lane",               "Sheffield",     "England", 1889),
    (17, "Tottenham Hotspur",        "TOT", "Tottenham Hotspur Stadium",  "London",        "England", 1882),
    (18, "West Ham United",          "WHU", "London Stadium",             "London",        "England", 1895),
    (19, "Wolverhampton Wanderers",  "WOL", "Molineux Stadium",           "Wolverhampton", "England", 1877),
    (20, "Leicester City",           "LEI", "King Power Stadium",         "Leicester",     "England", 1884),
]

FIRST_NAMES = [
    "James","Oliver","Harry","George","Jack","Noah","Charlie","Jacob","Alfie","Freddie",
    "Oscar","Archie","Henry","Leo","Ethan","Mason","Lucas","William","Thomas","Liam",
    "Mohammed","Adam","Kai","Marcus","Raheem","Bukayo","Declan","Jordan","Kyle","Trent",
    "Aaron","Ben","Erling","Kevin","Phil","Rodri","Bruno","Casemiro","Rasmus","Alejandro",
    "Callum","Billy","Ivan","Yoane","Wilfried","Patrick","Nicolas","Pape","Dominic","Darwin",
    "Diogo","Ibrahima","Ryan","Luis","Roberto","Conor","Harvey","Curtis","Stefan","Fabio",
    "Andy","Antoine","Moussa","Serge","Ismaila","Pedro","Alex","David","Fernando","Carlos",
    "Miguel","Rafael","Kylian","Ousmane","Sadio","Riyad","Richarlison","Gabriel","Emiliano",
    "Douglas","Leon","Eberechi","Michael","Daniel","Josh","Tim","Kenny","Aleksandar","Lautaro",
    "Julian","Christopher","Nathan","Andre","Mateus","Bernardo","Ruben","Joao","Renato","Goncalo",
    "Santiago","Lorenzo","Federico","Matteo","Antonio","Giuseppe","Francesco","Marco","Andrea","Luca"
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Anderson",
    "Taylor","Thomas","Moore","Martin","Jackson","Thompson","White","Lopez","Lee","Salah",
    "Haaland","De Bruyne","Silva","Walker","Fernandes","Rashford","Saka","Odegaard","Rice","Sterling",
    "Mount","Kane","Son","Ward-Prowse","Trippier","Maddison","Isak","Gordon","Barnes","Dier",
    "Robertson","Henderson","Thiago","Elliott","Jota","Nunez","Gomez","Konate","Ederson","Dias",
    "Stones","Akanji","Gvardiol","Grealish","Doku","Foden","Lindelof","Evans","Dalot","Mainoo",
    "Garnacho","McTominay","Ramsdale","Gabriel","Zinchenko","Trossard","Havertz","Timber","Saliba",
    "Pope","Burn","Botman","Schar","Longstaff","Willock","Anderson","Guimaraes","Tonali","Murphy",
    "Almiron","Pedro","Neto","Onana","Varane","Sancho","McAtee","Bobb","Lewis","Pickford",
    "Keane","Holgate","Mykolenko","Calvert-Lewin","Doucoure","Branthwaite","Patterson","Tarkowski",
    "Rodriguez","Martinez","Hernandez","Gonzalez","Perez","Sanchez","Ramirez","Torres","Flores","Cruz"
]

NATIONALITIES = [
    "English","Spanish","French","German","Brazilian","Argentine","Portuguese","Dutch","Belgian",
    "Italian","Uruguayan","Colombian","Senegalese","Ghanaian","Nigerian","Egyptian","Moroccan",
    "Ivorian","Swedish","Danish","Norwegian","Polish","Czech","Croatian","Serbian","Welsh",
    "Scottish","Irish","Japanese","South Korean","Australian","Algerian","Tunisian","Guinean","Malian"
]

COUNTRIES = [
    "England","Spain","Germany","France","Italy","Netherlands","Belgium","Portugal","Brazil",
    "Argentina","USA","Canada","Australia","Japan","South Korea","India","Mexico","Colombia",
    "Chile","Sweden","Norway","Denmark","Poland","Czech Republic","Romania","Turkey",
    "Nigeria","Ghana","South Africa","Egypt","Morocco","Israel","Greece","Ukraine","Russia"
]

FORMATIONS = ["4-4-2","4-3-3","3-5-2","4-2-3-1","3-4-3","5-3-2","4-5-1","4-1-4-1","3-4-1-2"]

EMAIL_DOMAINS = ["gmail.com","yahoo.com","hotmail.com","outlook.com","protonmail.com","icloud.com"]

LG_ADJ = ["Premier","Elite","Champions","Ultimate","Classic","Fantasy","Super","Legend","Master",
           "Pro","All-Star","Dream","Power","Victory","Glory","Mighty","Royal","Golden","Silver",
           "Diamond","Platinum","Thunder","Storm","Blitz","Titan","Supreme","Infinite","Galaxy"]

LG_NOUN = ["League","Cup","Championship","Division","Arena","Trophy","Tournament","Challenge",
            "Series","Hub","Zone","Club","Warriors","United","Squad","Legends","Syndicate"]

# ============================================================
# Helper Functions
# ============================================================
def q(s):
    """Return SQL-quoted string or NULL."""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def rand_date(start, end):
    """Random date between start and end (both datetime.date)."""
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + datetime.timedelta(days=random.randint(0, delta))

def pw_hash(uid):
    """Deterministic fake password hash."""
    return hashlib.sha256(f"fantasy_pw_{uid}".encode()).hexdigest()

def calc_points(pos_id, minutes, goals, assists, clean, yellow, red, saves, bonus):
    """Simplified FPL-style fantasy point calculation."""
    pts = 0
    if minutes >= 60:
        pts += 2
    elif minutes > 0:
        pts += 1
    if pos_id == 1:    # GK
        pts += goals * 6 + assists * 3 + (4 if (clean and minutes >= 60) else 0) + (saves // 3)
    elif pos_id == 2:  # DEF
        pts += goals * 6 + assists * 3 + (4 if (clean and minutes >= 60) else 0)
    elif pos_id == 3:  # MID
        pts += goals * 5 + assists * 3 + (1 if (clean and minutes >= 60) else 0)
    else:              # FWD
        pts += goals * 4 + assists * 3
    pts -= yellow
    pts -= red * 3
    pts += bonus
    return max(pts, -4)  # minimum -4 in FPL

# ============================================================
# Round-Robin Schedule (double round-robin for 20 teams)
# Returns list of 38 rounds, each round is list of (home_id, away_id)
# ============================================================
def make_schedule(team_ids):
    teams = list(team_ids)
    n = len(teams)
    first_half = []
    for round_num in range(n - 1):
        matches = []
        for i in range(n // 2):
            h = teams[i]
            a = teams[n - 1 - i]
            matches.append((h, a) if round_num % 2 == 0 else (a, h))
        first_half.append(matches)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    second_half = [[(a, h) for h, a in rnd] for rnd in first_half]
    return first_half + second_half

# ============================================================
# Main
# ============================================================
all_lines = []
def emit(line=''):
    all_lines.append(line)

print("Generating Fantasy Soccer League data...")

emit('-- ================================================================')
emit('-- Fantasy Soccer League - Python Generated Data (Method 2)')
emit('-- Generated by: generate_data.py')
emit(f'-- Generated on: {datetime.date.today()}')
emit('-- ================================================================')
emit()

# ---------------------------------------------------------------
# REAL_TEAM (20 rows)
# ---------------------------------------------------------------
print("  Generating REAL_TEAM...")
emit('-- ----------------------------------------------------------------')
emit('-- REAL_TEAM (20 rows)')
emit('-- ----------------------------------------------------------------')
vals = []
for (rtid, name, short, stadium, city, country, founded) in REAL_TEAMS:
    vals.append(f"({rtid},{q(name)},{q(short)},{q(stadium)},{q(city)},{q(country)},{founded})")
emit('INSERT INTO REAL_TEAM (real_team_id,team_name,short_name,stadium,city,country,founded_year) VALUES')
emit(',\n'.join(vals) + ';')
emit()

# ---------------------------------------------------------------
# PLAYERS (600 rows: 30 per team)
# pos distribution per squad: 3 GK, 8 DEF, 10 MID, 9 FWD
# ---------------------------------------------------------------
print("  Generating PLAYER (600 rows)...")
POS_DIST = [1]*3 + [2]*8 + [3]*10 + [4]*9   # 30 players

players = []      # list of (player_id, real_team_id, pos_id, price)
player_rows = []
player_id = 1

for (rtid, *_rest) in REAL_TEAMS:
    squad_pos = POS_DIST[:]
    random.shuffle(squad_pos)
    for pos_id in squad_pos:
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        nat = random.choice(NATIONALITIES)
        if pos_id == 1:
            price = round(random.uniform(4.0, 6.5), 1)
        elif pos_id == 2:
            price = round(random.uniform(4.0, 8.5), 1)
        elif pos_id == 3:
            price = round(random.uniform(4.5, 12.5), 1)
        else:
            price = round(random.uniform(5.0, 13.5), 1)
        total_pts = random.randint(0, 200)
        sel_pct   = round(random.uniform(0.0, 60.0), 2)
        birth     = rand_date(datetime.date(1990,1,1), datetime.date(2003,12,31))
        contract  = rand_date(datetime.date(2018,1,1), datetime.date(2023,7,31))
        player_rows.append(
            f"({player_id},{q(fn)},{q(ln)},{q(nat)},{price},{total_pts},"
            f"{sel_pct},{q(str(birth))},{q(str(contract))},{rtid},{pos_id})"
        )
        players.append((player_id, rtid, pos_id, price))
        player_id += 1

emit('-- ----------------------------------------------------------------')
emit('-- PLAYER (600 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO PLAYER (player_id,first_name,last_name,nationality,price,total_points,')
emit('    selected_by_percent,birth_date,contract_start_date,real_team_id,position_id) VALUES')
emit(',\n'.join(player_rows) + ';')
emit()

# Build lookup structures
player_map    = {p[0]: p for p in players}           # pid -> (pid, tid, pos_id, price)
players_by_team = {}
for pid, tid, posid, price in players:
    players_by_team.setdefault(tid, []).append(pid)

# ---------------------------------------------------------------
# USERS (500 rows)  — also written to users.csv for Method 3
# ---------------------------------------------------------------
print("  Generating USERS (500 rows)...")
users_data  = []
user_rows   = []

for uid in range(1, NUM_USERS + 1):
    fn  = random.choice(FIRST_NAMES)
    ln  = random.choice(LAST_NAMES)
    uname = f"{fn[:4].lower()}{ln[:5].lower()}{uid}"[:50]
    email = f"{fn.lower()}{uid}@{random.choice(EMAIL_DOMAINS)}"
    ph    = pw_hash(uid)
    cntry = random.choice(COUNTRIES)
    reg   = rand_date(datetime.date(2020,1,1), datetime.date(2023,8,10))
    birth = rand_date(datetime.date(1970,1,1), datetime.date(2002,12,31))
    users_data.append((uid, uname, email, ph, cntry, str(reg), str(birth)))
    user_rows.append(
        f"({uid},{q(uname)},{q(email)},{q(ph)},{q(cntry)},{q(str(reg))},{q(str(birth))})"
    )

emit('-- ----------------------------------------------------------------')
emit('-- USERS (500 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO USERS (user_id,username,email,password_hash,country,registration_date,birth_date) VALUES')
emit(',\n'.join(user_rows) + ';')
emit()

# ---------------------------------------------------------------
# GAMEWEEK (38 rows — 2023/24 PL season)
# ---------------------------------------------------------------
print("  Generating GAMEWEEK (38 rows)...")
gw_rows   = []
gameweeks = []   # list of (gw_id, start_date, end_date)
gw_start  = datetime.date(2023, 8, 11)

for gw_num in range(1, 39):
    gw_id  = gw_num
    gw_end = gw_start + datetime.timedelta(days=3)
    done   = 1 if gw_num <= 32 else 0
    gw_rows.append(f"({gw_id},{SEASON_YEAR},{gw_num},{q(str(gw_start))},{q(str(gw_end))},{done})")
    gameweeks.append((gw_id, gw_start, gw_end))
    gw_start += datetime.timedelta(days=7)

emit('-- ----------------------------------------------------------------')
emit('-- GAMEWEEK (38 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO GAMEWEEK (gameweek_id,season_year,gameweek_number,start_date,end_date,is_finished) VALUES')
emit(',\n'.join(gw_rows) + ';')
emit()

# ---------------------------------------------------------------
# MATCH (380 rows — full PL season round-robin)
# ---------------------------------------------------------------
print("  Generating MATCH (380 rows)...")
schedule = make_schedule(list(range(1, 21)))

match_rows    = []
match_id      = 1
team_match_gw = {}    # (team_id, gw_0idx) -> (match_id, 'home'|'away')
match_results = {}    # match_id -> (h_score, a_score, h_tid, a_tid)

for gw_idx, gw_fixtures in enumerate(schedule):
    gw_id   = gw_idx + 1
    gw_date = gameweeks[gw_idx][1]
    done    = gw_idx < 32
    status  = 3 if done else 1   # 3=Finished, 1=Scheduled

    for (h_tid, a_tid) in gw_fixtures:
        if done:
            h_sc = random.randint(0, 4)
            a_sc = random.randint(0, 3)
            h_val, a_val = str(h_sc), str(a_sc)
            match_results[match_id] = (h_sc, a_sc, h_tid, a_tid)
        else:
            h_val = a_val = 'NULL'

        m_date = gw_date + datetime.timedelta(days=random.randint(0, 3))
        match_rows.append(
            f"({match_id},{h_val},{a_val},{q(str(m_date))},{h_tid},{a_tid},{gw_id},{status})"
        )
        team_match_gw[(h_tid, gw_idx)] = (match_id, 'home')
        team_match_gw[(a_tid, gw_idx)] = (match_id, 'away')
        match_id += 1

emit('-- ----------------------------------------------------------------')
emit('-- MATCH (380 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO MATCH (match_id,home_score,away_score,match_date,home_team_id,away_team_id,gameweek_id,status_id) VALUES')
emit(',\n'.join(match_rows) + ';')
emit()

# ---------------------------------------------------------------
# FANTASY_LEAGUE (500 rows)
# ---------------------------------------------------------------
print("  Generating FANTASY_LEAGUE (500 rows)...")
fl_rows = []
for lid in range(1, NUM_FANTASY_LEAGUES + 1):
    name  = f"{random.choice(LG_ADJ)} {random.choice(LG_NOUN)} {lid}"
    desc  = f"Season 2023/24 fantasy competition #{lid}"
    maxt  = random.choice([8,10,12,16,20])
    budget= round(random.choice([100.0,100.0,100.0,105.0,110.0]), 1)
    s_dt  = datetime.date(2023, 8, 1)
    e_dt  = datetime.date(2024, 5, 31)
    cby   = random.randint(1, NUM_USERS)
    fl_rows.append(f"({lid},{q(name)},{q(desc)},{maxt},{budget},{q(str(s_dt))},{q(str(e_dt))},{cby})")

emit('-- ----------------------------------------------------------------')
emit('-- FANTASY_LEAGUE (500 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO FANTASY_LEAGUE (league_id,league_name,description,max_teams,budget_limit,start_date,end_date,created_by) VALUES')
emit(',\n'.join(fl_rows) + ';')
emit()

# ---------------------------------------------------------------
# FANTASY_TEAM (500 rows)
# ---------------------------------------------------------------
print("  Generating FANTASY_TEAM (500 rows)...")
ft_rows     = []
team_league = {}       # team_id -> league_id
league_teams = {}      # league_id -> [team_ids]

for tid in range(1, NUM_FANTASY_TEAMS + 1):
    uid   = random.randint(1, NUM_USERS)
    lid   = random.randint(1, NUM_FANTASY_LEAGUES)
    tname = f"{random.choice(FIRST_NAMES)} FC {tid}"
    form  = random.choice(FORMATIONS)
    tpts  = random.randint(0, 2000)
    budg  = round(random.uniform(0.5, 99.9), 1)
    ft_rows.append(f"({tid},{q(tname)},{q(form)},{tpts},{budg},{uid},{lid})")
    team_league[tid] = lid
    league_teams.setdefault(lid, []).append(tid)

emit('-- ----------------------------------------------------------------')
emit('-- FANTASY_TEAM (500 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO FANTASY_TEAM (team_id,team_name,formation,total_points,budget_remaining,user_id,league_id) VALUES')
emit(',\n'.join(ft_rows) + ';')
emit()

# ---------------------------------------------------------------
# PLAYER_GAMEWEEK_STATS  (600 players × 38 GWs = 22,800 rows)
# ---------------------------------------------------------------
print("  Generating PLAYER_GAMEWEEK_STATS (22,800 rows)...")
stat_id   = 1
stat_rows = []

for gw_idx in range(38):
    gw_id = gw_idx + 1
    done  = gw_idx < 32

    for (pid, tid, pos_id, price) in players:
        key = (tid, gw_idx)
        if key not in team_match_gw:
            continue
        mid, side = team_match_gw[key]

        if done:
            played  = random.random() < 0.82
            minutes = random.randint(60, 90) if played else random.randint(0, 25)
            if minutes > 0:
                if pos_id == 4:    # FWD
                    goals   = random.choices([0,1,2,3], weights=[70,20,8,2])[0]
                    assists = random.choices([0,1,2],   weights=[75,20,5])[0]
                    saves   = 0
                elif pos_id == 3:  # MID
                    goals   = random.choices([0,1,2],   weights=[75,20,5])[0]
                    assists = random.choices([0,1,2],   weights=[65,25,10])[0]
                    saves   = 0
                elif pos_id == 2:  # DEF
                    goals   = random.choices([0,1],     weights=[92,8])[0]
                    assists = random.choices([0,1],     weights=[85,15])[0]
                    saves   = 0
                else:              # GK
                    goals   = 0
                    assists = random.choices([0,1], weights=[90,10])[0]
                    saves   = random.randint(0, 8)

                # Clean sheet from actual result
                clean = 0
                if mid in match_results:
                    h_sc, a_sc, h_tid, a_tid = match_results[mid]
                    opp_goals = a_sc if side == 'home' else h_sc
                    clean = 1 if opp_goals == 0 else 0

                yellow = random.choices([0,1,2], weights=[85,13,2])[0]
                red    = random.choices([0,1],   weights=[97,3])[0]
                if red:
                    yellow = min(yellow, 1)
                bonus  = random.choices([0,1,2,3], weights=[60,20,12,8])[0]
                total_pts = calc_points(pos_id, minutes, goals, assists, clean, yellow, red, saves, bonus)
            else:
                goals = assists = saves = clean = yellow = red = bonus = total_pts = 0
        else:
            # Future GWs: zeroed out
            minutes = goals = assists = saves = clean = yellow = red = bonus = total_pts = 0

        stat_rows.append(
            f"({stat_id},{minutes},{goals},{assists},{clean},{yellow},{red},"
            f"{saves},{bonus},{total_pts},{pid},{mid},{gw_id})"
        )
        stat_id += 1

emit('-- ----------------------------------------------------------------')
emit(f'-- PLAYER_GAMEWEEK_STATS ({stat_id-1} rows)')
emit('-- ----------------------------------------------------------------')

header = ('INSERT INTO PLAYER_GAMEWEEK_STATS '
          '(stat_id,minutes_played,goals_scored,assists,clean_sheet,'
          'yellow_cards,red_cards,saves,bonus_points,total_points,player_id,match_id,gameweek_id) VALUES')

for i in range(0, len(stat_rows), BATCH_SIZE):
    batch = stat_rows[i:i+BATCH_SIZE]
    emit(header)
    emit(',\n'.join(batch) + ';')
emit()

# ---------------------------------------------------------------
# FANTASY_TEAM_SELECTION  (500 teams × 3 GWs × 15 = 22,500 rows)
# ---------------------------------------------------------------
print("  Generating FANTASY_TEAM_SELECTION (22,500 rows)...")
sel_id   = 1
sel_rows = []

all_player_ids = list(range(1, 601))

for gw_num in range(1, SELECTION_GAMEWEEKS + 1):
    gw_id = gw_num
    for tid in range(1, NUM_FANTASY_TEAMS + 1):
        sel_players = random.sample(all_player_ids, 15)
        for slot, pid in enumerate(sel_players):
            is_cap  = 1 if slot == 0 else 0
            is_vc   = 1 if slot == 1 else 0
            on_bench= 1 if slot >= 11 else 0
            b_order = str(slot - 10) if slot >= 11 else 'NULL'
            pts     = random.randint(0, 20)
            sel_rows.append(
                f"({sel_id},{is_cap},{is_vc},{on_bench},{b_order},{pts},{tid},{pid},{gw_id})"
            )
            sel_id += 1

emit('-- ----------------------------------------------------------------')
emit(f'-- FANTASY_TEAM_SELECTION ({sel_id-1} rows)')
emit('-- ----------------------------------------------------------------')
header_sel = ('INSERT INTO FANTASY_TEAM_SELECTION '
              '(selection_id,is_captain,is_vice_captain,is_on_bench,bench_order,'
              'points_scored,team_id,player_id,gameweek_id) VALUES')

for i in range(0, len(sel_rows), BATCH_SIZE):
    batch = sel_rows[i:i+BATCH_SIZE]
    emit(header_sel)
    emit(',\n'.join(batch) + ';')
emit()

# ---------------------------------------------------------------
# TRANSFER (1,000 rows)
# ---------------------------------------------------------------
print("  Generating TRANSFER (1,000 rows)...")
tr_rows = []
for tr_id in range(1, NUM_TRANSFERS + 1):
    ftid  = random.randint(1, NUM_FANTASY_TEAMS)
    gw_id = random.randint(2, 38)
    p_out = random.randint(1, 600)
    p_in  = random.randint(1, 600)
    while p_in == p_out:
        p_in = random.randint(1, 600)
    price     = round(player_map[p_in][3], 1)
    tr_date   = gameweeks[gw_id-1][1] - datetime.timedelta(days=random.randint(1, 4))
    tr_rows.append(f"({tr_id},{price},{q(str(tr_date))},{ftid},{p_out},{p_in},{gw_id})")

emit('-- ----------------------------------------------------------------')
emit('-- TRANSFER (1,000 rows)')
emit('-- ----------------------------------------------------------------')
emit('INSERT INTO TRANSFER (transfer_id,price_paid,transfer_date,team_id,player_out_id,player_in_id,gameweek_id) VALUES')
emit(',\n'.join(tr_rows) + ';')
emit()

# ---------------------------------------------------------------
# LEAGUE_STANDING (500 teams × 5 GWs = ~2,500 rows, exact depends on league membership)
# ---------------------------------------------------------------
print("  Generating LEAGUE_STANDING (~2,500 rows)...")
ls_rows = []
ls_id   = 1
cum_pts = {tid: 0 for tid in range(1, NUM_FANTASY_TEAMS + 1)}

for gw_num in range(1, STANDING_GAMEWEEKS + 1):
    gw_id = gw_num
    # update cumulative points
    for tid in range(1, NUM_FANTASY_TEAMS + 1):
        cum_pts[tid] += random.randint(20, 100)

    for lid, team_list in league_teams.items():
        if not team_list:
            continue
        ranked = sorted(team_list, key=lambda t: cum_pts[t], reverse=True)
        for rank, tid in enumerate(ranked, start=1):
            ls_rows.append(f"({ls_id},{cum_pts[tid]},{rank},{lid},{tid},{gw_id})")
            ls_id += 1

emit('-- ----------------------------------------------------------------')
emit(f'-- LEAGUE_STANDING ({ls_id-1} rows)')
emit('-- ----------------------------------------------------------------')
header_ls = 'INSERT INTO LEAGUE_STANDING (standing_id,points,rank,league_id,team_id,gameweek_id) VALUES'
for i in range(0, len(ls_rows), BATCH_SIZE):
    batch = ls_rows[i:i+BATCH_SIZE]
    emit(header_ls)
    emit(',\n'.join(batch) + ';')
emit()

emit('-- ================================================================')
emit('-- Summary of generated rows:')
emit(f'--   REAL_TEAM              : 20')
emit(f'--   PLAYER                 : 600')
emit(f'--   USERS                  : {NUM_USERS}')
emit(f'--   GAMEWEEK               : 38')
emit(f'--   MATCH                  : 380')
emit(f'--   FANTASY_LEAGUE         : {NUM_FANTASY_LEAGUES}')
emit(f'--   FANTASY_TEAM           : {NUM_FANTASY_TEAMS}')
emit(f'--   PLAYER_GAMEWEEK_STATS  : {stat_id-1}  ← exceeds 20,000 ✓')
emit(f'--   FANTASY_TEAM_SELECTION : {sel_id-1}  ← exceeds 20,000 ✓')
emit(f'--   TRANSFER               : {NUM_TRANSFERS}')
emit(f'--   LEAGUE_STANDING        : {ls_id-1}')
emit('-- ================================================================')

# ============================================================
# Write SQL output
# ============================================================
with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
    f.write('\n'.join(all_lines))
print(f"  ✓ Written {OUTPUT_SQL}  ({len(all_lines):,} lines)")

# ============================================================
# Write CSV for Method 3 (USERS)
# ============================================================
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['user_id','username','email','password_hash','country',
                     'registration_date','birth_date'])
    for row in users_data:
        writer.writerow(row)
print(f"  ✓ Written {OUTPUT_CSV}  ({len(users_data):,} rows)")
print("Done!")
