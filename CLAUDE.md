# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Event Director Analytics Demo — an AI-powered insights platform for race/event directors built with Streamlit. Analyzes participant registration data (CSV-based) to surface retention, churn, demographics, geographic reach, and benchmarking metrics.

## Running the App

```bash
uv sync                            # Install dependencies
uv run streamlit run src/app.py    # Launch at http://localhost:8501
```

Individual modules have `if __name__ == "__main__"` blocks for standalone testing:
```bash
uv run python src/data_loader.py
uv run python src/analytics.py
uv run python src/llm_client.py
```

There are no automated tests, linting, or CI/CD configured.

## Architecture

### Data Flow

```
CSV files (data/)
  → data_loader.load_enriched_entries()  # joins & enriches
  → EventAnalytics / EcosystemBenchmark  # business logic
  → app.py Streamlit pages              # UI rendering
  → llm_client                          # AI-generated insights
```

### Module Responsibilities

- **src/data_loader.py** — Loads and joins the three CSV files (Events→Categories→Entries), deduplicates participants using a composite key (`FName|LName|DOB` since RacerID is unreliable), adds derived columns (`participant_id`, `event_year`, `participant_age`). Results cached with `@lru_cache`.
- **src/analytics.py** — Two classes: `EventAnalytics` (single-promoter metrics: YoY, retention, cohorts, churn, demographics, geography) and `EcosystemBenchmark` (cross-promoter comparisons and participant overlap).
- **src/llm_client.py** — Dual-provider LLM integration (AWS Bedrock Claude primary, OpenAI fallback). Generates dashboard insights, query responses, re-engagement messages, and translates natural language to pandas code.
- **src/app.py** — Streamlit UI with 5 pages: Smart Dashboard, Ask Questions, Loyalty & Churn, Benchmarking, Geographic View. Uses Outside magazine brand styling (primary yellow #FFD100, black #000000).

### Data Model

```
Events (EventID) ──1:M──> Categories (EventID, RaceRecID) ──1:M──> Entries (ItemID)
```

Join keys: `Events.EventID = Categories.EventID`, `Categories.RaceRecID = Entries.ItemID`

### LLM Configuration

Provider controlled by `LLM_PROVIDER` env var. Keys in `.env` (gitignored). Bedrock model: `us.anthropic.claude-haiku-4-5-20251001-v1:0`, OpenAI model: `gpt-5-nano`.

### Known Security Concern

The "Ask Questions" feature uses `exec()` on LLM-generated pandas code. The production integration plan (docs/PRODUCTION_INTEGRATION_PLAN.md) recommends replacing this with parameterized SQL generation.

## Session State

Streamlit session state holds: `promoter_id`, `df` (cached enriched entries), `analytics` (EventAnalytics instance), `chat_history`.

## Brand Styling

Outside magazine visual identity is applied throughout — see `skills/outside-brand-style/SKILL.md` for the full palette and component patterns. Chart color sequence: `['#FFD100', '#000000', '#333333', '#666666', '#999999', '#CCCCCC', '#E6BC00', '#B8960A']`.
