--
-- PostgreSQL database dump
--

\restrict 38ANcb9yNkl2XbKCNxvaFhvtcA9EVxsluJyadA5U4qlMxb0chvCdY2B61MPTxzY

-- Dumped from database version 17.7 (Debian 17.7-3.pgdg13+1)
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: check_limits_on_bet(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.check_limits_on_bet() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
DECLARE
    settings RECORD;
    daily_total DECIMAL;
    weekly_total DECIMAL;
    monthly_total DECIMAL;
BEGIN
    -- Get user settings
    SELECT * INTO settings FROM bankroll_settings WHERE user_id = NEW.user_id;
    
    IF settings IS NOT NULL AND settings.enable_limit_alerts THEN
        -- Check daily limit
        IF settings.daily_limit IS NOT NULL THEN
            SELECT COALESCE(SUM(stake_amount), 0) INTO daily_total
            FROM bets
            WHERE user_id = NEW.user_id
            AND DATE(placed_at) = CURRENT_DATE;
            
            IF daily_total >= settings.daily_limit * (settings.alert_threshold_percentage / 100) THEN
                INSERT INTO user_alerts (user_id, alert_type, severity, message, related_bet_id)
                VALUES (
                    NEW.user_id,
                    'daily_limit',
                    'warning',
                    format('You have reached %s%% of your daily limit ($%s)', 
                           ROUND((daily_total / settings.daily_limit * 100), 0),
                           settings.daily_limit),
                    NEW.bet_id
                );
            END IF;
        END IF;
        
        -- Similar checks for weekly and monthly can be added
    END IF;
    
    RETURN NEW;
END;
$_$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bankroll_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bankroll_accounts (
    account_id integer NOT NULL,
    user_id integer DEFAULT 1 NOT NULL,
    bookmaker_name character varying(100) NOT NULL,
    current_balance numeric(10,2) DEFAULT 0 NOT NULL,
    starting_balance numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT bankroll_accounts_current_balance_check CHECK ((current_balance >= ('-10000'::integer)::numeric)),
    CONSTRAINT bankroll_accounts_starting_balance_check CHECK ((starting_balance >= (0)::numeric))
);


--
-- Name: bankroll_accounts_account_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bankroll_accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bankroll_accounts_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bankroll_accounts_account_id_seq OWNED BY public.bankroll_accounts.account_id;


--
-- Name: bankroll_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bankroll_settings (
    settings_id integer NOT NULL,
    user_id integer NOT NULL,
    daily_limit numeric(10,2),
    weekly_limit numeric(10,2),
    monthly_limit numeric(10,2),
    unit_size_type character varying(20) DEFAULT 'fixed'::character varying,
    unit_size_value numeric(10,2) DEFAULT 100.00,
    max_bet_percentage numeric(5,2) DEFAULT 5.00,
    enable_stop_loss boolean DEFAULT false,
    stop_loss_amount numeric(10,2),
    enable_limit_alerts boolean DEFAULT true,
    enable_streak_alerts boolean DEFAULT true,
    alert_threshold_percentage numeric(5,2) DEFAULT 80.00,
    daily_profit_goal numeric(10,2),
    weekly_profit_goal numeric(10,2),
    monthly_profit_goal numeric(10,2),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT bankroll_settings_alert_threshold_percentage_check CHECK (((alert_threshold_percentage > (0)::numeric) AND (alert_threshold_percentage <= (100)::numeric))),
    CONSTRAINT bankroll_settings_max_bet_percentage_check CHECK (((max_bet_percentage > (0)::numeric) AND (max_bet_percentage <= (100)::numeric))),
    CONSTRAINT bankroll_settings_unit_size_type_check CHECK (((unit_size_type)::text = ANY ((ARRAY['fixed'::character varying, 'percentage'::character varying])::text[])))
);


--
-- Name: bankroll_settings_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bankroll_settings_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bankroll_settings_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bankroll_settings_settings_id_seq OWNED BY public.bankroll_settings.settings_id;


--
-- Name: bankroll_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bankroll_transactions (
    transaction_id integer NOT NULL,
    account_id integer,
    user_id integer DEFAULT 1 NOT NULL,
    bet_id integer,
    transaction_type character varying(50) NOT NULL,
    amount numeric(10,2) NOT NULL,
    balance_after numeric(10,2) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT bankroll_transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['deposit'::character varying, 'withdrawal'::character varying, 'bet_placed'::character varying, 'bet_settled'::character varying, 'adjustment'::character varying])::text[])))
);


--
-- Name: bankroll_transactions_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bankroll_transactions_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bankroll_transactions_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bankroll_transactions_transaction_id_seq OWNED BY public.bankroll_transactions.transaction_id;


