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

Settings load from `../.env` (repo root) or `backend/.env`.

## Commands

Using Make (Git Bash / Linux / macOS):

```bash
make run      # Start dev server with reload
make test     # Run pytest
make lint     # Ruff check
make format   # Ruff format
```

Equivalent uv commands:

```bash
# Run API server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Root health check |
| GET | `/api/v1/health` | Versioned health check |

Health response shape:

```json
{
  "status": "healthy",
  "service": "RetainAI API",
  "environment": "development",
  "version": "0.1.0"
}
```

## Status

Basic FastAPI application shell is implemented. Database models, business services, and agents are added in later phases.
