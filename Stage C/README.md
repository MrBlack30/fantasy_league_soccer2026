# Phase C — Database Integration

**Submitters:** Ariel Zourno, Ariel Namir, Uria Shahor

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Two Systems](#the-two-systems)
3. [DSD — Received System (FIFA World Cup)](#dsd--received-system-fifa-world-cup)
4. [ERD — Received System (Reverse Engineered)](#erd--received-system-reverse-engineered)
5. [Reverse Engineering Algorithm](#reverse-engineering-algorithm)
6. [Integration Decisions](#integration-decisions)
7. [Combined ERD](#combined-erd)
8. [Combined DSD](#combined-dsd)
9. [Integration Process — Integrate.sql](#integration-process--integratesql)
10. [Views and Queries — Views.sql](#views-and-queries--viewssql)

---

## Introduction

In this phase we received a database backup from another group and merged it with our own Fantasy Football (Premier League) database into a single unified schema. The integration was performed using **Method A**: all tables from the received system were added to our existing database using `CREATE TABLE` commands, conflicting table names were resolved by renaming, and an `ALTER TABLE` command was used to add a foreign-key link between the two systems. No data was lost and all Phase B queries continue to run without modification on the merged database.

---

## The Two Systems

| System | Domain | Tables |
|--------|--------|--------|
| **Ours** | Premier League Fantasy Football | 13 tables — users, real teams, players, matches, gameweeks, fantasy leagues, fantasy teams, selections, standings, transfers, positions, player stats, match statuses |
| **Received (RL)** | FIFA World Cup (1970–2018) | 8 tables — persons, national teams, stadiums, referees, players, matches, match events, player match stats |

The natural integration bridge between the two systems is the **player**: a footballer who plays for a Premier League club may also have appeared in World Cup data. This connection is captured by a new `person_id` foreign key added to our `player` table, pointing to the `person` table from the received system.

---

## DSD — Received System (FIFA World Cup)

> **Screenshot this Mermaid diagram and save as `images/dsd_rl.png`**

```mermaid
erDiagram
    PERSON {
        varchar id PK
        text familyname
        text givenname
        text wikipediapage
    }
    TEAM {
        varchar teamcode PK
        text countryname
        text confederationname
        varchar confederationcode
        text wikipediapage
    }
    STADIUM {
        varchar stadiumid PK
        text city
        text name
        int capacity
        text country
        text wikipediapage
    }
    REFEREE {
        varchar id PK
        text country
        varchar confederationcode
        text confederationname
    }
    PLAYER {
        varchar id PK
        date dateofbirth
        varchar teamcode FK
    }
    MATCH {
        varchar matchid PK
        date matchdate
        text stage
        text tournament
        time matchtime
        varchar stadiumid FK
        varchar hometeamcode FK
        varchar guestteamcode FK
        varchar refereeid FK
    }
    MATCH_EVENT {
        varchar matcheventid PK
        text minute
        text eventtype
        varchar matchid FK
        varchar id FK
    }
    PLAYER_MATCH_STATS {
        varchar matchid PK
        varchar playerid PK
        text position
        int shirtnumber
    }

    PERSON ||--o| REFEREE : "is-a"
    PERSON ||--o| PLAYER : "is-a"
    TEAM ||--o{ PLAYER : "belongs to"
    STADIUM ||--o{ MATCH : "hosted at"
    TEAM ||--o{ MATCH : "home team"
    TEAM ||--o{ MATCH : "guest team"
    REFEREE ||--o{ MATCH : "officiated by"
    MATCH ||--o{ MATCH_EVENT : "contains"
    PLAYER ||--o{ MATCH_EVENT : "performs"
    MATCH ||--o{ PLAYER_MATCH_STATS : "records"
    PLAYER ||--o{ PLAYER_MATCH_STATS : "appears in"
```

---

## ERD — Received System (Reverse Engineered)

> **Screenshot this Mermaid diagram and save as `images/erd_rl.png`**

```mermaid
erDiagram
    PERSON {
        varchar id PK
        text familyname
        text givenname
        text wikipediapage
    }
    PLAYER {
        date dateofbirth
    }
    REFEREE {
        text country
        text confederationname
        varchar confederationcode
    }
    TEAM {
        varchar teamcode PK
        text countryname
        text confederationname
        varchar confederationcode
    }
    STADIUM {
        varchar stadiumid PK
        text city
        text name
        int capacity
        text country
    }
    MATCH {
        varchar matchid PK
        date matchdate
        text stage
        text tournament
        time matchtime
    }
    MATCH_EVENT {
        varchar matcheventid PK
        text minute
        text eventtype
    }
    PLAYER_MATCH_STATS {
        text position
        int shirtnumber
    }

    PERSON ||--|| PLAYER : "is-a"
    PERSON ||--|| REFEREE : "is-a"
    PLAYER }o--o| TEAM : "represents"
    MATCH }o--|| STADIUM : "played at"
    MATCH }o--|| REFEREE : "officiated by"
    MATCH }o--|| TEAM : "home"
    MATCH }o--|| TEAM : "guest"
    MATCH ||--o{ MATCH_EVENT : "contains"
    PLAYER ||--o{ MATCH_EVENT : "performs"
    MATCH ||--o{ PLAYER_MATCH_STATS : "records"
    PLAYER ||--o{ PLAYER_MATCH_STATS : "in"
```

---

## Reverse Engineering Algorithm

The ERD above was derived from the received database tables using the following process:

1. **Each table with a single primary key becomes an entity.** `person`, `team`, `stadium`, `match`, and `match_event` each have one PK and became independent entities.

2. **A table whose PK is also a FK to another table represents an ISA (subtype) relationship.** `player.id` is both a PK and a FK referencing `person.id`. Same for `referee.id`. These became subtype entities of `PERSON`.

3. **A table whose PK is a composite of two FKs represents a many-to-many relationship.** `player_match_stats` has a composite PK `(matchid, playerid)`, both of which are FKs. This became a relationship entity (associative entity) between `MATCH` and `PLAYER`.

4. **FK columns that are not part of the PK represent many-to-one relationships.** For example, `player.teamcode` is a FK to `team` but not part of the player's PK — a player belongs to one national team, a team has many players.

5. **Duplicate FK columns pointing to the same table represent distinct roles.** `match.hometeamcode` and `match.guestteamcode` both reference `team`, so `MATCH` has two separate relationships with `TEAM` — one for each role.

6. **Non-key columns that describe a concept from another domain were kept as attributes**, not promoted to new entities, because they are not referenced by any FK (e.g., `stage`, `tournament` in `match`).

---

## Integration Decisions

| Decision | Reasoning |
|----------|-----------|
| Rename `team` → `intl_team` | Both systems have a "team" concept: ours are Premier League clubs, theirs are national teams. Renaming makes the distinction explicit and avoids a name collision. |
| Rename `player` → `intl_player` | Same collision issue. A club player (our `player`) and a World Cup player (their `player`) represent the same real-world person but are modelled differently; a rename preserves both without confusion. |
| Rename `match` → `intl_match` | Our `match` holds Premier League fixtures; their `match` holds World Cup fixtures. The schemas are incompatible (ours has scores and a status; theirs has a tournament, stage, stadium, and referee), so merging them into one table was not appropriate. |
| Rename `player_match_stats` → `intl_player_match_stats` | Follows from renaming `match` and `player`. |
| Keep `person`, `stadium`, `referee`, `match_event` as-is | No name collisions and the entities are distinct enough to stand alone. |
| Add `person_id VARCHAR(50)` to our `player` table | This is the integration link: a Premier League player who also played in World Cup data can be identified as the same person. The column is nullable because most club players in the fantasy dataset are fictional/generated and have no corresponding World Cup record. |
| No FK from `real_team` to `intl_team` | Premier League clubs and national football teams are fundamentally different entities with no direct parent–child relationship. Forcing a FK here would be semantically wrong. |
| No structural merge of `match` and `intl_match` | The two match tables have different mandatory columns and serve completely different query patterns. Merging them into one table with many nullable columns would violate 1NF intent and make every query more complex. |

---

## Combined ERD

> **Screenshot this Mermaid diagram and save as `images/erd_combined.png`**

```mermaid
erDiagram
    USERS {
        int user_id PK
        varchar username
        varchar email
        varchar password_hash
        varchar country
        date registration_date
        date birth_date
    }
    REAL_TEAM {
        int real_team_id PK
        varchar team_name
        varchar short_name
        varchar stadium
        varchar city
        varchar country
        int founded_year
    }
    POSITION {
        int position_id PK
        varchar position_name
        varchar short_name
    }
    PLAYER {
        int player_id PK
        varchar first_name
        varchar last_name
        varchar nationality
        numeric price
        int total_points
        numeric selected_by_percent
        date birth_date
        date contract_start_date
        varchar person_id FK
    }
    GAMEWEEK {
        int gameweek_id PK
        int season_year
        int gameweek_number
        date start_date
        date end_date
        int is_finished
    }
    MATCH {
        int match_id PK
        date match_date
        int home_score
        int away_score
    }
    MATCH_STATUS {
        int status_id PK
        varchar status_name
    }
    PLAYER_GAMEWEEK_STATS {
        int stat_id PK
        int minutes_played
        int goals_scored
        int assists
        int clean_sheet
        int yellow_cards
        int red_cards
        int saves
        int bonus_points
        int total_points
    }
    FANTASY_LEAGUE {
        int league_id PK
        varchar league_name
        varchar description
        int max_teams
        numeric budget_limit
        date start_date
        date end_date
    }
    FANTASY_TEAM {
        int team_id PK
        varchar team_name
        varchar formation
        int total_points
        numeric budget_remaining
    }
    FANTASY_TEAM_SELECTION {
        int selection_id PK
        int is_captain
        int is_vice_captain
        int is_on_bench
        int bench_order
        int points_scored
    }
    LEAGUE_STANDING {
        int standing_id PK
        int points
        int rank
    }
    TRANSFER {
        int transfer_id PK
        numeric price_paid
        date transfer_date
    }
    PERSON {
        varchar id PK
        text familyname
        text givenname
        text wikipediapage
    }
    INTL_TEAM {
        varchar teamcode PK
        text countryname
        text confederationname
        varchar confederationcode
    }
    STADIUM {
        varchar stadiumid PK
        text city
        text name
        int capacity
        text country
    }
    REFEREE {
        varchar id PK
        text country
        varchar confederationcode
        text confederationname
    }
    INTL_PLAYER {
        varchar id PK
        date dateofbirth
        varchar teamcode FK
    }
    INTL_MATCH {
        varchar matchid PK
        date matchdate
        text stage
        text tournament
        time matchtime
    }
    MATCH_EVENT {
        varchar matcheventid PK
        text minute
        text eventtype
    }
    INTL_PLAYER_MATCH_STATS {
        varchar matchid PK
        varchar playerid PK
        text position
        int shirtnumber
    }

    USERS ||--o{ FANTASY_LEAGUE : "creates"
    USERS ||--o{ FANTASY_TEAM : "owns"
    REAL_TEAM ||--o{ PLAYER : "employs"
    POSITION ||--o{ PLAYER : "classifies"
    PLAYER ||--o{ FANTASY_TEAM_SELECTION : "selected in"
    PLAYER ||--o{ PLAYER_GAMEWEEK_STATS : "has stats"
    PLAYER ||--o{ TRANSFER : "transferred in"
    PLAYER ||--o{ TRANSFER : "transferred out"
    PLAYER }o--o| PERSON : "linked to"
    GAMEWEEK ||--o{ MATCH : "contains"
    GAMEWEEK ||--o{ FANTASY_TEAM_SELECTION : "in"
    GAMEWEEK ||--o{ PLAYER_GAMEWEEK_STATS : "during"
    GAMEWEEK ||--o{ LEAGUE_STANDING : "snapshot"
    GAMEWEEK ||--o{ TRANSFER : "made in"
    MATCH_STATUS ||--o{ MATCH : "status"
    REAL_TEAM ||--o{ MATCH : "home"
    REAL_TEAM ||--o{ MATCH : "away"
    MATCH ||--o{ PLAYER_GAMEWEEK_STATS : "in"
    FANTASY_LEAGUE ||--o{ FANTASY_TEAM : "contains"
    FANTASY_LEAGUE ||--o{ LEAGUE_STANDING : "tracks"
    FANTASY_TEAM ||--o{ FANTASY_TEAM_SELECTION : "has"
    FANTASY_TEAM ||--o{ LEAGUE_STANDING : "ranked in"
    FANTASY_TEAM ||--o{ TRANSFER : "makes"
    PERSON ||--o| REFEREE : "is-a"
    PERSON ||--o| INTL_PLAYER : "is-a"
    INTL_TEAM ||--o{ INTL_PLAYER : "represents"
    INTL_TEAM ||--o{ INTL_MATCH : "home"
    INTL_TEAM ||--o{ INTL_MATCH : "guest"
    STADIUM ||--o{ INTL_MATCH : "hosted at"
    REFEREE ||--o{ INTL_MATCH : "officiated by"
    INTL_MATCH ||--o{ MATCH_EVENT : "contains"
    INTL_PLAYER ||--o{ MATCH_EVENT : "performs"
    INTL_MATCH ||--o{ INTL_PLAYER_MATCH_STATS : "records"
    INTL_PLAYER ||--o{ INTL_PLAYER_MATCH_STATS : "in"
```

---

## Combined DSD

> **Screenshot this Mermaid diagram and save as `images/dsd_combined.png`**

```mermaid
erDiagram
    users {
        int user_id PK
        varchar username
        varchar email
        varchar password_hash
        varchar country
        date registration_date
        date birth_date
    }
    real_team {
        int real_team_id PK
        varchar team_name
        varchar short_name
        varchar stadium
        varchar city
        varchar country
        int founded_year
    }
    position {
        int position_id PK
        varchar position_name
        varchar short_name
    }
    player {
        int player_id PK
        varchar first_name
        varchar last_name
        varchar nationality
        numeric price
        int total_points
        numeric selected_by_percent
        date birth_date
        date contract_start_date
        int real_team_id FK
        int position_id FK
        varchar person_id FK
    }
    gameweek {
        int gameweek_id PK
        int season_year
        int gameweek_number
        date start_date
        date end_date
        int is_finished
    }
    match_status {
        int status_id PK
        varchar status_name
    }
    match {
        int match_id PK
        date match_date
        int home_score
        int away_score
        int home_team_id FK
        int away_team_id FK
        int gameweek_id FK
        int status_id FK
    }
    player_gameweek_stats {
        int stat_id PK
        int minutes_played
        int goals_scored
        int assists
        int clean_sheet
        int yellow_cards
        int red_cards
        int saves
        int bonus_points
        int total_points
        int player_id FK
        int match_id FK
        int gameweek_id FK
    }
    fantasy_league {
        int league_id PK
        varchar league_name
        varchar description
        int max_teams
        numeric budget_limit
        date start_date
        date end_date
        int created_by FK
    }
    fantasy_team {
        int team_id PK
        varchar team_name
        varchar formation
        int total_points
        numeric budget_remaining
        int user_id FK
        int league_id FK
    }
    fantasy_team_selection {
        int selection_id PK
        int is_captain
        int is_vice_captain
        int is_on_bench
        int bench_order
        int points_scored
        int team_id FK
        int player_id FK
        int gameweek_id FK
    }
    league_standing {
        int standing_id PK
        int points
        int rank
        int league_id FK
        int team_id FK
        int gameweek_id FK
    }
    transfer {
        int transfer_id PK
        numeric price_paid
        date transfer_date
        int team_id FK
        int player_out_id FK
        int player_in_id FK
        int gameweek_id FK
    }
    person {
        varchar id PK
        text familyname
        text givenname
        text wikipediapage
    }
    intl_team {
        varchar teamcode PK
        text countryname
        text confederationname
        varchar confederationcode
        text wikipediapage
    }
    stadium {
        varchar stadiumid PK
        text city
        text name
        int capacity
        text country
        text wikipediapage
    }
    referee {
        varchar id PK
        text country
        varchar confederationcode
        text confederationname
    }
    intl_player {
        varchar id PK
        date dateofbirth
        varchar teamcode FK
    }
    intl_match {
        varchar matchid PK
        date matchdate
        text stage
        text tournament
        time matchtime
        varchar stadiumid FK
        varchar hometeamcode FK
        varchar guestteamcode FK
        varchar refereeid FK
    }
    match_event {
        varchar matcheventid PK
        text minute
        text eventtype
        varchar matchid FK
        varchar id FK
    }
    intl_player_match_stats {
        varchar matchid PK
        varchar playerid PK
        text position
        int shirtnumber
    }

    users ||--o{ fantasy_league : "created_by"
    users ||--o{ fantasy_team : "user_id"
    real_team ||--o{ player : "real_team_id"
    position ||--o{ player : "position_id"
    real_team ||--o{ match : "home_team_id"
    real_team ||--o{ match : "away_team_id"
    match_status ||--o{ match : "status_id"
    gameweek ||--o{ match : "gameweek_id"
    gameweek ||--o{ fantasy_team_selection : "gameweek_id"
    gameweek ||--o{ player_gameweek_stats : "gameweek_id"
    gameweek ||--o{ league_standing : "gameweek_id"
    gameweek ||--o{ transfer : "gameweek_id"
    player ||--o{ player_gameweek_stats : "player_id"
    player ||--o{ fantasy_team_selection : "player_id"
    player ||--o{ transfer : "player_out_id"
    player ||--o{ transfer : "player_in_id"
    match ||--o{ player_gameweek_stats : "match_id"
    fantasy_league ||--o{ fantasy_team : "league_id"
    fantasy_league ||--o{ league_standing : "league_id"
    fantasy_team ||--o{ fantasy_team_selection : "team_id"
    fantasy_team ||--o{ league_standing : "team_id"
    fantasy_team ||--o{ transfer : "team_id"
    person ||--o| referee : "id"
    person ||--o| intl_player : "id"
    player }o--o| person : "person_id"
    intl_team ||--o{ intl_player : "teamcode"
    intl_team ||--o{ intl_match : "hometeamcode"
    intl_team ||--o{ intl_match : "guestteamcode"
    stadium ||--o{ intl_match : "stadiumid"
    referee ||--o{ intl_match : "refereeid"
    intl_match ||--o{ match_event : "matchid"
    intl_player ||--o{ match_event : "id"
    intl_match ||--o{ intl_player_match_stats : "matchid"
    intl_player ||--o{ intl_player_match_stats : "playerid"
```

---

## Integration Process — Integrate.sql

The `Integrate.sql` file performs the full integration in three steps.

### Step 1 — Create the new tables

Eight tables from the received system are created in `mydatabase`. Four of them are renamed to avoid collisions with our existing tables:

| Original name | Name in integrated DB | Reason for rename |
|---|---|---|
| `team` | `intl_team` | Collides conceptually with our `real_team` |
| `player` | `intl_player` | Collides with our `player` table |
| `match` | `intl_match` | Collides with our `match` table |
| `player_match_stats` | `intl_player_match_stats` | Follows from `match` and `player` rename |

```sql
CREATE TABLE public.person (
    id            CHARACTER VARYING(50) NOT NULL,
    familyname    TEXT,
    givenname     TEXT NOT NULL,
    wikipediapage TEXT,
    CONSTRAINT person_pkey PRIMARY KEY (id)
);

CREATE TABLE public.intl_team (
    teamcode          CHARACTER VARYING(50) NOT NULL,
    countryname       TEXT NOT NULL,
    confederationname TEXT NOT NULL,
    confederationcode CHARACTER VARYING(50) NOT NULL,
    wikipediapage     TEXT,
    CONSTRAINT intl_team_pkey PRIMARY KEY (teamcode)
);

-- ... (stadium, referee, intl_player, intl_match, match_event, intl_player_match_stats)
```

### Step 2 — Modify the existing `player` table

A nullable foreign key column is added to our `player` table to link club players to their international identity in the World Cup data:

```sql
ALTER TABLE public.player
    ADD COLUMN person_id CHARACTER VARYING(50),
    ADD CONSTRAINT player_person_id_fkey
        FOREIGN KEY (person_id) REFERENCES public.person(id);
```

This column is intentionally nullable: the fantasy dataset contains generated players with no real-world counterpart, so most rows will have `NULL` here. Only players who actually appeared in the World Cup data can be linked.

### Step 3 — Import the data

All rows from the received backup are inserted into the new tables. Counts after import:

| Table | Rows |
|---|---|
| `person` | 8,287 |
| `intl_team` | 84 |
| `stadium` | 185 |
| `referee` | 380 |
| `intl_player` | 7,907 |
| `intl_match` | 700 |
| `match_event` | 10,722 |
| `intl_player_match_stats` | 18,623 |

### Verification — Phase B queries still work

After the integration all Phase B queries were re-run on the merged database and produced correct results. As an example:

```sql
-- Phase B Query 1: Players born in 2002 playing for English clubs
SELECT p.first_name, p.last_name, p.price,
       EXTRACT(YEAR FROM p.birth_date) AS birth_year
FROM player p
WHERE EXTRACT(YEAR FROM p.birth_date) = 2002
  AND p.real_team_id IN (
      SELECT real_team_id FROM real_team WHERE country = 'England'
  );
```

The new `person_id` column added to `player` has no effect on this query because it is nullable and not referenced.

---

## Views and Queries — Views.sql

### View 1: Fantasy Football Perspective — `v_fantasy_player_profile`

This view presents a combined player profile for the fantasy game, joining the `player`, `real_team`, and `position` tables. It gives a scout-style summary: full name, position, club, price, fantasy points earned, and ownership percentage.

```sql
CREATE VIEW v_fantasy_player_profile AS
SELECT
    p.player_id,
    p.first_name || ' ' || p.last_name  AS player_name,
    pos.position_name,
    pos.short_name                        AS pos_short,
    rt.team_name                          AS club_team,
    rt.country                            AS club_country,
    p.price,
    p.total_points,
    p.selected_by_percent,
    p.nationality
FROM public.player      p
JOIN public.real_team   rt  ON p.real_team_id  = rt.real_team_id
JOIN public.position    pos ON p.position_id   = pos.position_id;
```

**Sample output (`SELECT * ... LIMIT 10`):**

![View 1 sample](images/view1_sample.png)

---

#### Q1-A — Top 10 highest-scoring players

Answers the question: which players have accumulated the most fantasy points, regardless of position or price?

```sql
SELECT player_name, position_name, club_team, price, total_points
FROM   v_fantasy_player_profile
ORDER  BY total_points DESC
LIMIT  10;
```

![Q1-A output](images/q1a_output.png)

---

#### Q1-B — Most expensive player per position

Answers the question: what is the priciest option available in each position?

```sql
SELECT DISTINCT ON (position_name)
    position_name,
    player_name,
    club_team,
    price
FROM   v_fantasy_player_profile
ORDER  BY position_name, price DESC;
```

![Q1-B output](images/q1b_output.png)

---

### View 2: FIFA World Cup Perspective — `v_world_cup_match_details`

This view presents a human-readable match record for every World Cup fixture, replacing team codes and stadium IDs with full names. It joins `intl_match`, two instances of `intl_team` (home and guest), and `stadium`.

```sql
CREATE VIEW v_world_cup_match_details AS
SELECT
    im.matchid,
    im.tournament,
    im.stage,
    im.matchdate,
    home_t.countryname  AS home_team,
    guest_t.countryname AS guest_team,
    s.name              AS stadium_name,
    s.city              AS stadium_city,
    s.country           AS stadium_country,
    s.capacity          AS stadium_capacity,
    im.matchtime
FROM public.intl_match   im
JOIN public.intl_team    home_t  ON im.hometeamcode  = home_t.teamcode
JOIN public.intl_team    guest_t ON im.guestteamcode = guest_t.teamcode
JOIN public.stadium      s       ON im.stadiumid     = s.stadiumid;
```

**Sample output (`SELECT * ... LIMIT 10`):**

![View 2 sample](images/view2_sample.png)

---

#### Q2-A — Number of matches per tournament

Answers the question: how many fixtures were played in each World Cup edition?

```sql
SELECT tournament, COUNT(*) AS match_count
FROM   v_world_cup_match_details
GROUP  BY tournament
ORDER  BY match_count DESC;
```

![Q2-A output](images/q2a_output.png)

---

#### Q2-B — All World Cup Final matches

Answers the question: who played in each World Cup Final, and where?

```sql
SELECT tournament, matchdate, home_team, guest_team, stadium_name, stadium_city
FROM   v_world_cup_match_details
WHERE  stage = 'final'
ORDER  BY matchdate;
```

![Q2-B output](images/q2b_output.png)
