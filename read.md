# RetainAI - Functional and Business Logic Guide

## 1) What this project does
RetainAI is an AI-assisted customer retention copilot for relationship managers (RMs). It combines deterministic scoring/rules with agent-generated explanations to help RMs identify at-risk customers and choose eligible retention actions.

## 2) Functional logic from the codebase

### Core flow
1. Customer and event data are loaded from synthetic datasets into SQLite.
2. The backend processes customer signals (bureau triggers, profile, transactions, interactions).
3. Deterministic services calculate:
   - churn risk
   - customer value
   - priority score
   - offer eligibility
4. A retention decision path is selected (retain/review/no-action).
5. CrewAI agents generate explanation/narrative outputs, but do not override rules.
6. Recommendations are stored and shown in UI.
7. Alerts are pushed via WebSocket and optional email notifications.
8. RM actions (approve/reject/defer/contact/close) are recorded with audit trail behavior.

### Main backend responsibilities
- **API layer (`backend/app/api`)**: REST and WebSocket endpoints.
- **Service layer (`backend/app/services`)**: business rules, scoring, eligibility, orchestration.
- **Flow and agents (`backend/app/flows`, `backend/app/agents`, `backend/app/crews`)**: agentic retention analysis and communication support.
- **Models/schemas (`backend/app/models`, `backend/app/schemas`)**: persistent data and validation contracts.
- **Event processing (`backend/app/services/event_*`)**: queue-based async event handling.

### Main frontend responsibilities
- Portfolio dashboard, customer 360 views, recommendations, alerts, chat/copilot, simulator, and system health pages.
- Calls backend APIs through typed client modules (`frontend/src/api`).
- Displays data and captures RM workflow actions; does not execute scoring or eligibility logic.

## 3) Business logic from the codebase
- The system is designed to reduce customer churn by identifying customers likely to leave and prioritizing intervention.
- Customer intervention priority is based on a blend of churn risk and customer value.
- Recommended offers are constrained to an approved catalog and filtered by deterministic eligibility policies.
- LLM/agent output is assistive (explanations and messaging) and not the source of policy decisions.
- Human-in-the-loop governance: RMs must approve/reject/defer recommendations.
- Real-time alerting supports proactive outreach before churn happens.

## 4) How to run the project

## Option A: Local (recommended for development)

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+
- npm

### Backend
```bash
cd /home/runner/work/retain-ai/retain-ai
cp .env.example .env
cd backend
uv sync --all-groups
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend
Open a new terminal:
```bash
cd /home/runner/work/retain-ai/retain-ai/frontend
cp .env.example .env
npm ci
npm run dev
```

Open: `http://localhost:5173`

## Option B: Docker
```bash
cd /home/runner/work/retain-ai/retain-ai
cp .env.example .env
docker compose build
docker compose up -d
```

Services:
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Mailpit: `http://localhost:8025`

## 5) Notes
- This repository uses synthetic data for MVP/demo.
- Mock LLM mode is available by default for reproducible local runs.
