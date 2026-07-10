# RetainAI — Agentic AI Customer Retention Copilot

**Proactive retention intelligence for Relationship Managers — synthetic data, deterministic guardrails, and AI-assisted explanations.**

> All customer data in this repository is **fictional**. Outputs are RM discussion aids, not production credit decisions.

<!-- Screenshot placeholders: add portfolio and Customer 360 captures after running locally -->

## Business problem

Retail RMs manage large portfolios without a unified view of churn signals, eligibility constraints, and approved retention offers. RetainAI combines **deterministic scoring** with a **four-agent CrewAI workflow** to prioritize outreach, recommend eligible offers, and explain decisions through an RM Copilot — while keeping the LLM out of eligibility and scoring.

## Key capabilities

- **Customer 360** — core banking, credit, bureau triggers, transaction features
- **Churn, value, and priority scoring** — reproducible rule-based engine
- **Revenue at risk** — synthetic financial exposure estimates
- **Agentic retention flow** — CrewAI agents with Pydantic-validated outputs
- **Event processing** — async queue for bureau and CRM signals
- **Alerts** — WebSocket toasts + SMTP email (Mailpit in demo)
- **RM Copilot** — evidence-grounded chat in mock or Qwen mode
- **RM approval workflow** — approve, reject, defer, contact, close
- **Event simulator** — trigger demo scenarios from the UI

## Architecture

```text
React (Vite) ──REST/WebSocket──► FastAPI ──► SQLite
                                    ├── Rules engine (deterministic)
                                    ├── CrewAI agents + Flow
                                    ├── asyncio.Queue
                                    └── SMTP → Mailpit
```

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for Mermaid diagrams and design decisions.

## Technology stack

| Layer | Stack |
|-------|-------|
| Frontend | React 19, TypeScript, Vite, TanStack Query, Recharts, Tailwind |
| Backend | Python 3.11, FastAPI, SQLModel, CrewAI, Pydantic |
| Database | SQLite (MVP) |
| LLM | Qwen via OpenAI-compatible API (mock mode default) |
| Email | aiosmtplib → Mailpit (local demo) |
| Tooling | uv, pytest, ruff, Vitest, Docker Compose |

## Four agents

1. **Retention Analyst** — interprets customer signals
2. **Offer Strategist** — selects from eligible approved offers only
3. **Risk Advisor** — surfaces policy warnings
4. **RM Communicator** — drafts customer-facing narrative

Agents **reason**; they do not control eligibility or scores.

## Deterministic guardrails

- Churn, value, priority, and eligibility are computed by services — not the LLM
- Only **approved offers** from the catalog may be recommended
- C004 lending restriction blocks new lending offers
- C010 no-action path blocks active retention offers
- RM must approve before any customer discussion is recorded as approved

## Customer scenarios (synthetic)

| ID | Scenario | Expected outcome |
|----|----------|------------------|
| C001 | External home-loan inquiry | Urgent RETAIN, home-loan offer |
| C004 | 60 DPD distressed borrower | No lending; repayment support only |
| C008 | FD maturing soon | OFFER-FD-RENEW |
| C010 | Stable, no signals | NO_ACTION |

Full catalog: ten customers in seed data. See [docs/DEMO_SCRIPT.md](./docs/DEMO_SCRIPT.md).

## Local setup

### Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22+ and npm

### Backend (port 8001)

```bash
cp .env.example .env
cd backend
uv sync --all-groups
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend (port 5173)

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Open http://localhost:5173

## Docker setup

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Mailpit | http://localhost:8025 |

See [docs/DOCKER_SETUP.md](./docs/DOCKER_SETUP.md).

## Mock Qwen mode (default)

```env
MOCK_LLM_MODE=true
```

Runs without GPU or live LLM. Agentic analysis and RM Copilot use deterministic mock responses. Recommended for demos, CI, and validation.

## Real Qwen mode

1. Start a Qwen-compatible server on port 9000
2. Set `MOCK_LLM_MODE=false` and `QWEN_BASE_URL=http://localhost:9000/v1`
3. Docker: use `http://host.docker.internal:9000/v1`

## Running tests

### Backend

```bash
cd backend
uv run ruff check .
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend
npm run build
npm exec vitest run
npm audit
```

See [docs/TESTING.md](./docs/TESTING.md).

## Running validation

```bash
cd backend
uv run python ../scripts/validate_project.py
uv run python ../scripts/run_demo_validation.py
uv run python ../scripts/run_demo.py
uv run python ../scripts/smoke_test.py --base-url http://127.0.0.1:8001
```

See [docs/VALIDATION.md](./docs/VALIDATION.md).

## Demo workflow

```bash
cd backend
uv run python ../scripts/run_demo.py
```

Or use the UI: Portfolio → C001 → Event Simulator → Alerts → RM Copilot.

## Main routes

| Route | Description |
|-------|-------------|
| `/` | Portfolio command center |
| `/customers` | Customer directory |
| `/customers/:id` | Customer 360 + recommendations |
| `/alerts` | Alert center (WebSocket) |
| `/chat` | RM Copilot |
| `/simulator` | Event simulator |
| `/system` | LLM, queue, notification status |

## API documentation

- Interactive: http://localhost:8001/docs (local) or http://localhost:8000/docs (Docker)
- Overview: [docs/API_OVERVIEW.md](./docs/API_OVERVIEW.md)

## Security

Synthetic data only. No authentication in MVP. See [docs/SECURITY.md](./docs/SECURITY.md).

## Known limitations

- SQLite + in-memory queue (non-durable)
- No RBAC or encryption at rest
- Revenue-by-product chart is estimated
- Seed not auto-loaded on every API startup (Docker entrypoint seeds on first run)

## Future roadmap

[docs/PRODUCTION_ROADMAP.md](./docs/PRODUCTION_ROADMAP.md) — PostgreSQL, durable queue, auth, bank connectors, model governance, Kubernetes.

## Documentation index

| Document | Topic |
|----------|-------|
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design |
| [BUSINESS_CASE.md](./docs/BUSINESS_CASE.md) | Value hypothesis |
| [DOCKER_SETUP.md](./docs/DOCKER_SETUP.md) | Container deployment |
| [DEMO_SCRIPT.md](./docs/DEMO_SCRIPT.md) | Repeatable demo |
| [API_OVERVIEW.md](./docs/API_OVERVIEW.md) | REST + WebSocket summary |
| [SECURITY.md](./docs/SECURITY.md) | Security posture |
| [VALIDATION.md](./docs/VALIDATION.md) | Validation scope |
| [TESTING.md](./docs/TESTING.md) | Test matrix |
| [FINAL_REVIEW.md](./FINAL_REVIEW.md) | Delivery checklist |

## Resume-ready summary

**RetainAI — Agentic AI Customer Retention Copilot**

- Built a Customer 360 retention platform integrating core banking, credit history, bureau triggers, and transaction data to calculate churn risk, customer value, and revenue at risk.
- Implemented a four-agent CrewAI workflow using Qwen to recommend eligible retention offers, support RM queries, and deliver real-time dashboard and email alerts through FastAPI and WebSockets.

---

See [PROJECT_REQUIREMENTS.md](./PROJECT_REQUIREMENTS.md) and [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for full project history.
