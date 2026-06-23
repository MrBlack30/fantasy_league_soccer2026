-- ============================================================
-- Views.sql
-- Two views on the integrated Fantasy Football + FIFA World Cup DB
-- ============================================================

-- ============================================================
-- VIEW 1: Fantasy Football perspective
-- Shows a combined player profile: name, position, club, price,
-- total fantasy points and ownership percentage.
-- Joins: player + real_team + position
-- ============================================================

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

-- ---- Queries on VIEW 1 ----------------------------------------

-- Q1-A: Top 10 highest-scoring players sorted by total fantasy points
SELECT player_name, position_name, club_team, price, total_points
FROM   v_fantasy_player_profile
ORDER  BY total_points DESC
LIMIT  10;

-- Q1-B: Most expensive players per position
--       (shows the priciest option in each position)
SELECT DISTINCT ON (position_name)
    position_name,
    player_name,
    club_team,
    price
FROM   v_fantasy_player_profile
ORDER  BY position_name, price DESC;

-- ============================================================
-- VIEW 2: FIFA World Cup perspective
-- Shows match details with full team names and stadium info.
-- Joins: intl_match + intl_team (home) + intl_team (guest) + stadium
-- ============================================================

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

-- ---- Queries on VIEW 2 ----------------------------------------

-- Q2-A: Number of matches played per tournament (ordered by most matches)
SELECT tournament, COUNT(*) AS match_count
FROM   v_world_cup_match_details
GROUP  BY tournament
ORDER  BY match_count DESC;

-- Q2-B: All Final-stage matches with participating teams and host city
SELECT tournament, matchdate, home_team, guest_team, stadium_name, stadium_city
FROM   v_world_cup_match_details
WHERE  stage = 'final'
ORDER  BY matchdate;
