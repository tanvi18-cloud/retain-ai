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
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

See [backend/README.md](./backend/README.md) for package layout and Makefile commands.

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

## Synthetic Demo Data

All customer names, emails, account numbers, balances, and events in RetainAI are **completely fictional**. The scenarios below are designed for local development and testing only — they **do not represent actual bank policies, real customers, or production decision rules**.

Load or reset the synthetic dataset from the `backend/` directory:

```bash
cd backend
uv run python ../scripts/reset_database.py
uv run python ../scripts/reset_database.py --reset
```

### Fictional customer scenarios

| ID | Profile | Key signals | Expected future outcome |
|----|---------|-------------|-------------------------|
| C001 | High-value priority salary customer since 2017 | External home-loan inquiry, 42% balance decline, large external transfer, excellent credit, zero DPD | Urgent retention |
| C002 | Mass-affluent card-active customer | External credit-card inquiry, good credit score, low DPD, strong card spending | Card upgrade or annual-fee-waiver review |
| C003 | Salary-dependent customer | Salary credit stopped, repeated transfers to another bank, declining balance, good credit | Immediate RM relationship call |
| C004 | Distressed borrower | High churn signals, 60 DPD, weak credit | Service or repayment assistance; no new lending offer |
| C005 | Long-tenure customer | Declining product usage, no strong external trigger | Relationship reactivation or monitoring |
| C006 | Low-value stable customer | One low-severity external inquiry, otherwise stable transactions | Monitor or no action |
| C007 | Frequent traveller | High forex spending, external travel-card inquiry | Travel-card recommendation |
| C008 | Priority depositor | Large fixed deposit maturing soon, recent external transfer, high customer value | Fixed-deposit renewal retention action |
| C009 | High-value investor | Increasing transfers to external investment platforms | Wealth-management referral subject to RM review |
| C010 | Stable customer | No material risk signals | No action |

Seed sources: `CORE_BANKING`, `CREDIT_BUREAU`, `TRANSACTION_ENGINE`, and `CRM` JSON files under `backend/app/seed/`.

## Running Tests

```bash
# Backend
cd backend
uv run pytest

# Frontend build verification
cd frontend
npm run build
```

## Development Workflow

1. Copy `.env.example` to `.env` at the repo root.
2. Start the backend API: `cd backend && uv run uvicorn app.main:app --reload` (or `make run`)
3. Start the frontend: `cd frontend && npm run dev`
4. Run lint before committing:
   - Backend: `cd backend && uv run ruff check .` (or `make lint`)
   - Frontend: `cd frontend && npm run lint`

## License

<!-- TBD -->
