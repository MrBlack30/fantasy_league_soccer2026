-- ============================================================
-- Fantasy Soccer League Database
-- File: createTables.sql
-- Description: Creates all tables with constraints and indexes
-- ============================================================
-- DATABASE DICTIONARY:
--   POSITION        - Lookup: player positions (GK, DEF, MID, FWD)
--   MATCH_STATUS    - Lookup: match states (Scheduled, Live, Finished, ...)
--   USERS           - Registered platform users / fantasy managers
--   REAL_TEAM       - Real-world soccer clubs
--   PLAYER          - Real-world players eligible for fantasy selection
--   FANTASY_LEAGUE  - User-created fantasy competitions
--   FANTASY_TEAM    - A user's squad within a fantasy league
--   GAMEWEEK        - A round of real-world fixtures
--   MATCH           - A real-world match between two clubs
--   PLAYER_GAMEWEEK_STATS - Per-match performance statistics
--   FANTASY_TEAM_SELECTION - 15-player squad chosen per gameweek
--   TRANSFER        - Player swap made by a fantasy team
--   LEAGUE_STANDING - Weekly ranking snapshot within a league
-- ============================================================


-- ============================================================
-- ENUM / LOOKUP TABLES
-- ============================================================

-- POSITION: The 4 playing positions in soccer fantasy games.
-- Fields:
--   position_id   INT          - Primary key
--   position_name VARCHAR(20)  - Full name: Goalkeeper, Defender, Midfielder, Forward
--   short_name    VARCHAR(3)   - Abbreviation: GKP, DEF, MID, FWD
CREATE TABLE POSITION (
    position_id     INT             PRIMARY KEY,
    position_name   VARCHAR(20)     NOT NULL UNIQUE,
    short_name      VARCHAR(3)      NOT NULL UNIQUE
);

-- MATCH_STATUS: Possible lifecycle states for a soccer match.
-- Fields:
--   status_id    INT         - Primary key
--   status_name  VARCHAR(20) - Label: Scheduled, Live, Finished, Postponed, Cancelled
CREATE TABLE MATCH_STATUS (
    status_id       INT             PRIMARY KEY,
    status_name     VARCHAR(20)     NOT NULL UNIQUE
);


-- ============================================================
-- CORE ENTITY TABLES
-- ============================================================

-- USERS: Platform accounts that manage one or more fantasy teams.
-- Fields:
--   user_id           INT          - Primary key
--   username          VARCHAR(50)  - Unique display name chosen at registration
--   email             VARCHAR(100) - Unique email used for login
--   password_hash     VARCHAR(255) - Bcrypt/SHA256 hashed password (never plaintext)
--   country           VARCHAR(50)  - User's country of residence
--   registration_date DATE         - Date the account was created [DATE - meaningful]
--   birth_date        DATE         - User's date of birth, used for age verification [DATE - meaningful]
-- Constraints:
--   birth_date must be before registration_date (user must exist before registering)
CREATE TABLE USERS (
    user_id             INT             PRIMARY KEY,
    username            VARCHAR(50)     NOT NULL UNIQUE,
    email               VARCHAR(100)    NOT NULL UNIQUE,
    password_hash       VARCHAR(255)    NOT NULL,
    country             VARCHAR(50),
    registration_date   DATE            NOT NULL,
    birth_date          DATE,
    CHECK (birth_date < registration_date)
);

-- REAL_TEAM: Real-world soccer clubs tracked in the system.
-- Fields:
--   real_team_id  INT          - Primary key
--   team_name     VARCHAR(100) - Full official club name (unique)
--   short_name    VARCHAR(5)   - 3-5 letter abbreviation (e.g., ARS, MCI)
--   stadium       VARCHAR(100) - Name of the home ground
--   city          VARCHAR(50)  - City where the club is based
--   country       VARCHAR(50)  - Country the club competes in
--   founded_year  INT          - Year the club was established
-- Constraints:
--   founded_year must be after 1800 and no later than 2024
CREATE TABLE REAL_TEAM (
    real_team_id    INT             PRIMARY KEY,
    team_name       VARCHAR(100)    NOT NULL UNIQUE,
    short_name      VARCHAR(5)      NOT NULL,
    stadium         VARCHAR(100),
    city            VARCHAR(50),
    country         VARCHAR(50)     NOT NULL,
    founded_year    INT             CHECK (founded_year > 1800 AND founded_year <= 2024)
);

