# SmartLine — NFL Sports Betting Intelligence System

**Author:** Tanner Gurley  
**Project Type:** End-to-End Data Engineering & Analytics Web Application  
**Technologies:** Python, SQL, PostgreSQL, FastAPI, React, Public APIs  

---

## Overview

SmartLine is a full-scale sports betting intelligence platform designed to analyze National Football League (NFL) games using historical results, betting market data, injury reports, and weather conditions. The system enables advanced analysis of betting market behavior, trend identification, and historical strategy backtesting using complex SQL analytics and real-world data pipelines :contentReference[oaicite:1]{index=1}.

This project was built to demonstrate professional-level data consulting and analytics engineering capabilities, including relational data modeling, ETL design, advanced SQL analytics, backend API development, and cloud deployment.

---

## Core Objectives

SmartLine was designed with the following goals:

- Design a normalized PostgreSQL database optimized for analytical workloads
- Integrate multiple independent data sources into a unified schema
- Implement advanced SQL analytics using CTEs, window functions, and temporal joins
- Enable historical backtesting of betting strategies with ROI analysis
- Expose analytics through a clean backend API
- Deploy the system using free-tier cloud infrastructure :contentReference[oaicite:2]{index=2}

---

## Data Sources

SmartLine integrates and normalizes data from multiple external sources, including:

- NFL schedules, teams, and final game results
- Historical betting odds (spreads, totals, moneylines) with time-series snapshots
- Player injury reports with status updates over time
- Weather observations for outdoor games

All datasets are ingested via Python-based ETL pipelines and stored in a centralized PostgreSQL database :contentReference[oaicite:3]{index=3}.

---

## System Architecture

SmartLine follows a three-tier architecture:

### Data Layer
- PostgreSQL relational database
- Strong primary and foreign key enforcement
- Indexed analytical columns for performance
- Materialized views for high-cost aggregations

### Application Layer
- FastAPI backend written in Python
- RESTful endpoints exposing analytical queries
- Designed to support future authentication and user-specific strategies

### Presentation Layer
- React-based frontend (polish in progress)
- Interactive tables and analytics dashboards
- Strategy backtesting and result exploration

:contentReference[oaicite:4]{index=4}

---

## Database Design

The database schema is designed to support both transactional integrity and analytical flexibility.

### Core Entities
- **Team** — NFL teams and identifiers
- **Player** — Player metadata and team assignments
- **Game** — Schedule and matchup information
- **GameResult** — Final scores and outcomes
- **OddsLine** — Time-series betting market snapshots
- **InjuryReport** — Player availability statuses
- **WeatherObservation** — Game-time weather conditions :contentReference[oaicite:5]{index=5}

---

## Functional Dependencies

Key functional dependencies governing the schema include:

- `team_id → team_name, abbreviation`
- `player_id → team_id, position`
- `game_id → date, home_team, away_team, venue`
- `(game_id, book, market, side, timestamp) → line_value, price`
- `(game_id, player_id, timestamp) → injury_status`

These dependencies ensure data consistency while enabling time-dependent analytical queries :contentReference[oaicite:6]{index=6}.

---

## Analytical Capabilities

SmartLine supports advanced analytics including:

### Line Movement Analysis
- Opening vs. closing line comparison
- Detection of significant market movement
- Cross-book discrepancies

### Trend Analysis
- Rolling team performance metrics
- Against-the-spread (ATS) trends
- Over/Under performance analysis
- Situational splits (home/away, favorites/underdogs)

### Strategy Backtesting
- User-defined filters on odds, teams, injuries, and weather
- ROI and win-rate computation
- Historical performance by season and week

All analytics are implemented primarily in SQL using window functions, CTEs, and aggregations :contentReference[oaicite:7]{index=7}.

---

## Deployment

The application is designed to run entirely on free-tier cloud services:

- **Database:** PostgreSQL (Supabase)
- **Backend API:** Railway or Render
- **Frontend:** Vercel
- **Scheduled ETL:** GitHub Actions

:contentReference[oaicite:8]{index=8}

---

## Project Status

SmartLine is under active development. Current focus areas include:

- Expanding analytics coverage (Totals, Moneyline, multi-book consensus)
- Hardening ETL pipelines and data validation
- Performance optimization using materialized views
- Strategy persistence and reproducibility
- Final production-grade frontend implementation

---

## Why This Project Matters

SmartLine is intentionally designed to mirror real-world data consulting and analytics engineering work. Rather than focusing on isolated queries or toy datasets, the project emphasizes:

- End-to-end system design
- Analytical correctness and reproducibility
- Clear separation between data, analytics, and application layers
- Scalable architecture suitable for real deployment

This project serves as a comprehensive portfolio centerpiece demonstrating readiness for data consulting and analytics engineering roles.

---

## License

This project is for educational and portfolio purposes only. Betting analytics are provided for analytical demonstration and are not intended as financial advice.
