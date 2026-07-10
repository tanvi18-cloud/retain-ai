# RetainAI Testing Guide

This guide documents how to run backend and frontend tests, coverage reporting, validation scripts, and common troubleshooting steps.

## Backend Tests

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
```

Run a single module:

```bash
uv run pytest tests/test_end_to_end_workflows.py -v
```

## Frontend Tests

```bash
cd frontend
npm install
npm run build
npm exec vitest run
```

Run a single file:

```bash
npm exec vitest run src/test/end-to-end-ui.test.tsx
```

## Validation Scripts

From `backend/`:

```bash
uv run python ../scripts/validate_project.py
uv run python ../scripts/run_demo_validation.py
```

See [VALIDATION.md](./VALIDATION.md) for expected outcomes and interpretation.

## Test Structure

### Backend (`backend/tests/`)

| Area | Representative modules |
|------|------------------------|
| Health & config | `test_health.py`, `test_config.py` |
| Seed & DB | `test_seed.py`, `test_database.py` |
| Scoring & eligibility | `test_scoring_service.py`, `test_eligibility_service.py`, `test_analysis_service.py` |
| Events & alerts | `test_events_api.py`, `test_event_processor.py`, `test_alerts_api.py` |
| Agents & crew | `test_retention_crew.py`, `test_retention_flow.py`, `test_agent_tools.py` |
| Chat | `test_chat_service.py`, `test_chat_tools.py` |
| Phase 9 integration | `test_end_to_end_workflows.py`, `test_data_integrity.py`, `test_security_guardrails.py`, `test_demo_scenarios.py` |

### Frontend (`frontend/src/test/`)

| Area | Modules |
|------|---------|
| MSW fixtures/handlers | `fixtures.ts`, `handlers.ts` |
| Page tests | `portfolio.test.tsx`, `customer360.test.tsx`, `alerts.test.tsx`, `chat.test.tsx`, … |
| Phase 9 integration | `end-to-end-ui.test.tsx`, `security-ui.test.tsx` |
| WebSocket | `websocket.test.tsx`, `setup.ts` (`MockWebSocket`) |

## Fixtures

### Backend

- `client` — empty DB + TestClient
- `seeded_client` — full synthetic seed + TestClient
- `agent_seeded_session` / `agent_seeded_engine` — seeded DB for agent/tool tests
- `db_session` — empty session from `conftest_repositories.py`

### Frontend

- MSW handlers mirror `/api/v1/*` contracts
- `renderWithProviders()` wraps QueryClient, router, alerts WebSocket provider, and Sonner
- `resetMockState()` resets polling counters and handler state between tests

## Mocking Strategy

| Layer | Approach |
|-------|----------|
| Backend LLM | `MOCK_LLM_MODE=true` (default in tests) |
| Backend email | `unittest.mock` patch on `aiosmtplib.send` |
| Frontend HTTP | MSW (`setupServer`) |
| Frontend WebSocket | `MockWebSocket` in `setup.ts` |
| Timers | `vi.useFakeTimers` with `vi.useRealTimers()` in `afterEach` |

## Coverage Notes

Backend coverage focuses on business-critical services (scoring, eligibility, flow, events, recommendations, chat). Low-risk areas intentionally not targeted for 100% coverage:

- Pure schema/model boilerplate
- Static health response builders
- Deprecated compatibility shims

Run `uv run pytest --cov=app --cov-report=term-missing` to see uncovered lines.

## Troubleshooting

### Backend

| Symptom | Fix |
|---------|-----|
| Empty portfolio / 404 customers | Run `uv run python ../scripts/reset_database.py --reset` |
| Event stays QUEUED in manual testing | Ensure API server started (workers run on lifespan) |
| Crew tests fail without mock mode | Confirm `mock_llm_mode=True` in test settings |
| SQLite locked errors | Close other processes using the same DB file |

### Frontend

| Symptom | Fix |
|---------|-----|
| MSW unhandled request | Add handler in `handlers.ts` or `server.use()` in test |
| React act warnings | Await async UI updates; restore fake timers after use |
| WebSocket test flake | Ensure `MockWebSocket.instances` reset via provider cleanup |
| Build fails on env | Copy `frontend/.env.example` to `frontend/.env` |

### Validation Scripts

| Symptom | Fix |
|---------|-----|
| Import errors | Run from `backend/` with `uv run python ../scripts/...` |
| Failures on C004 offer | Check policy rules — lending offers must remain rejected |
| Demo timeout | Increase local resources; scripts use 15s bounded polling |

## Recommended Pre-PR Checklist

```bash
cd backend && uv run ruff check . && uv run pytest && uv run python ../scripts/validate_project.py && uv run python ../scripts/run_demo_validation.py
cd ../frontend && npm run build && npm exec vitest run
```