-- PLAYER: Real-world soccer players eligible for fantasy selection.
-- Fields:
--   player_id            INT          - Primary key
--   first_name           VARCHAR(50)  - Player's first name
--   last_name            VARCHAR(50)  - Player's surname
--   nationality          VARCHAR(50)  - Country the player represents internationally
--   price                NUMERIC(5,1) - Current fantasy price (e.g., 8.5 = £8.5m)
--   total_points         INT          - Cumulative fantasy points this season
--   selected_by_percent  NUMERIC(5,2) - Percentage of managers who own this player
--   birth_date           DATE         - Player's date of birth [DATE - meaningful, used for age calc]
--   contract_start_date  DATE         - Date player signed current club contract [DATE - meaningful]
--   real_team_id         INT          - FK to REAL_TEAM: current club
--   position_id          INT          - FK to POSITION: playing position
-- Constraints:
--   price must be between 0 and 20 (fantasy price bands)
--   selected_by_percent between 0 and 100
CREATE TABLE PLAYER (
    player_id               INT             PRIMARY KEY,
    first_name              VARCHAR(50)     NOT NULL,
    last_name               VARCHAR(50)     NOT NULL,
    nationality             VARCHAR(50),
    price                   NUMERIC(5,1)    NOT NULL CHECK (price > 0 AND price <= 20),
    total_points            INT             DEFAULT 0,
    selected_by_percent     NUMERIC(5,2)    CHECK (selected_by_percent >= 0 AND selected_by_percent <= 100),
    birth_date              DATE,
    contract_start_date     DATE,
    real_team_id            INT             NOT NULL REFERENCES REAL_TEAM(real_team_id),
    position_id             INT             NOT NULL REFERENCES POSITION(position_id)
);

-- FANTASY_LEAGUE: A competition created by a user for fantasy teams to compete in.
-- Fields:
--   league_id    INT          - Primary key
--   league_name  VARCHAR(100) - Display name for the league
--   description  VARCHAR(500) - Optional rules or description
--   max_teams    INT          - Maximum number of teams allowed (1-200)
--   budget_limit NUMERIC(6,1) - Starting transfer budget (in fantasy currency units)
--   start_date   DATE         - Date the season begins [DATE - meaningful]
--   end_date     DATE         - Date the season ends [DATE - meaningful]
--   created_by   INT          - FK to USERS: the user who created this league
-- Constraints:
--   end_date must be after start_date
--   max_teams between 1 and 200
CREATE TABLE FANTASY_LEAGUE (
    league_id       INT             PRIMARY KEY,
    league_name     VARCHAR(100)    NOT NULL,
    description     VARCHAR(500),
    max_teams       INT             NOT NULL CHECK (max_teams > 0 AND max_teams <= 200),
    budget_limit    NUMERIC(6,1)    NOT NULL CHECK (budget_limit > 0),
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    created_by      INT             NOT NULL REFERENCES USERS(user_id),
    CHECK (end_date > start_date)
);

-- FANTASY_TEAM: A user's squad competing within a specific fantasy league.
-- Fields:
--   team_id          INT          - Primary key
--   team_name        VARCHAR(100) - User-chosen team name
--   formation        VARCHAR(10)  - Tactical formation e.g. 4-3-3, 3-5-2
--   total_points     INT          - Cumulative points earned across all gameweeks
--   budget_remaining NUMERIC(6,1) - Remaining transfer budget
--   user_id          INT          - FK to USERS: the manager
--   league_id        INT          - FK to FANTASY_LEAGUE: the competition
-- Constraints:
--   budget_remaining >= 0 (cannot spend more than available)
CREATE TABLE FANTASY_TEAM (
    team_id             INT             PRIMARY KEY,
    team_name           VARCHAR(100)    NOT NULL,
    formation           VARCHAR(10),
    total_points        INT             DEFAULT 0,
    budget_remaining    NUMERIC(6,1)    CHECK (budget_remaining >= 0),
    user_id             INT             NOT NULL REFERENCES USERS(user_id),
    league_id           INT             NOT NULL REFERENCES FANTASY_LEAGUE(league_id)
);

