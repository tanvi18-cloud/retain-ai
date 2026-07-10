# RetainAI — Implementation Status

## Current Phase

**Phase 4 — LLM and agent foundation (complete)**

Qwen configuration, mock LLM mode, shared LLM factory, read-only CrewAI tools, structured Pydantic agent outputs, four specialist agents, policy validation, and LLM status API are implemented with full test coverage.

## Completed Work

### Phase 0

- [x] Initialized git repository and core project documentation

### Phase 1

- [x] Monorepo scaffold with backend FastAPI shell and frontend Vite app
- [x] SQLModel domain models, repositories, API schemas, and exception handling
- [x] Synthetic seed data for 10 fictional customers and 8 approved offers
- [x] Idempotent seed loader and `scripts/reset_database.py`

### Phase 2

- [x] Customer 360 service and APIs
- [x] Deterministic scoring, eligibility, financial value, analysis, and portfolio services
- [x] Rules-only analysis and recommendation read APIs

### Phase 3

- [x] Async event ingestion, idempotency, asyncio queue workers
- [x] Event-driven Customer 360 updates and rules-only reanalysis
- [x] Preview alerts, WebSocket broadcasts, SMTP email notifications
- [x] Audit logging and system status APIs

### Phase 4

- [x] LLM configuration: `QWEN_*`, `AGENT_MAX_ITERATIONS`, `MOCK_LLM_MODE`
- [x] Shared LLM factory (`app/core/llm.py`) with Qwen via OpenAI-compatible endpoint
- [x] Global agent policy guardrails (`app/core/agent_policy.py`)
- [x] Structured agent output schemas (`app/schemas/agent_outputs.py`)
- [x] Eight read-only CrewAI tools (Customer 360, scores, offers, portfolio, interactions)
- [x] Deterministic mock LLM service for all 10 seeded customers
- [x] Agent validation service with policy enforcement
- [x] Four specialist agents:
  - Signal Investigator
  - Retention Decision Specialist
  - Offer Strategy Specialist
  - RM Copilot
- [x] `GET /api/v1/system/llm-status` (safe, no credential exposure)
- [x] Comprehensive tests (223 tests passing)
- [x] README LLM and agent documentation

### Not yet started

- [ ] CrewAI Crew/Flow orchestration (Prompt 10)
- [ ] Agentic recommendation persistence and event linkage
- [ ] Copilot chat REST endpoints
- [ ] Frontend portfolio, alerts, and copilot views
- [ ] Docker deployment

## Validation Commands

### Backend (current)

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pytest
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

curl http://localhost:8000/api/v1/system/llm-status
curl http://localhost:8000/api/v1/customers/C001/360
curl -X POST http://localhost:8000/api/v1/analysis/C001/rules-only
curl http://localhost:8000/api/v1/system/queue-status
```

### Agent smoke test (Python shell, mock mode)

```bash
cd backend
uv run python -c "
from app.agents.signal_investigator import run_signal_investigator
from app.agents.retention_decision_agent import run_retention_decision
print(run_signal_investigator('C001').primary_signal)
print(run_retention_decision('C001').deterministic_decision)
"
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

## Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Seed not auto-loaded on API startup | Low | Run `scripts/reset_database.py --reset` before testing API |
| asyncio.Queue is non-durable | Expected MVP | Events in queue are lost on process stop |
| Crew/Flow orchestration not yet wired | Expected | Individual agents callable; full pipeline in next phase |
| Recommendations list empty until persistence phase | Expected | Agent outputs not persisted yet |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 5 — CrewAI Crew/Flow orchestration**:

---

**Phase 5 — CrewAI Crew/Flow orchestration (Prompt 10)**

1. Create CrewAI Crew and Flow wiring the four specialist agents in sequence.
2. Persist agentic recommendations linked to events and alerts.
3. Replace or augment rules-preview alerts with final agentic outputs where appropriate.
4. Add copilot chat endpoints grounded in Customer 360 and approved offers.
5. Add tests for full flow, persistence, and idempotency.
6. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`.

---
