# RetainAI

**Agentic AI customer-retention copilot for retail banking Relationship Managers**

RetainAI helps Relationship Managers proactively retain customers by surfacing churn risk, deterministic eligibility scores, and AI-assisted explanations grounded in approved retention offers—all powered by synthetic data for safe local development.

## Problem Statement

Retail banking Relationship Managers manage large customer portfolios under time pressure. Identifying who is at risk of leaving, which retention offers apply, and how to prioritize outreach is often manual and inconsistent. RetainAI combines deterministic business logic (scoring, eligibility, approved offers) with an agentic copilot that explains insights and recommends next steps—without letting the LLM alter scores or invent offers.

## Architecture Summary

```text
retain-ai/
├── backend/          # FastAPI + SQLModel + CrewAI
├── frontend/         # React + TypeScript + Vite
├── scripts/          # Dev and validation scripts
├── docs/             # Extended documentation
├── docker/           # Container definitions (later phases)
├── .env.example      # Environment variable template
└── docker-compose.yml
```

```text
┌─────────────────────────────────────────────────────────────────┐
│                     React + TypeScript (Vite)                   │
│   Dashboard · Portfolio · Alerts (WebSocket) · Copilot Chat     │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI (Python 3.11+)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Scoring      │  │ Approved     │  │ CrewAI Agents        │ │
│  │ (deterministic)│ │ Offers       │  │ (Pydantic outputs)   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ asyncio.Queue│  │ WebSockets   │  │ SMTP (dev alerts)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ SQLite (MVP)    │
                    │ Synthetic data  │
                    └─────────────────┘
```

### Key design constraints

- **Deterministic scoring** — churn and credit eligibility are computed by services, not the LLM.
- **Approved offers only** — the copilot may recommend only offers from the approved-offer service.
- **Structured AI output** — all LLM responses validate against Pydantic schemas.
- **Mock mode** — set `MOCK_LLM_MODE=true` to run without a live LLM.
- **MVP simplicity** — SQLite, in-memory `asyncio.Queue`; no Kafka, Redis, Celery, or microservices.

See [PROJECT_REQUIREMENTS.md](./PROJECT_REQUIREMENTS.md) for the full requirements list and [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for current progress.

## Prerequisites

- Python 3.11+ (3.13 tested)
- [uv](https://docs.astral.sh/uv/) for Python dependency management (`pip install uv`)
- Node.js 20+ and npm

## Backend Setup

```bash
cp .env.example .env
cd backend
uv sync --all-groups
```

See [backend/README.md](./backend/README.md) for package layout and commands.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at http://localhost:5173. See [frontend/README.md](./frontend/README.md) for details.

## Environment Variables

Copy the template and adjust as needed:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose |
|----------|---------|
| `MOCK_LLM_MODE` | Run without a live LLM (`true` for local dev) |
| `DATABASE_URL` | SQLite connection string |
| `FRONTEND_ORIGIN` | CORS origin for the Vite dev server |
| `QWEN_*` | OpenAI-compatible Qwen endpoint settings |
| `SMTP_*` | Development email (e.g. Mailhog on port 1025) |
| `ALERT_PRIORITY_THRESHOLD` | Score threshold for high-priority alerts |

Full list: [.env.example](./.env.example)

## Running Tests

```bash
# Backend (once tests are implemented)
cd backend
uv run pytest

# Frontend build verification
cd frontend
npm run build
```

## Development Workflow

1. Copy `.env.example` to `.env` at the repo root.
2. Start the backend API (once `app/main.py` exists): `cd backend && uv run uvicorn app.main:app --reload`
3. Start the frontend: `cd frontend && npm run dev`
4. Run lint before committing:
   - Backend: `cd backend && uv run ruff check .`
   - Frontend: `cd frontend && npm run lint`

## License

<!-- TBD -->