-- GAMEWEEK: A scheduled round of real-world matches within a season.
-- Fields:
--   gameweek_id      INT  - Primary key
--   season_year      INT  - The starting year of the season (e.g., 2023 for 2023/24)
--   gameweek_number  INT  - The round number within the season (1-38)
--   start_date       DATE - First day of this gameweek window [DATE - meaningful]
--   end_date         DATE - Last day of this gameweek window [DATE - meaningful]
--   is_finished      INT  - 1 if all matches in this GW are complete, 0 otherwise
-- Constraints:
--   gameweek_number must be 1-38 (Premier League season length)
--   end_date must be after start_date
--   (season_year, gameweek_number) must be unique
CREATE TABLE GAMEWEEK (
    gameweek_id         INT             PRIMARY KEY,
    season_year         INT             NOT NULL,
    gameweek_number     INT             NOT NULL CHECK (gameweek_number >= 1 AND gameweek_number <= 38),
    start_date          DATE            NOT NULL,
    end_date            DATE            NOT NULL,
    is_finished         INT             DEFAULT 0 CHECK (is_finished IN (0, 1)),
    CHECK (end_date > start_date),
    UNIQUE (season_year, gameweek_number)
);

-- MATCH: A real-world soccer match between two clubs in a gameweek.
-- Fields:
--   match_id      INT  - Primary key
--   home_score    INT  - Goals scored by the home team (NULL if not played yet)
--   away_score    INT  - Goals scored by the away team (NULL if not played yet)
--   match_date    DATE - Date the match is played [DATE - meaningful]
--   home_team_id  INT  - FK to REAL_TEAM: the home club
--   away_team_id  INT  - FK to REAL_TEAM: the away club
--   gameweek_id   INT  - FK to GAMEWEEK: which round this match belongs to
--   status_id     INT  - FK to MATCH_STATUS: current state
-- Constraints:
--   home_score and away_score >= 0
--   home_team_id != away_team_id (a team cannot play itself)
CREATE TABLE MATCH (
    match_id        INT             PRIMARY KEY,
    home_score      INT             CHECK (home_score >= 0),
    away_score      INT             CHECK (away_score >= 0),
    match_date      DATE            NOT NULL,
    home_team_id    INT             NOT NULL REFERENCES REAL_TEAM(real_team_id),
    away_team_id    INT             NOT NULL REFERENCES REAL_TEAM(real_team_id),
    gameweek_id     INT             NOT NULL REFERENCES GAMEWEEK(gameweek_id),
    status_id       INT             NOT NULL REFERENCES MATCH_STATUS(status_id),
    CHECK (home_team_id != away_team_id)
);

-- PLAYER_GAMEWEEK_STATS: Per-match performance stats for a real-world player.
-- This is a HIGH-VOLUME table (600 players × 38 GWs = 22,800+ rows).
-- Fields:
--   stat_id        INT  - Primary key
--   minutes_played INT  - Minutes on the pitch (0-120 including extra time)
--   goals_scored   INT  - Goals scored in this match
--   assists        INT  - Goal assists in this match
--   clean_sheet    INT  - 1 if player's team kept a clean sheet, 0 otherwise
--   yellow_cards   INT  - Yellow cards received (0-2)
--   red_cards      INT  - Red card received (0/1)
--   saves          INT  - Saves made (for goalkeepers)
--   bonus_points   INT  - BPS bonus awarded (0-3)
--   total_points   INT  - Calculated fantasy points for this appearance
--   player_id      INT  - FK to PLAYER
--   match_id       INT  - FK to MATCH
--   gameweek_id    INT  - FK to GAMEWEEK
-- Constraints:
--   minutes_played 0-120; yellow_cards 0-2; red_cards 0/1; bonus 0-3
--   (player_id, match_id) must be unique — one stat row per player per match
CREATE TABLE PLAYER_GAMEWEEK_STATS (
    stat_id         INT             PRIMARY KEY,
    minutes_played  INT             DEFAULT 0 CHECK (minutes_played >= 0 AND minutes_played <= 120),
    goals_scored    INT             DEFAULT 0 CHECK (goals_scored >= 0),
    assists         INT             DEFAULT 0 CHECK (assists >= 0),
    clean_sheet     INT             DEFAULT 0 CHECK (clean_sheet IN (0, 1)),
    yellow_cards    INT             DEFAULT 0 CHECK (yellow_cards >= 0 AND yellow_cards <= 2),
    red_cards       INT             DEFAULT 0 CHECK (red_cards IN (0, 1)),
    saves           INT             DEFAULT 0 CHECK (saves >= 0),
    bonus_points    INT             DEFAULT 0 CHECK (bonus_points >= 0 AND bonus_points <= 3),
    total_points    INT             DEFAULT 0,
    player_id       INT             NOT NULL REFERENCES PLAYER(player_id),
    match_id        INT             NOT NULL REFERENCES MATCH(match_id),
    gameweek_id     INT             NOT NULL REFERENCES GAMEWEEK(gameweek_id),
    UNIQUE (player_id, match_id)
);

