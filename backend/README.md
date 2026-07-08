# RetainAI Backend

FastAPI backend for the RetainAI customer-retention copilot.

## Stack

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- FastAPI, SQLModel, Pydantic Settings
- CrewAI (agents added in a later phase)
- pytest + Ruff for testing and linting

## Package layout

```text
backend/
  app/
    api/       # HTTP route modules
    models/    # SQLModel database models
    schemas/   # Pydantic request/response schemas
    services/  # Business logic
    agents/    # CrewAI agent definitions
    crews/     # CrewAI crew orchestration
    flows/     # CrewAI flows
    tools/     # Agent tools
    core/      # Config, database, logging, queue
    seed/      # Synthetic seed data
  tests/
```

## Setup

From the repository root, copy environment variables:

```bash
cp .env.example .env
```

Install dependencies with uv:

```bash
cd backend
uv sync --all-groups
```

## Commands

```bash
# Lint
uv run ruff check .
uv run ruff format --check .

# Tests (once implemented)
uv run pytest

# Run API server (once main.py is added)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Status

Scaffold only — business logic, API routes, and database models are added in later phases.
