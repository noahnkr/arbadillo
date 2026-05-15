# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Arbadillo is a sports betting arbitrage/EV bot. It scrapes live odds from multiple sportsbooks, collects sports statistics via the ESPN API, and uses ML models to predict event outcomes. Currently active for MLB only (`CLIENT_LEAGUES = {'mlb'}` in `backend/common/constants/sportsbook_definitions.py`).

## Commands

All commands run from `backend/` with `DJANGO_SETTINGS_MODULE=core.settings.dev`.

```bash
# Install dependencies
pip install -r backend/requirements.txt
playwright install

# Database migrations
python manage.py makemigrations
python manage.py migrate --settings=core.settings.dev

# Run Django dev server
python manage.py runserver --settings=core.settings.dev

# Run Celery worker (handles scraping + database queues)
celery -A core.celery worker -l info -Q scraping,database

# Run tests
python -m pytest
python tests/market_test.py  # sportsbook client integration test

# Fetch raw API data to a local file (for debugging)
python scripts/fetch_data.py <sportsbook> <league> [-e <event_id>] [-o <output.json>]

# ML pipeline
python manage.py train_model --market moneyline --league nfl --season 2024 --cutoff 2024-12-01
python manage.py predict_event --market moneyline --league nfl --season 2024 --after 2024-12-01 --model-name nfl_2024_moneyline.pkl --output-path data/predictions.json
python manage.py eval_predictions --league nfl --season 2024 --predictions-path data/predictions.json
```

## Architecture

### Django Apps

- **`sports/`** — Teams, players, events, and per-game stats from ESPN. Models: `Event`, `EventResult`, `Team`, `Player`, `TeamStat`, `PlayerStat`.
- **`sportsbook/`** — Scraped betting odds. Model: `Selection` (one row per sportsbook × event × market × outcome).
- **`ev/`** — Expected value pipeline. `ev/ml/` contains `features.py`, `train.py`, `predict.py`. Trained models are saved as `.pkl` files in `ev/ml/model_store/`.
- **`common/`** — Shared constants, aliases, and helpers. No models.
- **`core/`** — Django project config, Celery app, and orchestration tasks.

### Key Identifiers

Three canonical string keys used throughout as primary identifiers:
- **`event_key`**: `{YYYY-MM-DD}:{away-team}@{home-team}` (e.g. `2025-07-04:detroit-tigers@cleveland-guardians`)
- **`market_key`**: `{market}:{line}:{player}:{team}` components joined by `:`, omitting null parts
- **`team_key`** / **`player_key`**: ESPN slug format (e.g. `cleveland-guardians`, `freddie-freeman`)

### Alias / Normalization System

`common/constants/aliases/` maps raw sportsbook/ESPN strings to canonical keys:
- **`REVERSE_TEAM_LOOKUP`**: `(league, alias_str) → team_key`
- **`REVERSE_MARKET_LOOKUP`**: `(league, alias_str) → (standard_market, market_type)`
- **`REVERSE_STATS_LOOKUP`**: `(league, espn_label) → (stat_name, ...)`
- **`MARKET_TO_STATS`**: `league → market → {context, label, stats[]}` — controls which features are built for each ML model

`NormalizationError` (from `common/exceptions.py`) is raised when an alias is unknown. This is expected to be caught and logged; it skips the selection rather than crashing.

### Celery Task Flow

Bootstrap runs in 4 sequential phases orchestrated via `chord`/`group`:
1. `sync_teams` (per league)
2. `bootstrap_roster_and_schedule` → `sync_players` + `sync_schedule` (per team/league)
3. `bootstrap_sportsbook_schedule` → `scrape_events_for_league` (per sportsbook/league)
4. `bootstrap_sportsbook_odds` → `sync_selections` (upcoming + active)

Ongoing: `sync_selections` → fans out to `scrape_selections_for_event` per (sportsbook, league, event_key) → aggregates into `batch_upsert_selections`.

Two queues: `scraping` (Playwright/API work) and `database` (bulk writes).

### Sportsbook Clients

`sportsbook/clients/base.py` — `SportsbookClient` ABC. Each concrete client (espnbet, draftkings, fanduel, betrivers, betmgm) implements `get_events`, `parse_events`, `get_markets`, `parse_markets`, `export_markets`.

The `_get()` method supports three scraping strategies controlled by the `method` parameter:
- `request` — Playwright `context.request.get()` (fastest, for JSON APIs)
- `page_evaluate_fetch` — `fetch()` via JS inside a headless page (bypasses some CORS checks)
- `page_intercept` — navigate to the page and intercept a matching XHR response by URL fragment

Redis is used both for caching (event/selection hashes to skip unchanged data) and as inter-task state (event keys by status, team/player key lookups).

### ML Pipeline

`ev/ml/features.py` builds a feature vector from season-average stats for a team vs. opponent. `MARKET_TO_STATS[league][market]['stats']` defines which stat columns are included. Each stat produces 5 features: `_self`, `_opp`, `_diff`, `_vs_opp_allowed`, `_vs_self_allowed`.

`train.py` uses `sklearn.pipeline.Pipeline` with `StandardScaler` → `RandomForestClassifier`, saved via `joblib`.

### Environment Variables

Required: `DJANGO_SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
