# RetainAI — Implementation Status

## Current Phase

**Phase 8 — Operational frontend features (complete)**

Live WebSocket alerts, alert center, RM Copilot chat UI, event simulator, system status page, route-based code splitting, navigation completion, responsive/a11y polish, and expanded Vitest coverage.

## Completed Work

### Phase 0–7

See prior phases: monorepo scaffold, Customer 360, deterministic scoring, event processing, LLM/agent foundation, Crew/Flow orchestration, recommendation persistence, RM action workflows, RM Copilot chat backend, and core React dashboard (portfolio, customers, Customer 360).

### Phase 8

- [x] Extended `VITE_*` environment (`WS`, RM identity, feature flags)
- [x] Typed API clients: alerts, chat, events, system
- [x] WebSocket hook with reconnect, PING/PONG, deduplicated alerts, query cache updates
- [x] Live alert Sonner toasts and alert center (`/alerts`)
- [x] RM Copilot chat UI (`/chat`) with conversations, evidence, suggestions, customer context
- [x] Event simulator (`/simulator`) with polling, retry, and scenario cards
- [x] System status page (`/system`) with safe diagnostics
- [x] Top navigation: API/WebSocket status, unacknowledged alert count
- [x] Mobile bottom navigation and completed sidebar links
- [x] Route-based lazy loading (Customer 360, Alerts, Chat, Simulator, System)
- [x] Frontend tests with MSW and MockWebSocket (73 tests passing)
- [x] README frontend documentation updated

### Not yet started

- [ ] Docker deployment

## Validation Commands

### Backend

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pytest
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run build
npm exec vitest run
npm run dev
```

### End-to-end smoke

```bash
curl http://127.0.0.1:8001/api/v1/health
curl http://127.0.0.1:8001/api/v1/portfolio/summary
curl http://127.0.0.1:8001/api/v1/customers/C001/360
curl http://127.0.0.1:8001/api/v1/system/llm-status
```

## Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Seed not auto-loaded on API startup | Low | Run `scripts/reset_database.py --reset` before testing API |
| Frontend default API port is 8001 | Low | Configure `VITE_API_BASE_URL` if backend uses another port |
| Revenue-by-product chart is estimated | Expected | Grouped from trigger/offer fields, not ledger data |
| asyncio.Queue is non-durable | Expected MVP | Events in queue are lost on process stop |
| Docker services empty | Expected | Dockerfiles added in a later phase |
| WebSocket requires backend running | Low | UI shows reconnecting state when API/WS unavailable |

## Next Recommended Prompt

Use **Prompt 14** (or equivalent) for:

1. Docker deployment configuration (backend, frontend, Mailhog)
2. Production hardening (CORS, env templates, health probes)
3. Optional E2E Playwright suite against seeded data
4. Update `IMPLEMENTATION_STATUS.md` when complete

Follow all rules in `PROJECT_REQUIREMENTS.md`.

---