-- FANTASY_TEAM_SELECTION: The 15-player squad chosen by a fantasy team for a gameweek.
-- This is a HIGH-VOLUME table (500 teams × 3 GWs × 15 = 22,500+ rows).
-- Fields:
--   selection_id    INT - Primary key
--   is_captain      INT - 1 if this player is captain (points doubled), else 0
--   is_vice_captain INT - 1 if this player is vice-captain, else 0
--   is_on_bench     INT - 1 if player starts on the bench (slots 12-15), else 0
--   bench_order     INT - Bench priority 1-4 (NULL if in starting XI)
--   points_scored   INT - Fantasy points this player earned for this team this GW
--   team_id         INT - FK to FANTASY_TEAM
--   player_id       INT - FK to PLAYER
--   gameweek_id     INT - FK to GAMEWEEK
-- Constraints:
--   is_captain, is_vice_captain, is_on_bench are 0 or 1 flags
--   bench_order must be 1-4 or NULL
--   (team_id, player_id, gameweek_id) must be unique
CREATE TABLE FANTASY_TEAM_SELECTION (
    selection_id        INT             PRIMARY KEY,
    is_captain          INT             DEFAULT 0 CHECK (is_captain IN (0, 1)),
    is_vice_captain     INT             DEFAULT 0 CHECK (is_vice_captain IN (0, 1)),
    is_on_bench         INT             DEFAULT 0 CHECK (is_on_bench IN (0, 1)),
    bench_order         INT             CHECK (bench_order IS NULL OR (bench_order >= 1 AND bench_order <= 4)),
    points_scored       INT             DEFAULT 0,
    team_id             INT             NOT NULL REFERENCES FANTASY_TEAM(team_id),
    player_id           INT             NOT NULL REFERENCES PLAYER(player_id),
    gameweek_id         INT             NOT NULL REFERENCES GAMEWEEK(gameweek_id),
    UNIQUE (team_id, player_id, gameweek_id)
);

-- TRANSFER: A player swap executed by a fantasy team between gameweeks.
-- Fields:
--   transfer_id   INT          - Primary key
--   price_paid    NUMERIC(5,1) - Fantasy price paid to buy the incoming player
--   transfer_date DATE         - Date the transfer was confirmed [DATE - meaningful]
--   team_id       INT          - FK to FANTASY_TEAM: the team making the change
--   player_out_id INT          - FK to PLAYER: the player being sold/removed
--   player_in_id  INT          - FK to PLAYER: the player being bought/added
--   gameweek_id   INT          - FK to GAMEWEEK: the gameweek this takes effect from
-- Constraints:
--   price_paid > 0 (must cost something)
--   player_out_id != player_in_id (cannot transfer same player in and out)
CREATE TABLE TRANSFER (
    transfer_id     INT             PRIMARY KEY,
    price_paid      NUMERIC(5,1)    NOT NULL CHECK (price_paid > 0),
    transfer_date   DATE            NOT NULL,
    team_id         INT             NOT NULL REFERENCES FANTASY_TEAM(team_id),
    player_out_id   INT             NOT NULL REFERENCES PLAYER(player_id),
    player_in_id    INT             NOT NULL REFERENCES PLAYER(player_id),
    gameweek_id     INT             NOT NULL REFERENCES GAMEWEEK(gameweek_id),
    CHECK (player_out_id != player_in_id)
);

-- LEAGUE_STANDING: Weekly snapshot of team rankings within a fantasy league.
-- Fields:
--   standing_id  INT - Primary key
--   points       INT - Cumulative fantasy points at the time of this snapshot
--   rank         INT - Team's rank within the league at this gameweek
--   league_id    INT - FK to FANTASY_LEAGUE
--   team_id      INT - FK to FANTASY_TEAM
--   gameweek_id  INT - FK to GAMEWEEK
-- Constraints:
--   points >= 0; rank >= 1
--   (league_id, team_id, gameweek_id) must be unique — one snapshot per team per GW
CREATE TABLE LEAGUE_STANDING (
    standing_id     INT             PRIMARY KEY,
    points          INT             DEFAULT 0 CHECK (points >= 0),
    rank            INT             NOT NULL CHECK (rank > 0),
    league_id       INT             NOT NULL REFERENCES FANTASY_LEAGUE(league_id),
    team_id         INT             NOT NULL REFERENCES FANTASY_TEAM(team_id),
    gameweek_id     INT             NOT NULL REFERENCES GAMEWEEK(gameweek_id),
    UNIQUE (league_id, team_id, gameweek_id)
);