--
-- Name: bets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bets (
    bet_id integer NOT NULL,
    user_id integer DEFAULT 1 NOT NULL,
    account_id integer,
    bet_type character varying(50) NOT NULL,
    sport character varying(50) DEFAULT 'NFL'::character varying,
    game_id bigint,
    player_id bigint,
    market_key character varying(100),
    bet_side character varying(20),
    line_value numeric(10,2),
    odds_american integer NOT NULL,
    stake_amount numeric(10,2) NOT NULL,
    potential_payout numeric(10,2),
    actual_payout numeric(10,2),
    profit_loss numeric(10,2),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    placed_at timestamp without time zone DEFAULT now() NOT NULL,
    settled_at timestamp without time zone,
    notes text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    parlay_id integer,
    sport_id smallint,
    CONSTRAINT bets_odds_american_check CHECK ((odds_american <> 0)),
    CONSTRAINT bets_stake_amount_check CHECK ((stake_amount > (0)::numeric)),
    CONSTRAINT bets_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'won'::character varying, 'lost'::character varying, 'push'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: bets_bet_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bets_bet_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bets_bet_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bets_bet_id_seq OWNED BY public.bets.bet_id;


--
-- Name: book; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.book (
    book_id smallint NOT NULL,
    name text NOT NULL
);


--
-- Name: book_book_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.book_book_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: book_book_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.book_book_id_seq OWNED BY public.book.book_id;


--
-- Name: game; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game (
    game_id bigint NOT NULL,
    season_id smallint NOT NULL,
    week smallint NOT NULL,
    game_datetime_utc timestamp with time zone NOT NULL,
    home_team_id smallint NOT NULL,
    away_team_id smallint NOT NULL,
    venue_id smallint,
    status text DEFAULT 'scheduled'::text NOT NULL,
    external_game_key integer,
    sport_id smallint,
    CONSTRAINT game_check CHECK ((home_team_id <> away_team_id)),
    CONSTRAINT game_status_check CHECK ((status = ANY (ARRAY['scheduled'::text, 'in_progress'::text, 'final'::text, 'postponed'::text, 'canceled'::text]))),
    CONSTRAINT game_week_check CHECK (((week >= 0) AND (week <= 25)))
);


--
-- Name: game_game_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_game_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_game_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_game_id_seq OWNED BY public.game.game_id;


--
-- Name: game_player_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_player_statistics (
    stat_id bigint NOT NULL,
    game_id bigint NOT NULL,
    player_id bigint NOT NULL,
    team_id smallint NOT NULL,
    stat_group text NOT NULL,
    metric_name text NOT NULL,
    metric_value text,
    source text DEFAULT 'api-sports'::text,
    pulled_at_utc timestamp with time zone DEFAULT now(),
    CONSTRAINT game_player_statistics_stat_group_check CHECK ((stat_group = ANY (ARRAY['Passing'::text, 'Rushing'::text, 'Receiving'::text, 'Defense'::text, 'Fumbles'::text, 'Interceptions'::text, 'Kicking'::text, 'Punting'::text, 'Kick Returns'::text, 'Punt Returns'::text])))
);


--
-- Name: game_player_statistics_stat_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_player_statistics_stat_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_player_statistics_stat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_player_statistics_stat_id_seq OWNED BY public.game_player_statistics.stat_id;


--
-- Name: game_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_result (
    game_id bigint NOT NULL,
    home_score smallint NOT NULL,
    away_score smallint NOT NULL,
    home_win boolean GENERATED ALWAYS AS ((home_score > away_score)) STORED,
    total_points smallint GENERATED ALWAYS AS ((home_score + away_score)) STORED,
    CONSTRAINT game_result_away_score_check CHECK ((away_score >= 0)),
    CONSTRAINT game_result_home_score_check CHECK ((home_score >= 0))
);


--
-- Name: game_team_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_team_statistics (
    stat_id bigint NOT NULL,
    game_id bigint NOT NULL,
    team_id smallint NOT NULL,
    first_downs_total smallint,
    first_downs_passing smallint,
    first_downs_rushing smallint,
    first_downs_from_penalties smallint,
    third_down_efficiency text,
    fourth_down_efficiency text,
    plays_total smallint,
    yards_total smallint,
    yards_per_play numeric(4,1),
    total_drives numeric(4,1),
    passing_yards smallint,
    passing_comp_att text,
    passing_yards_per_pass numeric(4,1),
    passing_interceptions_thrown smallint,
    passing_sacks_yards_lost text,
    rushing_yards smallint,
    rushing_attempts smallint,
    rushing_yards_per_rush numeric(4,1),
    red_zone_made_att text,
    penalties_total text,
    turnovers_total smallint,
    turnovers_lost_fumbles smallint,
    turnovers_interceptions smallint,
    possession_total text,
    interceptions_total smallint,
    fumbles_recovered_total smallint,
    sacks_total smallint,
    safeties_total smallint,
    int_touchdowns_total smallint,
    points_against_total smallint,
    source text DEFAULT 'api-sports'::text,
    pulled_at_utc timestamp with time zone DEFAULT now()
);


--
-- Name: game_team_statistics_stat_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_team_statistics_stat_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_team_statistics_stat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_team_statistics_stat_id_seq OWNED BY public.game_team_statistics.stat_id;


--
-- Name: injury_report; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.injury_report (
    report_id bigint NOT NULL,
    game_id bigint NOT NULL,
    team_id smallint NOT NULL,
    player_id bigint NOT NULL,
    status text NOT NULL,
    designation text,
    updated_at_utc timestamp with time zone NOT NULL,
    source text,
    CONSTRAINT injury_report_status_check CHECK ((status = ANY (ARRAY['out'::text, 'doubtful'::text, 'questionable'::text, 'probable'::text, 'active'::text, 'inactive'::text, 'unknown'::text])))
);


--
-- Name: injury_report_report_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.injury_report_report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: injury_report_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.injury_report_report_id_seq OWNED BY public.injury_report.report_id;


--
-- Name: league; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.league (
    league_id smallint NOT NULL,
    name text NOT NULL,
    sport_id smallint,
    league_code character varying(20)
);


--
-- Name: league_league_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.league_league_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: league_league_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.league_league_id_seq OWNED BY public.league.league_id;


--
-- Name: odds_line; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.odds_line (
    line_id bigint NOT NULL,
    game_id bigint NOT NULL,
    book_id smallint NOT NULL,
    market text NOT NULL,
    side text NOT NULL,
    line_value numeric(6,2),
    price_american integer NOT NULL,
    pulled_at_utc timestamp with time zone NOT NULL,
    source text,
    CONSTRAINT odds_line_check CHECK ((((market = 'moneyline'::text) AND (line_value IS NULL)) OR ((market = ANY (ARRAY['spread'::text, 'total'::text])) AND (line_value IS NOT NULL)))),
    CONSTRAINT odds_line_check1 CHECK (((market <> 'total'::text) OR (line_value >= (0)::numeric))),
    CONSTRAINT odds_line_market_check CHECK ((market = ANY (ARRAY['spread'::text, 'total'::text, 'moneyline'::text]))),
    CONSTRAINT odds_line_price_american_check CHECK (((price_american <> 0) AND ((price_american >= '-10000'::integer) AND (price_american <= 10000)))),
    CONSTRAINT odds_line_side_check CHECK ((side = ANY (ARRAY['home'::text, 'away'::text, 'over'::text, 'under'::text])))
);


--
-- Name: odds_line_line_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.odds_line_line_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: odds_line_line_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.odds_line_line_id_seq OWNED BY public.odds_line.line_id;


--
-- Name: parlay_bets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parlay_bets (
    parlay_id integer NOT NULL,
    user_id integer NOT NULL,
    account_id integer,
    num_legs integer NOT NULL,
    total_odds_american integer NOT NULL,
    stake_amount numeric(10,2) NOT NULL,
    potential_payout numeric(10,2),
    actual_payout numeric(10,2),
    profit_loss numeric(10,2),
    status character varying(20) DEFAULT 'pending'::character varying,
    legs_won integer DEFAULT 0,
    legs_lost integer DEFAULT 0,
    legs_pending integer,
    placed_at timestamp without time zone DEFAULT now() NOT NULL,
    settled_at timestamp without time zone,
    notes text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT parlay_bets_num_legs_check CHECK ((num_legs >= 2)),
    CONSTRAINT parlay_bets_stake_amount_check CHECK ((stake_amount > (0)::numeric)),
    CONSTRAINT parlay_bets_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'won'::character varying, 'lost'::character varying, 'partial_win'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: parlay_bets_parlay_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parlay_bets_parlay_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parlay_bets_parlay_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parlay_bets_parlay_id_seq OWNED BY public.parlay_bets.parlay_id;


--
-- Name: player; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player (
    player_id bigint NOT NULL,
    full_name text NOT NULL,
    "position" text,
    team_id smallint,
    external_player_id integer,
    jersey_number smallint,
    height text,
    weight text,
    age smallint,
    college text,
    experience_years smallint,
    salary text,
    image_url text,
    player_group text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    sport_id smallint,
    position_id integer
);


--
-- Name: player_odds; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player_odds (
    odds_id bigint NOT NULL,
    game_id bigint NOT NULL,
    player_id bigint NOT NULL,
    book_id smallint NOT NULL,
    market_key text NOT NULL,
    bet_type text NOT NULL,
    line_value numeric(6,2) NOT NULL,
    odds_american integer NOT NULL,
    pulled_at_utc timestamp with time zone NOT NULL,
    source text DEFAULT 'the-odds-api'::text,
    CONSTRAINT player_odds_bet_type_check CHECK ((bet_type = ANY (ARRAY['over'::text, 'under'::text]))),
    CONSTRAINT player_odds_line_value_check CHECK ((line_value > (0)::numeric)),
    CONSTRAINT player_odds_odds_american_check CHECK (((odds_american <> 0) AND ((odds_american >= '-10000'::integer) AND (odds_american <= 10000))))
);


--
-- Name: player_odds_odds_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.player_odds_odds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: player_odds_odds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.player_odds_odds_id_seq OWNED BY public.player_odds.odds_id;


--
-- Name: player_player_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.player_player_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: player_player_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.player_player_id_seq OWNED BY public.player.player_id;


--
-- Name: player_statistic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.player_statistic (
    statistic_id bigint NOT NULL,
    player_id bigint NOT NULL,
    team_id smallint NOT NULL,
    season_id smallint NOT NULL,
    stat_group text NOT NULL,
    metric_name text NOT NULL,
    metric_value text,
    pulled_at_utc timestamp with time zone DEFAULT now() NOT NULL,
    source text DEFAULT 'api-sports'::text,
    CONSTRAINT player_statistic_stat_group_check CHECK ((stat_group = ANY (ARRAY['Passing'::text, 'Rushing'::text, 'Receiving'::text, 'Defense'::text, 'Kicking'::text, 'Punting'::text, 'Returning'::text, 'Scoring'::text])))
);


--
-- Name: TABLE player_statistic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.player_statistic IS 'Detailed player statistics from API-Sports grouped by category (Passing, Rushing, Receiving, Defense, etc.)';


--
-- Name: COLUMN player_statistic.stat_group; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.player_statistic.stat_group IS 'Statistics category: Passing, Rushing, Receiving, Defense, Kicking, Punting, Returning, Scoring';


--
-- Name: COLUMN player_statistic.metric_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.player_statistic.metric_name IS 'Specific metric name (e.g., "passing attempts", "yards", "touchdowns")';


--
-- Name: COLUMN player_statistic.metric_value; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.player_statistic.metric_value IS 'Metric value stored as TEXT to handle NULL, integers, decimals, and percentages';


--
-- Name: season; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.season (
    season_id smallint NOT NULL,
    league_id smallint NOT NULL,
    year smallint NOT NULL
);


--
-- Name: team; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team (
    team_id smallint NOT NULL,
    league_id smallint NOT NULL,
    name text NOT NULL,
    abbrev text NOT NULL,
    city text,
    external_team_key integer NOT NULL,
    coach text,
    owner text,
    stadium text,
    established integer,
    logo_url text,
    country_name text,
    country_code text,
    country_flag_url text,
    updated_at timestamp with time zone DEFAULT now(),
    sport_id smallint
);


--
-- Name: player_season_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.player_season_summary AS
 SELECT ps.player_id,
    ps.season_id,
    ps.team_id,
    p.full_name,
    p."position",
    t.name AS team_name,
    t.abbrev AS team_abbrev,
    s.year AS season_year,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'passing attempts'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS passing_attempts,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'completions'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS completions,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'yards'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS passing_yards,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'passing touchdowns'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS passing_tds,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'interceptions'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS interceptions,
    max(
        CASE
            WHEN ((ps.stat_group = 'Passing'::text) AND (ps.metric_name = 'quaterback rating'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS qb_rating,
    max(
        CASE
            WHEN ((ps.stat_group = 'Rushing'::text) AND (ps.metric_name = 'rushing attempts'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS rushing_attempts,
    max(
        CASE
            WHEN ((ps.stat_group = 'Rushing'::text) AND (ps.metric_name = 'yards'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS rushing_yards,
    max(
        CASE
            WHEN ((ps.stat_group = 'Rushing'::text) AND (ps.metric_name = 'rushing touchdowns'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS rushing_tds,
    max(
        CASE
            WHEN ((ps.stat_group = 'Receiving'::text) AND (ps.metric_name = 'receptions'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS receptions,
    max(
        CASE
            WHEN ((ps.stat_group = 'Receiving'::text) AND (ps.metric_name = 'yards'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS receiving_yards,
    max(
        CASE
            WHEN ((ps.stat_group = 'Receiving'::text) AND (ps.metric_name = 'receiving touchdowns'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS receiving_tds,
    max(
        CASE
            WHEN ((ps.stat_group = 'Defense'::text) AND (ps.metric_name = 'total tackles'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS tackles,
    max(
        CASE
            WHEN ((ps.stat_group = 'Defense'::text) AND (ps.metric_name = 'sacks'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS sacks,
    max(
        CASE
            WHEN ((ps.stat_group = 'Defense'::text) AND (ps.metric_name = 'interceptions'::text)) THEN ps.metric_value
            ELSE NULL::text
        END) AS def_interceptions,
    max(ps.pulled_at_utc) AS last_updated
   FROM (((public.player_statistic ps
     JOIN public.player p ON ((ps.player_id = p.player_id)))
     JOIN public.team t ON ((ps.team_id = t.team_id)))
     JOIN public.season s ON ((ps.season_id = s.season_id)))
  GROUP BY ps.player_id, ps.season_id, ps.team_id, p.full_name, p."position", t.name, t.abbrev, s.year
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW player_season_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON MATERIALIZED VIEW public.player_season_summary IS 'Aggregated view of key player statistics per season for quick lookups. Refresh periodically.';


--
-- Name: player_statistic_statistic_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.player_statistic_statistic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: player_statistic_statistic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.player_statistic_statistic_id_seq OWNED BY public.player_statistic.statistic_id;


--
-- Name: season_season_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.season_season_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: season_season_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.season_season_id_seq OWNED BY public.season.season_id;


--
-- Name: sport_position; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sport_position (
    position_id integer NOT NULL,
    sport_id smallint NOT NULL,
    position_code character varying(10) NOT NULL,
    position_name text NOT NULL,
    position_group character varying(50),
    abbreviation character varying(5),
    description text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: TABLE sport_position; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sport_position IS 'Maps positions to sports (e.g., QB=NFL, PG=NBA)';


--
-- Name: sport_position_position_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sport_position_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sport_position_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sport_position_position_id_seq OWNED BY public.sport_position.position_id;


--
-- Name: sport_stat_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sport_stat_type (
    stat_type_id integer NOT NULL,
    sport_id smallint NOT NULL,
    stat_group character varying(50) NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_code character varying(50),
    data_type character varying(20) DEFAULT 'numeric'::character varying,
    unit character varying(20),
    description text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT sport_stat_type_data_type_check CHECK (((data_type)::text = ANY ((ARRAY['numeric'::character varying, 'text'::character varying, 'time'::character varying, 'boolean'::character varying])::text[])))
);


--
-- Name: TABLE sport_stat_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sport_stat_type IS 'Defines valid stat types for each sport';


--
-- Name: sport_stat_type_stat_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sport_stat_type_stat_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sport_stat_type_stat_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sport_stat_type_stat_type_id_seq OWNED BY public.sport_stat_type.stat_type_id;


--
-- Name: sport_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sport_type (
    sport_id smallint NOT NULL,
    sport_code character varying(10) NOT NULL,
    sport_name text NOT NULL,
    sport_category character varying(20) NOT NULL,
    is_active boolean DEFAULT true,
    has_quarters boolean,
    has_halves boolean,
    has_periods boolean,
    has_innings boolean,
    num_periods smallint,
    icon_url text,
    display_order smallint,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT sport_type_sport_category_check CHECK (((sport_category)::text = ANY ((ARRAY['football'::character varying, 'basketball'::character varying, 'baseball'::character varying, 'hockey'::character varying, 'soccer'::character varying, 'other'::character varying])::text[])))
);


--
-- Name: TABLE sport_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sport_type IS 'Defines all sports supported by SmartLine';


--
-- Name: COLUMN sport_type.sport_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sport_type.sport_code IS 'Short code for sport (e.g., NFL, NBA)';


--
-- Name: COLUMN sport_type.sport_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sport_type.sport_category IS 'Category: football, basketball, baseball, hockey, soccer, other';


--
-- Name: COLUMN sport_type.num_periods; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sport_type.num_periods IS 'Number of periods/quarters/innings in a standard game';


--
-- Name: sport_type_sport_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sport_type_sport_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sport_type_sport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sport_type_sport_id_seq OWNED BY public.sport_type.sport_id;


--
-- Name: team_game_stat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team_game_stat (
    game_id bigint NOT NULL,
    team_id smallint NOT NULL,
    metric text NOT NULL,
    value numeric(12,4) NOT NULL
);


--
-- Name: team_team_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.team_team_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: team_team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.team_team_id_seq OWNED BY public.team.team_id;


--
-- Name: user_account; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account (
    user_id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    username character varying(50),
    first_name character varying(100),
    last_name character varying(100),
    display_name character varying(100),
    is_active boolean DEFAULT true,
    is_verified boolean DEFAULT false,
    email_verified_at timestamp without time zone,
    timezone character varying(50) DEFAULT 'America/New_York'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    last_login_at timestamp without time zone,
    failed_login_attempts integer DEFAULT 0,
    locked_until timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT user_account_email_check CHECK (((email)::text ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text)),
    CONSTRAINT user_account_failed_login_attempts_check CHECK ((failed_login_attempts >= 0))
);


--
-- Name: TABLE user_account; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_account IS 'User authentication and profile management';


--
-- Name: COLUMN user_account.password_hash; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_account.password_hash IS 'bcrypt hash of user password';


--
-- Name: COLUMN user_account.is_verified; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_account.is_verified IS 'Email verification status';


--
-- Name: COLUMN user_account.locked_until; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_account.locked_until IS 'Account locked until this timestamp (for failed login attempts)';


--
-- Name: user_account_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_account_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_account_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_account_user_id_seq OWNED BY public.user_account.user_id;


--
-- Name: user_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_alerts (
    alert_id integer NOT NULL,
    user_id integer NOT NULL,
    alert_type character varying(50) NOT NULL,
    severity character varying(20) DEFAULT 'info'::character varying,
    message text NOT NULL,
    is_read boolean DEFAULT false,
    read_at timestamp without time zone,
    related_bet_id integer,
    related_goal_id integer,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT user_alerts_severity_check CHECK (((severity)::text = ANY ((ARRAY['info'::character varying, 'warning'::character varying, 'error'::character varying])::text[])))
);


--
-- Name: user_alerts_alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_alerts_alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_alerts_alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_alerts_alert_id_seq OWNED BY public.user_alerts.alert_id;


--
-- Name: user_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_goals (
    goal_id integer NOT NULL,
    user_id integer NOT NULL,
    goal_type character varying(20) NOT NULL,
    goal_amount numeric(10,2) NOT NULL,
    current_progress numeric(10,2) DEFAULT 0,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    completed_at timestamp without time zone,
    description text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT user_goals_check CHECK ((end_date >= start_date)),
    CONSTRAINT user_goals_goal_amount_check CHECK ((goal_amount > (0)::numeric)),
    CONSTRAINT user_goals_goal_type_check CHECK (((goal_type)::text = ANY ((ARRAY['daily'::character varying, 'weekly'::character varying, 'monthly'::character varying, 'yearly'::character varying, 'custom'::character varying])::text[]))),
    CONSTRAINT user_goals_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: user_goals_goal_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_goals_goal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_goals_goal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_goals_goal_id_seq OWNED BY public.user_goals.goal_id;


--
-- Name: v_bankroll_overview; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_bankroll_overview AS
 SELECT user_id,
    sum(current_balance) AS total_bankroll,
    sum(starting_balance) AS total_starting_balance,
    (sum(current_balance) - sum(starting_balance)) AS total_profit_loss,
        CASE
            WHEN (sum(starting_balance) > (0)::numeric) THEN round((((sum(current_balance) - sum(starting_balance)) / sum(starting_balance)) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS roi_percentage,
    count(*) AS total_accounts
   FROM public.bankroll_accounts
  GROUP BY user_id;


--
-- Name: v_best_odds_finder; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_best_odds_finder AS
 WITH ranked_odds AS (
         SELECT po.odds_id,
            po.game_id,
            po.player_id,
            po.book_id,
            po.market_key,
            po.bet_type,
            po.line_value,
            po.odds_american,
            po.pulled_at_utc,
            po.source,
            p.full_name AS player_name,
            p."position",
            t.abbrev AS player_team,
            b.name AS bookmaker,
            g.week,
            g.game_datetime_utc,
            s.year AS season_year,
            row_number() OVER (PARTITION BY po.game_id, po.player_id, po.market_key, po.bet_type ORDER BY po.odds_american DESC) AS odds_rank
           FROM (((((public.player_odds po
             JOIN public.player p ON ((po.player_id = p.player_id)))
             LEFT JOIN public.team t ON ((p.team_id = t.team_id)))
             JOIN public.book b ON ((po.book_id = b.book_id)))
             JOIN public.game g ON ((po.game_id = g.game_id)))
             JOIN public.season s ON ((g.season_id = s.season_id)))
        )
 SELECT game_id,
    player_id,
    player_name,
    "position",
    player_team,
    market_key,
    bet_type,
    line_value,
    odds_american AS best_odds_american,
    bookmaker AS best_odds_bookmaker,
    week,
    game_datetime_utc,
    season_year,
    pulled_at_utc
   FROM ranked_odds
  WHERE (odds_rank = 1);


--
-- Name: VIEW v_best_odds_finder; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_best_odds_finder IS 'Best available odds for each prop across all bookmakers.';


--
-- Name: v_bet_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_bet_statistics AS
 SELECT user_id,
    count(*) AS total_bets,
    count(*) FILTER (WHERE ((status)::text = 'pending'::text)) AS pending_bets,
    count(*) FILTER (WHERE ((status)::text = 'won'::text)) AS won_bets,
    count(*) FILTER (WHERE ((status)::text = 'lost'::text)) AS lost_bets,
    count(*) FILTER (WHERE ((status)::text = 'push'::text)) AS push_bets,
    COALESCE(sum(stake_amount) FILTER (WHERE ((status)::text = 'pending'::text)), (0)::numeric) AS locked_in_bets,
    COALESCE(sum(profit_loss) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))), (0)::numeric) AS total_profit_loss,
        CASE
            WHEN (count(*) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))) > 0) THEN round((((count(*) FILTER (WHERE ((status)::text = 'won'::text)))::numeric / (count(*) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))))::numeric) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS win_rate,
    COALESCE(avg(stake_amount), (0)::numeric) AS avg_bet_size
   FROM public.bets
  GROUP BY user_id;


--
-- Name: v_bookmaker_comparison; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_bookmaker_comparison AS
 SELECT b.book_id,
    b.name AS bookmaker_name,
    s.year AS season_year,
    po.market_key,
    count(DISTINCT po.game_id) AS games_covered,
    count(DISTINCT po.player_id) AS players_covered,
    count(po.odds_id) AS total_props_offered,
    round(avg(po.odds_american), 0) AS avg_odds_american,
    round(avg(abs((po.odds_american + 110))), 0) AS avg_distance_from_standard_vig,
    count(*) FILTER (WHERE (po.odds_american = ( SELECT max(po2.odds_american) AS max
           FROM public.player_odds po2
          WHERE ((po2.game_id = po.game_id) AND (po2.player_id = po.player_id) AND (po2.market_key = po.market_key) AND (po2.bet_type = po.bet_type))))) AS times_had_best_odds,
    round((((count(*) FILTER (WHERE (po.odds_american = ( SELECT max(po2.odds_american) AS max
           FROM public.player_odds po2
          WHERE ((po2.game_id = po.game_id) AND (po2.player_id = po.player_id) AND (po2.market_key = po.market_key) AND (po2.bet_type = po.bet_type))))))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS best_odds_pct
   FROM (((public.book b
     JOIN public.player_odds po ON ((b.book_id = po.book_id)))
     JOIN public.game g ON ((po.game_id = g.game_id)))
     JOIN public.season s ON ((g.season_id = s.season_id)))
  GROUP BY b.book_id, b.name, s.year, po.market_key;


--
-- Name: VIEW v_bookmaker_comparison; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_bookmaker_comparison IS 'Comparative analysis of bookmaker coverage and odds competitiveness.';


--
-- Name: v_current_limits_status; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_current_limits_status AS
 SELECT bs.user_id,
    bs.daily_limit,
    bs.weekly_limit,
    bs.monthly_limit,
    COALESCE(sum(b.stake_amount) FILTER (WHERE (date(b.placed_at) = CURRENT_DATE)), (0)::numeric) AS daily_spent,
        CASE
            WHEN (bs.daily_limit IS NOT NULL) THEN round(((COALESCE(sum(b.stake_amount) FILTER (WHERE (date(b.placed_at) = CURRENT_DATE)), (0)::numeric) / bs.daily_limit) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS daily_used_percentage,
    COALESCE(sum(b.stake_amount) FILTER (WHERE (b.placed_at >= date_trunc('week'::text, (CURRENT_DATE)::timestamp with time zone))), (0)::numeric) AS weekly_spent,
        CASE
            WHEN (bs.weekly_limit IS NOT NULL) THEN round(((COALESCE(sum(b.stake_amount) FILTER (WHERE (b.placed_at >= date_trunc('week'::text, (CURRENT_DATE)::timestamp with time zone))), (0)::numeric) / bs.weekly_limit) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS weekly_used_percentage,
    COALESCE(sum(b.stake_amount) FILTER (WHERE (b.placed_at >= date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))), (0)::numeric) AS monthly_spent,
        CASE
            WHEN (bs.monthly_limit IS NOT NULL) THEN round(((COALESCE(sum(b.stake_amount) FILTER (WHERE (b.placed_at >= date_trunc('month'::text, (CURRENT_DATE)::timestamp with time zone))), (0)::numeric) / bs.monthly_limit) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS monthly_used_percentage
   FROM (public.bankroll_settings bs
     LEFT JOIN public.bets b ON ((bs.user_id = b.user_id)))
  GROUP BY bs.user_id, bs.daily_limit, bs.weekly_limit, bs.monthly_limit;


--
-- Name: v_daily_bankroll_history; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_daily_bankroll_history AS
 WITH daily_transactions AS (
         SELECT bankroll_transactions.user_id,
            date(bankroll_transactions.created_at) AS transaction_date,
            sum(
                CASE
                    WHEN (((bankroll_transactions.transaction_type)::text = ANY ((ARRAY['deposit'::character varying, 'bet_settled'::character varying])::text[])) AND (bankroll_transactions.amount > (0)::numeric)) THEN bankroll_transactions.amount
                    ELSE (0)::numeric
                END) AS total_deposits,
            sum(
                CASE
                    WHEN ((bankroll_transactions.transaction_type)::text = 'withdrawal'::text) THEN abs(bankroll_transactions.amount)
                    ELSE (0)::numeric
                END) AS total_withdrawals,
            sum(
                CASE
                    WHEN ((bankroll_transactions.transaction_type)::text = 'bet_placed'::text) THEN abs(bankroll_transactions.amount)
                    ELSE (0)::numeric
                END) AS total_wagered,
            sum(
                CASE
                    WHEN ((bankroll_transactions.transaction_type)::text = 'bet_settled'::text) THEN bankroll_transactions.amount
                    ELSE (0)::numeric
                END) AS total_won
           FROM public.bankroll_transactions
          GROUP BY bankroll_transactions.user_id, (date(bankroll_transactions.created_at))
        )
 SELECT user_id,
    transaction_date,
    total_deposits,
    total_withdrawals,
    total_wagered,
    total_won,
    (((total_deposits - total_withdrawals) + total_won) - total_wagered) AS net_change
   FROM daily_transactions
  ORDER BY transaction_date DESC;


--
-- Name: v_goal_progress; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_goal_progress AS
 SELECT g.goal_id,
    g.user_id,
    g.goal_type,
    g.goal_amount,
    g.start_date,
    g.end_date,
    g.status,
    g.description,
    COALESCE(sum(b.profit_loss) FILTER (WHERE (((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[])) AND ((date(b.settled_at) >= g.start_date) AND (date(b.settled_at) <= g.end_date)))), (0)::numeric) AS current_progress,
        CASE
            WHEN (g.goal_amount > (0)::numeric) THEN round(((COALESCE(sum(b.profit_loss) FILTER (WHERE (((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[])) AND ((date(b.settled_at) >= g.start_date) AND (date(b.settled_at) <= g.end_date)))), (0)::numeric) / g.goal_amount) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS progress_percentage,
        CASE
            WHEN (g.end_date >= CURRENT_DATE) THEN (g.end_date - CURRENT_DATE)
            ELSE 0
        END AS days_remaining,
    ((g.end_date - g.start_date) + 1) AS total_days
   FROM (public.user_goals g
     LEFT JOIN public.bets b ON ((g.user_id = b.user_id)))
  GROUP BY g.goal_id, g.user_id, g.goal_type, g.goal_amount, g.start_date, g.end_date, g.status, g.description;


--
-- Name: v_home_away_splits; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_home_away_splits AS
 WITH player_game_results AS (
         SELECT p.player_id,
            p.full_name AS player_name,
            p."position",
            po.market_key,
            s.year AS season_year,
                CASE
                    WHEN (p.team_id = g.home_team_id) THEN 'home'::text
                    ELSE 'away'::text
                END AS home_away,
            avg(po.line_value) AS line_value,
            (gps.metric_value)::numeric AS actual_result
           FROM ((((public.player p
             JOIN public.player_odds po ON ((p.player_id = po.player_id)))
             JOIN public.game g ON ((po.game_id = g.game_id)))
             JOIN public.season s ON ((g.season_id = s.season_id)))
             LEFT JOIN public.game_player_statistics gps ON (((po.game_id = gps.game_id) AND (po.player_id = gps.player_id) AND (((po.market_key = 'player_pass_yds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_pass_tds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'touchdowns'::text)) OR ((po.market_key = 'player_rush_yds'::text) AND (gps.stat_group = 'Rushing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_reception_yds'::text) AND (gps.stat_group = 'Receiving'::text) AND (gps.metric_name = 'yards'::text))))))
          WHERE (gps.metric_value IS NOT NULL)
          GROUP BY p.player_id, p.full_name, p."position", po.market_key, s.year, p.team_id, g.home_team_id, g.game_id, gps.metric_value
        )
 SELECT player_id,
    player_name,
    "position",
    market_key,
    season_year,
    count(*) FILTER (WHERE (home_away = 'home'::text)) AS home_games,
    round(avg(actual_result) FILTER (WHERE (home_away = 'home'::text)), 2) AS home_avg,
    round(avg(line_value) FILTER (WHERE (home_away = 'home'::text)), 2) AS home_avg_line,
    count(*) FILTER (WHERE ((home_away = 'home'::text) AND (actual_result > line_value))) AS home_overs,
    count(*) FILTER (WHERE (home_away = 'away'::text)) AS away_games,
    round(avg(actual_result) FILTER (WHERE (home_away = 'away'::text)), 2) AS away_avg,
    round(avg(line_value) FILTER (WHERE (home_away = 'away'::text)), 2) AS away_avg_line,
    count(*) FILTER (WHERE ((home_away = 'away'::text) AND (actual_result > line_value))) AS away_overs,
    round((avg(actual_result) FILTER (WHERE (home_away = 'home'::text)) - avg(actual_result) FILTER (WHERE (home_away = 'away'::text))), 2) AS home_away_diff
   FROM player_game_results
  GROUP BY player_id, player_name, "position", market_key, season_year
 HAVING ((count(*) FILTER (WHERE (home_away = 'home'::text)) > 0) AND (count(*) FILTER (WHERE (home_away = 'away'::text)) > 0));


--
-- Name: VIEW v_home_away_splits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_home_away_splits IS 'Player performance and over/under rates split by home vs away games.';


--
-- Name: v_performance_by_bookmaker; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_performance_by_bookmaker AS
 SELECT b.user_id,
    ba.bookmaker_name,
    count(*) AS total_bets,
    count(*) FILTER (WHERE ((b.status)::text = 'won'::text)) AS won_bets,
    count(*) FILTER (WHERE ((b.status)::text = 'lost'::text)) AS lost_bets,
    COALESCE(sum(b.profit_loss) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))), (0)::numeric) AS total_profit_loss,
        CASE
            WHEN (count(*) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))) > 0) THEN round((((count(*) FILTER (WHERE ((b.status)::text = 'won'::text)))::numeric / (count(*) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))))::numeric) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS win_rate
   FROM (public.bets b
     LEFT JOIN public.bankroll_accounts ba ON ((b.account_id = ba.account_id)))
  GROUP BY b.user_id, ba.bookmaker_name;


--
-- Name: v_performance_by_market; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_performance_by_market AS
 SELECT user_id,
    market_key,
    count(*) AS total_bets,
    count(*) FILTER (WHERE ((status)::text = 'won'::text)) AS won_bets,
    count(*) FILTER (WHERE ((status)::text = 'lost'::text)) AS lost_bets,
    COALESCE(sum(profit_loss) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))), (0)::numeric) AS total_profit_loss,
        CASE
            WHEN (count(*) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))) > 0) THEN round((((count(*) FILTER (WHERE ((status)::text = 'won'::text)))::numeric / (count(*) FILTER (WHERE ((status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))))::numeric) * (100)::numeric), 1)
            ELSE (0)::numeric
        END AS win_rate,
    round(avg(stake_amount), 2) AS avg_stake
   FROM public.bets b
  WHERE (market_key IS NOT NULL)
  GROUP BY user_id, market_key;


--
-- Name: v_player_odds_by_game; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_odds_by_game AS
 SELECT g.game_id,
    g.week,
    s.year AS season_year,
    g.game_datetime_utc,
    ht.name AS home_team,
    ht.abbrev AS home_abbrev,
    at.name AS away_team,
    at.abbrev AS away_abbrev,
    count(DISTINCT po.player_id) AS players_with_props,
    count(DISTINCT po.market_key) AS markets_offered,
    count(DISTINCT po.book_id) AS bookmakers,
    count(po.odds_id) AS total_prop_count,
    string_agg(DISTINCT p.full_name, ', '::text ORDER BY p.full_name) FILTER (WHERE (po.market_key = 'player_pass_yds'::text)) AS qbs_with_props,
    string_agg(DISTINCT p.full_name, ', '::text ORDER BY p.full_name) FILTER (WHERE (po.market_key = 'player_rush_yds'::text)) AS rbs_with_props,
    string_agg(DISTINCT p.full_name, ', '::text ORDER BY p.full_name) FILTER (WHERE (po.market_key = 'player_reception_yds'::text)) AS receivers_with_props,
    min(po.pulled_at_utc) AS earliest_pull,
    max(po.pulled_at_utc) AS latest_pull
   FROM (((((public.game g
     JOIN public.season s ON ((g.season_id = s.season_id)))
     JOIN public.team ht ON ((g.home_team_id = ht.team_id)))
     JOIN public.team at ON ((g.away_team_id = at.team_id)))
     LEFT JOIN public.player_odds po ON ((g.game_id = po.game_id)))
     LEFT JOIN public.player p ON ((po.player_id = p.player_id)))
  GROUP BY g.game_id, g.week, s.year, g.game_datetime_utc, ht.name, ht.abbrev, at.name, at.abbrev;


--
-- Name: VIEW v_player_odds_by_game; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_odds_by_game IS 'Game-level aggregation of player prop availability and coverage.';


--
-- Name: v_player_odds_consensus; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_odds_consensus AS
 SELECT po.game_id,
    po.player_id,
    po.market_key,
    po.bet_type,
    g.week,
    g.game_datetime_utc,
    s.year AS season_year,
    p.full_name AS player_name,
    p."position" AS player_position,
    t.abbrev AS player_team,
    round(avg(po.line_value), 2) AS consensus_line,
    round(avg(po.odds_american), 0) AS consensus_odds_american,
    count(DISTINCT po.book_id) AS num_bookmakers,
    max(po.odds_american) AS best_odds_american,
    min(po.line_value) AS min_line,
    max(po.line_value) AS max_line,
    round((max(po.line_value) - min(po.line_value)), 2) AS line_spread,
    min(po.odds_american) AS min_odds,
    max(po.odds_american) AS max_odds,
    ( SELECT b.name
           FROM (public.player_odds po2
             JOIN public.book b ON ((po2.book_id = b.book_id)))
          WHERE ((po2.game_id = po.game_id) AND (po2.player_id = po.player_id) AND (po2.market_key = po.market_key) AND (po2.bet_type = po.bet_type))
          ORDER BY po2.odds_american DESC
         LIMIT 1) AS best_odds_bookmaker,
    max(po.pulled_at_utc) AS latest_pull_time
   FROM ((((public.player_odds po
     JOIN public.game g ON ((po.game_id = g.game_id)))
     JOIN public.season s ON ((g.season_id = s.season_id)))
     JOIN public.player p ON ((po.player_id = p.player_id)))
     LEFT JOIN public.team t ON ((p.team_id = t.team_id)))
  GROUP BY po.game_id, po.player_id, po.market_key, po.bet_type, g.week, g.game_datetime_utc, s.year, p.full_name, p."position", t.abbrev;


--
-- Name: VIEW v_player_odds_consensus; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_odds_consensus IS 'Aggregated consensus odds across all bookmakers with best odds identification.';


--
-- Name: v_player_odds_detailed; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_odds_detailed AS
 SELECT po.odds_id,
    po.game_id,
    po.player_id,
    po.book_id,
    po.market_key,
    po.bet_type,
    po.line_value,
    po.odds_american,
    po.pulled_at_utc,
    po.source,
    g.week,
    g.game_datetime_utc,
    s.year AS season_year,
    ht.team_id AS home_team_id,
    ht.name AS home_team_name,
    ht.abbrev AS home_team_abbrev,
    at.team_id AS away_team_id,
    at.name AS away_team_name,
    at.abbrev AS away_team_abbrev,
    p.full_name AS player_name,
    p."position" AS player_position,
    p.team_id AS player_team_id,
    pt.name AS player_team_name,
    pt.abbrev AS player_team_abbrev,
    b.name AS bookmaker_name,
        CASE
            WHEN (p.team_id = g.home_team_id) THEN 'home'::text
            WHEN (p.team_id = g.away_team_id) THEN 'away'::text
            ELSE 'unknown'::text
        END AS player_home_away,
        CASE
            WHEN (p.team_id = g.home_team_id) THEN at.name
            WHEN (p.team_id = g.away_team_id) THEN ht.name
            ELSE NULL::text
        END AS opponent_name,
        CASE
            WHEN (p.team_id = g.home_team_id) THEN at.abbrev
            WHEN (p.team_id = g.away_team_id) THEN ht.abbrev
            ELSE NULL::text
        END AS opponent_abbrev,
        CASE
            WHEN (po.odds_american > 0) THEN round((((po.odds_american)::numeric / 100.0) + (1)::numeric), 3)
            ELSE round(((100.0 / (abs(po.odds_american))::numeric) + (1)::numeric), 3)
        END AS odds_decimal,
        CASE
            WHEN (po.odds_american > 0) THEN round(((100.0 / ((po.odds_american)::numeric + 100.0)) * (100)::numeric), 2)
            ELSE round((((abs(po.odds_american))::numeric / ((abs(po.odds_american))::numeric + 100.0)) * (100)::numeric), 2)
        END AS implied_probability_pct
   FROM (((((((public.player_odds po
     JOIN public.game g ON ((po.game_id = g.game_id)))
     JOIN public.season s ON ((g.season_id = s.season_id)))
     JOIN public.team ht ON ((g.home_team_id = ht.team_id)))
     JOIN public.team at ON ((g.away_team_id = at.team_id)))
     JOIN public.player p ON ((po.player_id = p.player_id)))
     LEFT JOIN public.team pt ON ((p.team_id = pt.team_id)))
     JOIN public.book b ON ((po.book_id = b.book_id)));


--
-- Name: VIEW v_player_odds_detailed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_odds_detailed IS 'Comprehensive player odds view with all common joins and derived fields. Use for most queries.';


--
-- Name: v_player_over_under_record; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_over_under_record AS
 WITH player_results AS (
         SELECT p.player_id,
            p.full_name AS player_name,
            p."position",
            po.market_key,
            s.year AS season_year,
            g.game_id,
            g.week,
            avg(po.line_value) AS line_value,
            (gps.metric_value)::numeric AS actual_result,
                CASE
                    WHEN ((gps.metric_value)::numeric > avg(po.line_value)) THEN 'over'::text
                    WHEN ((gps.metric_value)::numeric < avg(po.line_value)) THEN 'under'::text
                    WHEN ((gps.metric_value)::numeric = avg(po.line_value)) THEN 'push'::text
                    ELSE NULL::text
                END AS result
           FROM ((((public.player p
             JOIN public.player_odds po ON ((p.player_id = po.player_id)))
             JOIN public.game g ON ((po.game_id = g.game_id)))
             JOIN public.season s ON ((g.season_id = s.season_id)))
             LEFT JOIN public.game_player_statistics gps ON (((po.game_id = gps.game_id) AND (po.player_id = gps.player_id) AND (((po.market_key = 'player_pass_yds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_pass_tds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'touchdowns'::text)) OR ((po.market_key = 'player_rush_yds'::text) AND (gps.stat_group = 'Rushing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_reception_yds'::text) AND (gps.stat_group = 'Receiving'::text) AND (gps.metric_name = 'yards'::text))))))
          GROUP BY p.player_id, p.full_name, p."position", po.market_key, s.year, g.game_id, g.week, gps.metric_value
        )
 SELECT player_id,
    player_name,
    "position",
    market_key,
    season_year,
    count(*) FILTER (WHERE (result IS NOT NULL)) AS games_with_result,
    count(*) FILTER (WHERE (result = 'over'::text)) AS times_hit_over,
    count(*) FILTER (WHERE (result = 'under'::text)) AS times_hit_under,
    count(*) FILTER (WHERE (result = 'push'::text)) AS times_push,
    round((((count(*) FILTER (WHERE (result = 'over'::text)))::numeric / (NULLIF(count(*) FILTER (WHERE (result = ANY (ARRAY['over'::text, 'under'::text]))), 0))::numeric) * (100)::numeric), 1) AS over_percentage,
    round(avg((actual_result - line_value)), 2) AS avg_diff_from_line,
    string_agg(
        CASE result
            WHEN 'over'::text THEN 'O'::text
            WHEN 'under'::text THEN 'U'::text
            WHEN 'push'::text THEN 'P'::text
            ELSE '-'::text
        END, ''::text ORDER BY week DESC) FILTER (WHERE (week >= ( SELECT (max(pr.week) - 4)
           FROM player_results pr
          WHERE ((pr.player_id = player_results.player_id) AND (pr.season_year = player_results.season_year))))) AS last_5_games_trend,
    round(avg(line_value), 2) AS avg_line,
    round(avg(actual_result), 2) AS avg_actual,
    min(actual_result) AS min_actual,
    max(actual_result) AS max_actual
   FROM player_results
  WHERE (result IS NOT NULL)
  GROUP BY player_id, player_name, "position", market_key, season_year;


--
-- Name: VIEW v_player_over_under_record; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_over_under_record IS 'Player over/under hit rates and performance vs betting lines by season and market.';


--
-- Name: v_player_prop_streaks; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_prop_streaks AS
 WITH game_results AS (
         SELECT p.player_id,
            p.full_name AS player_name,
            p."position",
            po.market_key,
            g.game_id,
            g.week,
            s.year AS season_year,
            g.game_datetime_utc,
            avg(po.line_value) AS line_value,
            (gps.metric_value)::numeric AS actual_result,
                CASE
                    WHEN ((gps.metric_value)::numeric > avg(po.line_value)) THEN 1
                    WHEN ((gps.metric_value)::numeric < avg(po.line_value)) THEN '-1'::integer
                    ELSE 0
                END AS result_code
           FROM ((((public.player p
             JOIN public.player_odds po ON ((p.player_id = po.player_id)))
             JOIN public.game g ON ((po.game_id = g.game_id)))
             JOIN public.season s ON ((g.season_id = s.season_id)))
             LEFT JOIN public.game_player_statistics gps ON (((po.game_id = gps.game_id) AND (po.player_id = gps.player_id) AND (((po.market_key = 'player_pass_yds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_pass_tds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'touchdowns'::text)) OR ((po.market_key = 'player_rush_yds'::text) AND (gps.stat_group = 'Rushing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_reception_yds'::text) AND (gps.stat_group = 'Receiving'::text) AND (gps.metric_name = 'yards'::text))))))
          WHERE (gps.metric_value IS NOT NULL)
          GROUP BY p.player_id, p.full_name, p."position", po.market_key, g.game_id, g.week, s.year, g.game_datetime_utc, gps.metric_value
        ), game_results_with_lag AS (
         SELECT game_results.player_id,
            game_results.player_name,
            game_results."position",
            game_results.market_key,
            game_results.game_id,
            game_results.week,
            game_results.season_year,
            game_results.game_datetime_utc,
            game_results.line_value,
            game_results.actual_result,
            game_results.result_code,
            lag(game_results.result_code, 1, 0) OVER (PARTITION BY game_results.player_id, game_results.market_key, game_results.season_year ORDER BY game_results.week) AS prev_result_code
           FROM game_results
        ), streak_changes AS (
         SELECT game_results_with_lag.player_id,
            game_results_with_lag.player_name,
            game_results_with_lag."position",
            game_results_with_lag.market_key,
            game_results_with_lag.game_id,
            game_results_with_lag.week,
            game_results_with_lag.season_year,
            game_results_with_lag.game_datetime_utc,
            game_results_with_lag.line_value,
            game_results_with_lag.actual_result,
            game_results_with_lag.result_code,
            game_results_with_lag.prev_result_code,
                CASE
                    WHEN (game_results_with_lag.result_code <> game_results_with_lag.prev_result_code) THEN 1
                    ELSE 0
                END AS is_new_streak
           FROM game_results_with_lag
        ), streaks AS (
         SELECT streak_changes.player_id,
            streak_changes.player_name,
            streak_changes."position",
            streak_changes.market_key,
            streak_changes.season_year,
            streak_changes.game_id,
            streak_changes.week,
            streak_changes.result_code,
            sum(streak_changes.is_new_streak) OVER (PARTITION BY streak_changes.player_id, streak_changes.market_key, streak_changes.season_year ORDER BY streak_changes.week) AS streak_group
           FROM streak_changes
        )
 SELECT player_id,
    player_name,
    "position",
    market_key,
    season_year,
        CASE
            WHEN (result_code = 1) THEN 'over'::text
            WHEN (result_code = '-1'::integer) THEN 'under'::text
            ELSE 'push'::text
        END AS current_streak_type,
    count(*) AS current_streak_length,
    max(week) AS most_recent_week,
    ( SELECT count(*) AS count
           FROM streaks s2
          WHERE ((s2.player_id = streaks.player_id) AND (s2.market_key = streaks.market_key) AND (s2.season_year = streaks.season_year) AND (s2.result_code = 1))
          GROUP BY s2.streak_group
          ORDER BY (count(*)) DESC
         LIMIT 1) AS longest_over_streak,
    ( SELECT count(*) AS count
           FROM streaks s2
          WHERE ((s2.player_id = streaks.player_id) AND (s2.market_key = streaks.market_key) AND (s2.season_year = streaks.season_year) AND (s2.result_code = '-1'::integer))
          GROUP BY s2.streak_group
          ORDER BY (count(*)) DESC
         LIMIT 1) AS longest_under_streak
   FROM streaks
  WHERE (streak_group = ( SELECT max(s2.streak_group) AS max
           FROM streaks s2
          WHERE ((s2.player_id = streaks.player_id) AND (s2.market_key = streaks.market_key) AND (s2.season_year = streaks.season_year))))
  GROUP BY player_id, player_name, "position", market_key, season_year, result_code;


--
-- Name: VIEW v_player_prop_streaks; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_prop_streaks IS 'Tracks player hot and cold streaks relative to their prop lines.';


--
-- Name: v_player_props_history; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_player_props_history AS
 SELECT p.player_id,
    p.full_name AS player_name,
    p."position",
    pt.abbrev AS player_team,
    po.market_key,
    g.game_id,
    g.week,
    s.year AS season_year,
    g.game_datetime_utc,
        CASE
            WHEN (p.team_id = g.home_team_id) THEN at.name
            ELSE ht.name
        END AS opponent,
        CASE
            WHEN (p.team_id = g.home_team_id) THEN 'home'::text
            ELSE 'away'::text
        END AS home_away,
    round(avg(po.line_value), 2) AS avg_line,
    min(po.line_value) AS min_line,
    max(po.line_value) AS max_line,
    count(DISTINCT po.book_id) AS num_books,
    (gps.metric_value)::numeric AS actual_result,
        CASE
            WHEN ((gps.metric_value IS NOT NULL) AND (avg(po.line_value) IS NOT NULL)) THEN
            CASE
                WHEN ((gps.metric_value)::numeric > avg(po.line_value)) THEN 'over'::text
                WHEN ((gps.metric_value)::numeric < avg(po.line_value)) THEN 'under'::text
                ELSE 'push'::text
            END
            ELSE NULL::text
        END AS result_vs_line
   FROM (((((((public.player p
     LEFT JOIN public.team pt ON ((p.team_id = pt.team_id)))
     JOIN public.player_odds po ON ((p.player_id = po.player_id)))
     JOIN public.game g ON ((po.game_id = g.game_id)))
     JOIN public.season s ON ((g.season_id = s.season_id)))
     JOIN public.team ht ON ((g.home_team_id = ht.team_id)))
     JOIN public.team at ON ((g.away_team_id = at.team_id)))
     LEFT JOIN public.game_player_statistics gps ON (((po.game_id = gps.game_id) AND (po.player_id = gps.player_id) AND (((po.market_key = 'player_pass_yds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_pass_tds'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'touchdowns'::text)) OR ((po.market_key = 'player_pass_completions'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'completions'::text)) OR ((po.market_key = 'player_pass_attempts'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'attempts'::text)) OR ((po.market_key = 'player_pass_interceptions'::text) AND (gps.stat_group = 'Passing'::text) AND (gps.metric_name = 'interceptions'::text)) OR ((po.market_key = 'player_rush_yds'::text) AND (gps.stat_group = 'Rushing'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_rush_attempts'::text) AND (gps.stat_group = 'Rushing'::text) AND (gps.metric_name = 'attempts'::text)) OR ((po.market_key = 'player_reception_yds'::text) AND (gps.stat_group = 'Receiving'::text) AND (gps.metric_name = 'yards'::text)) OR ((po.market_key = 'player_receptions'::text) AND (gps.stat_group = 'Receiving'::text) AND (gps.metric_name = 'receptions'::text))))))
  GROUP BY p.player_id, p.full_name, p."position", pt.abbrev, po.market_key, g.game_id, g.week, s.year, g.game_datetime_utc, p.team_id, g.home_team_id, at.name, ht.name, gps.metric_value
  ORDER BY p.player_id, g.game_datetime_utc;


--
-- Name: VIEW v_player_props_history; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_player_props_history IS 'Historical prop lines with actual game results for trend analysis and hit rate tracking.';


--
-- Name: v_recent_bets; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_recent_bets AS
 SELECT b.bet_id,
    b.user_id,
    b.account_id,
    ba.bookmaker_name,
    b.bet_type,
    b.sport,
    b.player_id,
    p.full_name AS player_name,
    p."position" AS player_position,
    p.image_url AS player_image_url,
    b.game_id,
    b.market_key,
    b.bet_side,
    b.line_value,
    b.odds_american,
    b.stake_amount,
    b.potential_payout,
    b.actual_payout,
    b.profit_loss,
    b.status,
    b.placed_at,
    b.settled_at,
    b.notes
   FROM ((public.bets b
     LEFT JOIN public.bankroll_accounts ba ON ((b.account_id = ba.account_id)))
     LEFT JOIN public.player p ON ((b.player_id = p.player_id)))
  ORDER BY b.placed_at DESC;


--
-- Name: v_sharp_line_movement; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_sharp_line_movement AS
 WITH line_changes AS (
         SELECT po.game_id,
            po.player_id,
            p.full_name AS player_name,
            po.market_key,
            po.bet_type,
            g.game_datetime_utc,
            avg(po.line_value) AS current_line,
            ( SELECT avg(po2.line_value) AS avg
                   FROM public.player_odds po2
                  WHERE ((po2.game_id = po.game_id) AND (po2.player_id = po.player_id) AND (po2.market_key = po.market_key) AND (po2.bet_type = po.bet_type) AND (po2.pulled_at_utc = ( SELECT min(po3.pulled_at_utc) AS min
                           FROM public.player_odds po3
                          WHERE ((po3.game_id = po.game_id) AND (po3.player_id = po.player_id) AND (po3.market_key = po.market_key) AND (po3.bet_type = po.bet_type)))))) AS opening_line,
            count(DISTINCT po.book_id) AS num_books,
            min(po.pulled_at_utc) AS first_pull,
            max(po.pulled_at_utc) AS last_pull
           FROM ((public.player_odds po
             JOIN public.player p ON ((po.player_id = p.player_id)))
             JOIN public.game g ON ((po.game_id = g.game_id)))
          GROUP BY po.game_id, po.player_id, p.full_name, po.market_key, po.bet_type, g.game_datetime_utc
        )
 SELECT game_id,
    player_id,
    player_name,
    market_key,
    bet_type,
    game_datetime_utc,
    opening_line,
    current_line,
    round((current_line - opening_line), 2) AS line_movement,
    round((((current_line - opening_line) / NULLIF(opening_line, (0)::numeric)) * (100)::numeric), 1) AS line_movement_pct,
    num_books,
        CASE
            WHEN (abs((current_line - opening_line)) >= (10)::numeric) THEN 'major'::text
            WHEN (abs((current_line - opening_line)) >= (5)::numeric) THEN 'significant'::text
            WHEN (abs((current_line - opening_line)) >= (2)::numeric) THEN 'moderate'::text
            ELSE 'minor'::text
        END AS movement_magnitude,
        CASE
            WHEN (current_line > opening_line) THEN 'up'::text
            WHEN (current_line < opening_line) THEN 'down'::text
            ELSE 'stable'::text
        END AS movement_direction,
    first_pull,
    last_pull
   FROM line_changes
  WHERE ((opening_line IS NOT NULL) AND (current_line IS NOT NULL) AND (opening_line <> current_line));


--
-- Name: VIEW v_sharp_line_movement; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.v_sharp_line_movement IS 'Detects line movements that may indicate sharp money or injury news.';


--
-- Name: v_unread_alerts; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_unread_alerts AS
 SELECT alert_id,
    user_id,
    alert_type,
    severity,
    message,
    related_bet_id,
    related_goal_id,
    created_at
   FROM public.user_alerts
  WHERE (is_read = false)
  ORDER BY created_at DESC;


--
-- Name: v_user_activity; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_user_activity AS
SELECT
    NULL::integer AS user_id,
    NULL::character varying(255) AS email,
    NULL::character varying(50) AS username,
    NULL::bigint AS bets_last_7_days,
    NULL::bigint AS bets_last_30_days,
    NULL::numeric AS staked_last_7_days,
    NULL::numeric AS profit_last_7_days,
    NULL::bigint AS unread_alerts,
    NULL::timestamp without time zone AS last_bet_placed,
    NULL::timestamp without time zone AS last_login_at;


--
-- Name: v_user_profile; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_user_profile AS
SELECT
    NULL::integer AS user_id,
    NULL::character varying(255) AS email,
    NULL::character varying(50) AS username,
    NULL::character varying(100) AS first_name,
    NULL::character varying(100) AS last_name,
    NULL::character varying(100) AS display_name,
    NULL::boolean AS is_active,
    NULL::boolean AS is_verified,
    NULL::character varying(50) AS timezone,
    NULL::character varying(3) AS currency,
    NULL::timestamp without time zone AS last_login_at,
    NULL::timestamp without time zone AS created_at,
    NULL::bigint AS num_bankroll_accounts,
    NULL::bigint AS total_bets,
    NULL::bigint AS active_goals,
    NULL::numeric AS total_bankroll,
    NULL::numeric AS lifetime_profit,
    NULL::timestamp without time zone AS last_bet_date;


--
-- Name: v_user_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_user_statistics AS
SELECT
    NULL::integer AS user_id,
    NULL::character varying(255) AS email,
    NULL::bigint AS total_bets,
    NULL::bigint AS bets_won,
    NULL::bigint AS bets_lost,
    NULL::bigint AS bets_push,
    NULL::bigint AS bets_pending,
    NULL::numeric AS win_rate_percentage,
    NULL::numeric AS total_staked,
    NULL::numeric AS total_profit,
    NULL::numeric AS avg_profit_per_bet,
    NULL::numeric AS roi_percentage,
    NULL::bigint AS total_parlays,
    NULL::bigint AS parlays_won,
    NULL::bigint AS total_goals,
    NULL::bigint AS goals_completed,
    NULL::bigint AS goals_active;


--
-- Name: venue; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.venue (
    venue_id smallint NOT NULL,
    name text NOT NULL,
    city text NOT NULL,
    state text NOT NULL,
    is_dome boolean DEFAULT false NOT NULL,
    surface text
);


--
-- Name: venue_venue_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.venue_venue_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: venue_venue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.venue_venue_id_seq OWNED BY public.venue.venue_id;


--
-- Name: weather_observation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_observation (
    obs_id bigint NOT NULL,
    game_id bigint NOT NULL,
    temp_f numeric(5,2),
    wind_mph numeric(5,2),
    precip_prob numeric(5,2),
    conditions text,
    observed_at_utc timestamp with time zone NOT NULL,
    source text,
    temp_c numeric(5,2),
    is_cold boolean,
    is_hot boolean,
    is_windy boolean,
    is_heavy_wind boolean,
    is_rain_risk boolean,
    is_storm_risk boolean,
    weather_severity_score smallint,
    precip_mm numeric,
    CONSTRAINT chk_weather_severity_score CHECK (((weather_severity_score IS NULL) OR ((weather_severity_score >= 0) AND (weather_severity_score <= 100)))),
    CONSTRAINT chk_weather_temp_f CHECK (((temp_f IS NULL) OR ((temp_f > ('-40'::integer)::numeric) AND (temp_f < (130)::numeric)))),
    CONSTRAINT weather_observation_precip_prob_check CHECK (((precip_prob IS NULL) OR ((precip_prob >= (0)::numeric) AND (precip_prob <= (100)::numeric))))
);


--
-- Name: weather_observation_obs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weather_observation_obs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weather_observation_obs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weather_observation_obs_id_seq OWNED BY public.weather_observation.obs_id;


--
-- Name: bankroll_accounts account_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_accounts ALTER COLUMN account_id SET DEFAULT nextval('public.bankroll_accounts_account_id_seq'::regclass);


--
-- Name: bankroll_settings settings_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_settings ALTER COLUMN settings_id SET DEFAULT nextval('public.bankroll_settings_settings_id_seq'::regclass);


--
-- Name: bankroll_transactions transaction_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_transactions ALTER COLUMN transaction_id SET DEFAULT nextval('public.bankroll_transactions_transaction_id_seq'::regclass);


--
-- Name: bets bet_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets ALTER COLUMN bet_id SET DEFAULT nextval('public.bets_bet_id_seq'::regclass);


--
-- Name: book book_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.book ALTER COLUMN book_id SET DEFAULT nextval('public.book_book_id_seq'::regclass);


--
-- Name: game game_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game ALTER COLUMN game_id SET DEFAULT nextval('public.game_game_id_seq'::regclass);


--
-- Name: game_player_statistics stat_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics ALTER COLUMN stat_id SET DEFAULT nextval('public.game_player_statistics_stat_id_seq'::regclass);


--
-- Name: game_team_statistics stat_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_team_statistics ALTER COLUMN stat_id SET DEFAULT nextval('public.game_team_statistics_stat_id_seq'::regclass);


--
-- Name: injury_report report_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report ALTER COLUMN report_id SET DEFAULT nextval('public.injury_report_report_id_seq'::regclass);


--
-- Name: league league_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league ALTER COLUMN league_id SET DEFAULT nextval('public.league_league_id_seq'::regclass);


--
-- Name: odds_line line_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.odds_line ALTER COLUMN line_id SET DEFAULT nextval('public.odds_line_line_id_seq'::regclass);


--
-- Name: parlay_bets parlay_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parlay_bets ALTER COLUMN parlay_id SET DEFAULT nextval('public.parlay_bets_parlay_id_seq'::regclass);


--
-- Name: player player_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player ALTER COLUMN player_id SET DEFAULT nextval('public.player_player_id_seq'::regclass);


--
-- Name: player_odds odds_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds ALTER COLUMN odds_id SET DEFAULT nextval('public.player_odds_odds_id_seq'::regclass);


--
-- Name: player_statistic statistic_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic ALTER COLUMN statistic_id SET DEFAULT nextval('public.player_statistic_statistic_id_seq'::regclass);


--
-- Name: season season_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.season ALTER COLUMN season_id SET DEFAULT nextval('public.season_season_id_seq'::regclass);


--
-- Name: sport_position position_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_position ALTER COLUMN position_id SET DEFAULT nextval('public.sport_position_position_id_seq'::regclass);


--
-- Name: sport_stat_type stat_type_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_stat_type ALTER COLUMN stat_type_id SET DEFAULT nextval('public.sport_stat_type_stat_type_id_seq'::regclass);


--
-- Name: sport_type sport_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_type ALTER COLUMN sport_id SET DEFAULT nextval('public.sport_type_sport_id_seq'::regclass);


--
-- Name: team team_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team ALTER COLUMN team_id SET DEFAULT nextval('public.team_team_id_seq'::regclass);


--
-- Name: user_account user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account ALTER COLUMN user_id SET DEFAULT nextval('public.user_account_user_id_seq'::regclass);


--
-- Name: user_alerts alert_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_alerts ALTER COLUMN alert_id SET DEFAULT nextval('public.user_alerts_alert_id_seq'::regclass);


--
-- Name: user_goals goal_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals ALTER COLUMN goal_id SET DEFAULT nextval('public.user_goals_goal_id_seq'::regclass);


--
-- Name: venue venue_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.venue ALTER COLUMN venue_id SET DEFAULT nextval('public.venue_venue_id_seq'::regclass);


--
-- Name: weather_observation obs_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observation ALTER COLUMN obs_id SET DEFAULT nextval('public.weather_observation_obs_id_seq'::regclass);


--
-- Name: bankroll_accounts bankroll_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_accounts
    ADD CONSTRAINT bankroll_accounts_pkey PRIMARY KEY (account_id);


--
-- Name: bankroll_settings bankroll_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_settings
    ADD CONSTRAINT bankroll_settings_pkey PRIMARY KEY (settings_id);


--
-- Name: bankroll_settings bankroll_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_settings
    ADD CONSTRAINT bankroll_settings_user_id_key UNIQUE (user_id);


--
-- Name: bankroll_transactions bankroll_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_transactions
    ADD CONSTRAINT bankroll_transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: bets bets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_pkey PRIMARY KEY (bet_id);


--
-- Name: book book_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.book
    ADD CONSTRAINT book_name_key UNIQUE (name);


--
-- Name: book book_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.book
    ADD CONSTRAINT book_pkey PRIMARY KEY (book_id);


--
-- Name: game game_external_game_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_external_game_key_key UNIQUE (external_game_key);


--
-- Name: game game_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_pkey PRIMARY KEY (game_id);


--
-- Name: game_player_statistics game_player_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics
    ADD CONSTRAINT game_player_statistics_pkey PRIMARY KEY (stat_id);


--
-- Name: game_result game_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_result
    ADD CONSTRAINT game_result_pkey PRIMARY KEY (game_id);


--
-- Name: game_team_statistics game_team_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_team_statistics
    ADD CONSTRAINT game_team_statistics_pkey PRIMARY KEY (stat_id);


--
-- Name: injury_report injury_report_game_id_player_id_updated_at_utc_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report
    ADD CONSTRAINT injury_report_game_id_player_id_updated_at_utc_key UNIQUE (game_id, player_id, updated_at_utc);


--
-- Name: injury_report injury_report_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report
    ADD CONSTRAINT injury_report_pkey PRIMARY KEY (report_id);


--
-- Name: league league_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league
    ADD CONSTRAINT league_name_key UNIQUE (name);


--
-- Name: league league_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.league
    ADD CONSTRAINT league_pkey PRIMARY KEY (league_id);


--
-- Name: odds_line odds_line_game_id_book_id_market_side_pulled_at_utc_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.odds_line
    ADD CONSTRAINT odds_line_game_id_book_id_market_side_pulled_at_utc_key UNIQUE (game_id, book_id, market, side, pulled_at_utc);


--
-- Name: odds_line odds_line_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.odds_line
    ADD CONSTRAINT odds_line_pkey PRIMARY KEY (line_id);


--
-- Name: parlay_bets parlay_bets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parlay_bets
    ADD CONSTRAINT parlay_bets_pkey PRIMARY KEY (parlay_id);


--
-- Name: player player_external_player_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player
    ADD CONSTRAINT player_external_player_id_key UNIQUE (external_player_id);


--
-- Name: player_odds player_odds_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds
    ADD CONSTRAINT player_odds_pkey PRIMARY KEY (odds_id);


--
-- Name: player player_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player
    ADD CONSTRAINT player_pkey PRIMARY KEY (player_id);


--
-- Name: player_statistic player_statistic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic
    ADD CONSTRAINT player_statistic_pkey PRIMARY KEY (statistic_id);


--
-- Name: player_statistic player_statistic_player_id_team_id_season_id_stat_group_met_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic
    ADD CONSTRAINT player_statistic_player_id_team_id_season_id_stat_group_met_key UNIQUE (player_id, team_id, season_id, stat_group, metric_name);


--
-- Name: season season_league_id_year_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.season
    ADD CONSTRAINT season_league_id_year_key UNIQUE (league_id, year);


--
-- Name: season season_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.season
    ADD CONSTRAINT season_pkey PRIMARY KEY (season_id);


--
-- Name: sport_position sport_position_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_position
    ADD CONSTRAINT sport_position_pkey PRIMARY KEY (position_id);


--
-- Name: sport_position sport_position_sport_id_position_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_position
    ADD CONSTRAINT sport_position_sport_id_position_code_key UNIQUE (sport_id, position_code);


--
-- Name: sport_stat_type sport_stat_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_stat_type
    ADD CONSTRAINT sport_stat_type_pkey PRIMARY KEY (stat_type_id);


--
-- Name: sport_stat_type sport_stat_type_sport_id_stat_group_metric_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_stat_type
    ADD CONSTRAINT sport_stat_type_sport_id_stat_group_metric_name_key UNIQUE (sport_id, stat_group, metric_name);


--
-- Name: sport_type sport_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_type
    ADD CONSTRAINT sport_type_pkey PRIMARY KEY (sport_id);


--
-- Name: sport_type sport_type_sport_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_type
    ADD CONSTRAINT sport_type_sport_code_key UNIQUE (sport_code);


--
-- Name: team team_external_team_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT team_external_team_key_key UNIQUE (external_team_key);


--
-- Name: team_game_stat team_game_stat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_game_stat
    ADD CONSTRAINT team_game_stat_pkey PRIMARY KEY (game_id, team_id, metric);


--
-- Name: team team_league_id_abbrev_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT team_league_id_abbrev_key UNIQUE (league_id, abbrev);


--
-- Name: team team_league_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT team_league_id_name_key UNIQUE (league_id, name);


--
-- Name: team team_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT team_pkey PRIMARY KEY (team_id);


--
-- Name: game_player_statistics uq_game_player_stat; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics
    ADD CONSTRAINT uq_game_player_stat UNIQUE (game_id, player_id, team_id, stat_group, metric_name);


--
-- Name: game_team_statistics uq_game_team_stat; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_team_statistics
    ADD CONSTRAINT uq_game_team_stat UNIQUE (game_id, team_id);


--
-- Name: player_odds uq_player_odds_snapshot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds
    ADD CONSTRAINT uq_player_odds_snapshot UNIQUE (game_id, player_id, book_id, market_key, bet_type, pulled_at_utc);


--
-- Name: venue uq_venue_name_city_state; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.venue
    ADD CONSTRAINT uq_venue_name_city_state UNIQUE (name, city, state);


--
-- Name: user_account user_account_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_email_key UNIQUE (email);


--
-- Name: user_account user_account_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_pkey PRIMARY KEY (user_id);


--
-- Name: user_account user_account_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_username_key UNIQUE (username);


--
-- Name: user_alerts user_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT user_alerts_pkey PRIMARY KEY (alert_id);


--
-- Name: user_goals user_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT user_goals_pkey PRIMARY KEY (goal_id);


--
-- Name: venue venue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.venue
    ADD CONSTRAINT venue_pkey PRIMARY KEY (venue_id);


--
-- Name: weather_observation weather_observation_game_id_observed_at_utc_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observation
    ADD CONSTRAINT weather_observation_game_id_observed_at_utc_key UNIQUE (game_id, observed_at_utc);


--
-- Name: weather_observation weather_observation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observation
    ADD CONSTRAINT weather_observation_pkey PRIMARY KEY (obs_id);


--
-- Name: idx_bankroll_accounts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bankroll_accounts_user_id ON public.bankroll_accounts USING btree (user_id);


--
-- Name: idx_bankroll_settings_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bankroll_settings_user_id ON public.bankroll_settings USING btree (user_id);


--
-- Name: idx_bets_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_account_id ON public.bets USING btree (account_id);


--
-- Name: idx_bets_bet_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_bet_type ON public.bets USING btree (bet_type);


--
-- Name: idx_bets_game_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_game_id ON public.bets USING btree (game_id);


--
-- Name: idx_bets_market_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_market_key ON public.bets USING btree (market_key);


--
-- Name: idx_bets_parlay_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_parlay_id ON public.bets USING btree (parlay_id);


--
-- Name: idx_bets_placed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_placed_at ON public.bets USING btree (placed_at DESC);


--
-- Name: idx_bets_player_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_player_id ON public.bets USING btree (player_id);


--
-- Name: idx_bets_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_sport_id ON public.bets USING btree (sport_id);


--
-- Name: idx_bets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_status ON public.bets USING btree (status);


--
-- Name: idx_bets_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bets_user_id ON public.bets USING btree (user_id);


--
-- Name: idx_game_away_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_away_team ON public.game USING btree (away_team_id);


--
-- Name: idx_game_datetime; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_datetime ON public.game USING btree (game_datetime_utc);


--
-- Name: idx_game_home_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_home_team ON public.game USING btree (home_team_id);


--
-- Name: idx_game_player_stat_game; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_game ON public.game_player_statistics USING btree (game_id);


--
-- Name: idx_game_player_stat_game_player; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_game_player ON public.game_player_statistics USING btree (game_id, player_id);


--
-- Name: idx_game_player_stat_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_group ON public.game_player_statistics USING btree (stat_group);


--
-- Name: idx_game_player_stat_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_metric ON public.game_player_statistics USING btree (metric_name);


--
-- Name: idx_game_player_stat_player; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_player ON public.game_player_statistics USING btree (player_id);


--
-- Name: idx_game_player_stat_player_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_player_group ON public.game_player_statistics USING btree (player_id, stat_group);


--
-- Name: idx_game_player_stat_pulled_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_pulled_at ON public.game_player_statistics USING btree (pulled_at_utc);


--
-- Name: idx_game_player_stat_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_player_stat_team ON public.game_player_statistics USING btree (team_id);


--
-- Name: idx_game_season_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_season_week ON public.game USING btree (season_id, week);


--
-- Name: idx_game_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_sport_id ON public.game USING btree (sport_id);


--
-- Name: idx_game_team_stat_game; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_team_stat_game ON public.game_team_statistics USING btree (game_id);


--
-- Name: idx_game_team_stat_game_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_team_stat_game_team ON public.game_team_statistics USING btree (game_id, team_id);


--
-- Name: idx_game_team_stat_pulled_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_team_stat_pulled_at ON public.game_team_statistics USING btree (pulled_at_utc);


--
-- Name: idx_game_team_stat_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_game_team_stat_team ON public.game_team_statistics USING btree (team_id);


--
-- Name: idx_injury_game_team_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_injury_game_team_time ON public.injury_report USING btree (game_id, team_id, updated_at_utc);


--
-- Name: idx_injury_player_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_injury_player_time ON public.injury_report USING btree (player_id, updated_at_utc);


--
-- Name: idx_league_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_league_code ON public.league USING btree (league_code);


--
-- Name: idx_league_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_league_sport_id ON public.league USING btree (sport_id);


--
-- Name: idx_odds_book_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_odds_book_time ON public.odds_line USING btree (book_id, pulled_at_utc);


--
-- Name: idx_odds_game_market_side_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_odds_game_market_side_time ON public.odds_line USING btree (game_id, market, side, pulled_at_utc);


--
-- Name: idx_parlay_bets_placed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parlay_bets_placed_at ON public.parlay_bets USING btree (placed_at DESC);


--
-- Name: idx_parlay_bets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parlay_bets_status ON public.parlay_bets USING btree (status);


--
-- Name: idx_parlay_bets_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parlay_bets_user_id ON public.parlay_bets USING btree (user_id);


--
-- Name: idx_player_odds_book; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_book ON public.player_odds USING btree (book_id);


--
-- Name: idx_player_odds_composite; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_composite ON public.player_odds USING btree (game_id, player_id, market_key);


--
-- Name: idx_player_odds_game; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_game ON public.player_odds USING btree (game_id);


--
-- Name: idx_player_odds_market; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_market ON public.player_odds USING btree (market_key);


--
-- Name: idx_player_odds_player; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_player ON public.player_odds USING btree (player_id);


--
-- Name: idx_player_odds_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_odds_time ON public.player_odds USING btree (pulled_at_utc);


--
-- Name: idx_player_position_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_position_id ON public.player USING btree (position_id);


--
-- Name: idx_player_season_summary_player; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_season_summary_player ON public.player_season_summary USING btree (player_id);


--
-- Name: idx_player_season_summary_season; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_season_summary_season ON public.player_season_summary USING btree (season_id);


--
-- Name: idx_player_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_sport_id ON public.player USING btree (sport_id);


--
-- Name: idx_player_stat_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_group ON public.player_statistic USING btree (stat_group);


--
-- Name: idx_player_stat_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_metric ON public.player_statistic USING btree (metric_name);


--
-- Name: idx_player_stat_player; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_player ON public.player_statistic USING btree (player_id);


--
-- Name: idx_player_stat_player_season_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_player_season_group ON public.player_statistic USING btree (player_id, season_id, stat_group);


--
-- Name: idx_player_stat_season; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_season ON public.player_statistic USING btree (season_id);


--
-- Name: idx_player_stat_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_player_stat_team ON public.player_statistic USING btree (team_id);


--
-- Name: idx_sport_position_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_position_code ON public.sport_position USING btree (position_code);


--
-- Name: idx_sport_position_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_position_group ON public.sport_position USING btree (position_group);


--
-- Name: idx_sport_position_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_position_sport_id ON public.sport_position USING btree (sport_id);


--
-- Name: idx_sport_stat_type_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_stat_type_code ON public.sport_stat_type USING btree (metric_code);


--
-- Name: idx_sport_stat_type_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_stat_type_group ON public.sport_stat_type USING btree (stat_group);


--
-- Name: idx_sport_stat_type_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_stat_type_sport_id ON public.sport_stat_type USING btree (sport_id);


--
-- Name: idx_sport_type_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_type_category ON public.sport_type USING btree (sport_category);


--
-- Name: idx_sport_type_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_type_code ON public.sport_type USING btree (sport_code);


--
-- Name: idx_sport_type_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sport_type_is_active ON public.sport_type USING btree (is_active);


--
-- Name: idx_team_game_stat_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_game_stat_metric ON public.team_game_stat USING btree (metric);


--
-- Name: idx_team_game_stat_team; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_game_stat_team ON public.team_game_stat USING btree (team_id);


--
-- Name: idx_team_sport_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_sport_id ON public.team USING btree (sport_id);


--
-- Name: idx_transactions_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_account_id ON public.bankroll_transactions USING btree (account_id);


--
-- Name: idx_transactions_bet_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_bet_id ON public.bankroll_transactions USING btree (bet_id);


--
-- Name: idx_transactions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_created_at ON public.bankroll_transactions USING btree (created_at DESC);


--
-- Name: idx_transactions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_type ON public.bankroll_transactions USING btree (transaction_type);


--
-- Name: idx_transactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_user_id ON public.bankroll_transactions USING btree (user_id);


--
-- Name: idx_user_account_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_account_created_at ON public.user_account USING btree (created_at DESC);


--
-- Name: idx_user_account_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_account_email ON public.user_account USING btree (email);


--
-- Name: idx_user_account_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_account_is_active ON public.user_account USING btree (is_active);


--
-- Name: idx_user_account_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_account_username ON public.user_account USING btree (username);


--
-- Name: idx_user_alerts_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_alerts_created_at ON public.user_alerts USING btree (created_at DESC);


--
-- Name: idx_user_alerts_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_alerts_is_read ON public.user_alerts USING btree (is_read);


--
-- Name: idx_user_alerts_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_alerts_user_id ON public.user_alerts USING btree (user_id);


--
-- Name: idx_user_goals_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_goals_end_date ON public.user_goals USING btree (end_date);


--
-- Name: idx_user_goals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_goals_status ON public.user_goals USING btree (status);


--
-- Name: idx_user_goals_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_goals_user_id ON public.user_goals USING btree (user_id);


--
-- Name: idx_weather_game_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weather_game_time ON public.weather_observation USING btree (game_id, observed_at_utc);


--
-- Name: v_user_activity _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_user_activity AS
 SELECT u.user_id,
    u.email,
    u.username,
    count(b.bet_id) FILTER (WHERE (b.placed_at >= (now() - '7 days'::interval))) AS bets_last_7_days,
    count(b.bet_id) FILTER (WHERE (b.placed_at >= (now() - '30 days'::interval))) AS bets_last_30_days,
    sum(b.stake_amount) FILTER (WHERE (b.placed_at >= (now() - '7 days'::interval))) AS staked_last_7_days,
    sum(b.profit_loss) FILTER (WHERE ((b.placed_at >= (now() - '7 days'::interval)) AND ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[])))) AS profit_last_7_days,
    count(a.alert_id) FILTER (WHERE (NOT a.is_read)) AS unread_alerts,
    max(b.placed_at) AS last_bet_placed,
    u.last_login_at
   FROM ((public.user_account u
     LEFT JOIN public.bets b ON ((u.user_id = b.user_id)))
     LEFT JOIN public.user_alerts a ON ((u.user_id = a.user_id)))
  GROUP BY u.user_id;


--
-- Name: v_user_profile _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_user_profile AS
 SELECT u.user_id,
    u.email,
    u.username,
    u.first_name,
    u.last_name,
    u.display_name,
    u.is_active,
    u.is_verified,
    u.timezone,
    u.currency,
    u.last_login_at,
    u.created_at,
    count(DISTINCT ba.account_id) AS num_bankroll_accounts,
    count(DISTINCT b.bet_id) AS total_bets,
    count(DISTINCT g.goal_id) AS active_goals,
    COALESCE(sum(ba.current_balance), (0)::numeric) AS total_bankroll,
    COALESCE(sum(b.profit_loss) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))), (0)::numeric) AS lifetime_profit,
    max(b.placed_at) AS last_bet_date
   FROM (((public.user_account u
     LEFT JOIN public.bankroll_accounts ba ON ((u.user_id = ba.user_id)))
     LEFT JOIN public.bets b ON ((u.user_id = b.user_id)))
     LEFT JOIN public.user_goals g ON (((u.user_id = g.user_id) AND ((g.status)::text = 'active'::text))))
  GROUP BY u.user_id;


--
-- Name: v_user_statistics _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_user_statistics AS
 SELECT u.user_id,
    u.email,
    count(b.bet_id) AS total_bets,
    count(b.bet_id) FILTER (WHERE ((b.status)::text = 'won'::text)) AS bets_won,
    count(b.bet_id) FILTER (WHERE ((b.status)::text = 'lost'::text)) AS bets_lost,
    count(b.bet_id) FILTER (WHERE ((b.status)::text = 'push'::text)) AS bets_push,
    count(b.bet_id) FILTER (WHERE ((b.status)::text = 'pending'::text)) AS bets_pending,
    round((((count(b.bet_id) FILTER (WHERE ((b.status)::text = 'won'::text)))::numeric / (NULLIF(count(b.bet_id) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying])::text[]))), 0))::numeric) * (100)::numeric), 1) AS win_rate_percentage,
    sum(b.stake_amount) AS total_staked,
    sum(b.profit_loss) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))) AS total_profit,
    round(avg(b.profit_loss) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))), 2) AS avg_profit_per_bet,
    round(((sum(b.profit_loss) FILTER (WHERE ((b.status)::text = ANY ((ARRAY['won'::character varying, 'lost'::character varying, 'push'::character varying])::text[]))) / NULLIF(sum(b.stake_amount), (0)::numeric)) * (100)::numeric), 2) AS roi_percentage,
    count(pb.parlay_id) AS total_parlays,
    count(pb.parlay_id) FILTER (WHERE ((pb.status)::text = 'won'::text)) AS parlays_won,
    count(g.goal_id) AS total_goals,
    count(g.goal_id) FILTER (WHERE ((g.status)::text = 'completed'::text)) AS goals_completed,
    count(g.goal_id) FILTER (WHERE ((g.status)::text = 'active'::text)) AS goals_active
   FROM (((public.user_account u
     LEFT JOIN public.bets b ON ((u.user_id = b.user_id)))
     LEFT JOIN public.parlay_bets pb ON ((u.user_id = pb.user_id)))
     LEFT JOIN public.user_goals g ON ((u.user_id = g.user_id)))
  GROUP BY u.user_id;


--
-- Name: bets bet_limit_check_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER bet_limit_check_trigger AFTER INSERT ON public.bets FOR EACH ROW EXECUTE FUNCTION public.check_limits_on_bet();


--
-- Name: bankroll_accounts update_bankroll_accounts_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_bankroll_accounts_updated_at BEFORE UPDATE ON public.bankroll_accounts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: bankroll_settings update_bankroll_settings_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_bankroll_settings_updated_at BEFORE UPDATE ON public.bankroll_settings FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: bets update_bets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_bets_updated_at BEFORE UPDATE ON public.bets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: parlay_bets update_parlay_bets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_parlay_bets_updated_at BEFORE UPDATE ON public.parlay_bets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_goals update_user_goals_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_goals_updated_at BEFORE UPDATE ON public.user_goals FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: bankroll_transactions bankroll_transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_transactions
    ADD CONSTRAINT bankroll_transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.bankroll_accounts(account_id) ON DELETE CASCADE;


--
-- Name: bankroll_transactions bankroll_transactions_bet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_transactions
    ADD CONSTRAINT bankroll_transactions_bet_id_fkey FOREIGN KEY (bet_id) REFERENCES public.bets(bet_id) ON DELETE SET NULL;


--
-- Name: bets bets_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.bankroll_accounts(account_id) ON DELETE SET NULL;


--
-- Name: bets bets_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE SET NULL;


--
-- Name: bets bets_parlay_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_parlay_id_fkey FOREIGN KEY (parlay_id) REFERENCES public.parlay_bets(parlay_id) ON DELETE CASCADE;


--
-- Name: bets bets_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT bets_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(player_id) ON DELETE SET NULL;


--
-- Name: bankroll_accounts fk_bankroll_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_accounts
    ADD CONSTRAINT fk_bankroll_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: bankroll_settings fk_bankroll_settings_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_settings
    ADD CONSTRAINT fk_bankroll_settings_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: bankroll_transactions fk_bankroll_transactions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bankroll_transactions
    ADD CONSTRAINT fk_bankroll_transactions_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: bets fk_bets_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bets
    ADD CONSTRAINT fk_bets_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: parlay_bets fk_parlay_bets_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parlay_bets
    ADD CONSTRAINT fk_parlay_bets_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: user_alerts fk_user_alerts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT fk_user_alerts_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: user_goals fk_user_goals_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_goals
    ADD CONSTRAINT fk_user_goals_user_id FOREIGN KEY (user_id) REFERENCES public.user_account(user_id) ON DELETE CASCADE;


--
-- Name: game game_away_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_away_team_id_fkey FOREIGN KEY (away_team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: game game_home_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_home_team_id_fkey FOREIGN KEY (home_team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: game_player_statistics game_player_statistics_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics
    ADD CONSTRAINT game_player_statistics_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: game_player_statistics game_player_statistics_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics
    ADD CONSTRAINT game_player_statistics_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(player_id) ON DELETE CASCADE;


--
-- Name: game_player_statistics game_player_statistics_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_player_statistics
    ADD CONSTRAINT game_player_statistics_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: game_result game_result_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_result
    ADD CONSTRAINT game_result_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: game game_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.season(season_id) ON DELETE RESTRICT;


--
-- Name: game_team_statistics game_team_statistics_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_team_statistics
    ADD CONSTRAINT game_team_statistics_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: game_team_statistics game_team_statistics_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_team_statistics
    ADD CONSTRAINT game_team_statistics_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: game game_venue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game
    ADD CONSTRAINT game_venue_id_fkey FOREIGN KEY (venue_id) REFERENCES public.venue(venue_id) ON DELETE SET NULL;


--
-- Name: injury_report injury_report_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report
    ADD CONSTRAINT injury_report_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: injury_report injury_report_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report
    ADD CONSTRAINT injury_report_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(player_id) ON DELETE RESTRICT;


--
-- Name: injury_report injury_report_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.injury_report
    ADD CONSTRAINT injury_report_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: odds_line odds_line_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.odds_line
    ADD CONSTRAINT odds_line_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book(book_id) ON DELETE RESTRICT;


--
-- Name: odds_line odds_line_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.odds_line
    ADD CONSTRAINT odds_line_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: parlay_bets parlay_bets_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parlay_bets
    ADD CONSTRAINT parlay_bets_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.bankroll_accounts(account_id) ON DELETE SET NULL;


--
-- Name: player_odds player_odds_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds
    ADD CONSTRAINT player_odds_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.book(book_id) ON DELETE RESTRICT;


--
-- Name: player_odds player_odds_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds
    ADD CONSTRAINT player_odds_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: player_odds player_odds_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_odds
    ADD CONSTRAINT player_odds_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(player_id) ON DELETE CASCADE;


--
-- Name: player_statistic player_statistic_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic
    ADD CONSTRAINT player_statistic_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.player(player_id) ON DELETE CASCADE;


--
-- Name: player_statistic player_statistic_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic
    ADD CONSTRAINT player_statistic_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.season(season_id) ON DELETE RESTRICT;


--
-- Name: player_statistic player_statistic_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player_statistic
    ADD CONSTRAINT player_statistic_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: player player_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.player
    ADD CONSTRAINT player_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE SET NULL;


--
-- Name: season season_league_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.season
    ADD CONSTRAINT season_league_id_fkey FOREIGN KEY (league_id) REFERENCES public.league(league_id) ON DELETE RESTRICT;


--
-- Name: sport_position sport_position_sport_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_position
    ADD CONSTRAINT sport_position_sport_id_fkey FOREIGN KEY (sport_id) REFERENCES public.sport_type(sport_id);


--
-- Name: sport_stat_type sport_stat_type_sport_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sport_stat_type
    ADD CONSTRAINT sport_stat_type_sport_id_fkey FOREIGN KEY (sport_id) REFERENCES public.sport_type(sport_id);


--
-- Name: team_game_stat team_game_stat_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_game_stat
    ADD CONSTRAINT team_game_stat_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- Name: team_game_stat team_game_stat_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_game_stat
    ADD CONSTRAINT team_game_stat_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.team(team_id) ON DELETE RESTRICT;


--
-- Name: team team_league_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team
    ADD CONSTRAINT team_league_id_fkey FOREIGN KEY (league_id) REFERENCES public.league(league_id) ON DELETE RESTRICT;


--
-- Name: user_alerts user_alerts_related_bet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT user_alerts_related_bet_id_fkey FOREIGN KEY (related_bet_id) REFERENCES public.bets(bet_id) ON DELETE SET NULL;


--
-- Name: user_alerts user_alerts_related_goal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT user_alerts_related_goal_id_fkey FOREIGN KEY (related_goal_id) REFERENCES public.user_goals(goal_id) ON DELETE SET NULL;


--
-- Name: weather_observation weather_observation_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observation
    ADD CONSTRAINT weather_observation_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.game(game_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 38ANcb9yNkl2XbKCNxvaFhvtcA9EVxsluJyadA5U4qlMxb0chvCdY2B61MPTxzY

