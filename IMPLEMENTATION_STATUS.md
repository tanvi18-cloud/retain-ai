# RetainAI — Implementation Status

## Current Phase

**Phase 7 — Core frontend dashboard (complete)**

React RM dashboard with portfolio command center, customer directory, Customer 360, typed API client, TanStack Query, reusable UI system, charts, RM action controls, analysis polling, and Vitest coverage.

## Completed Work

### Phase 0–6

See prior phases: monorepo scaffold, Customer 360, deterministic scoring, event processing, LLM/agent foundation, Crew/Flow orchestration, recommendation persistence, RM action workflows, RM Copilot chat backend.

### Phase 7

- [x] Typed environment helper (`VITE_*` validation)
- [x] API client with `ApiError`, timeout, and standard error parsing
- [x] TypeScript types matching backend schemas
- [x] TanStack Query providers with sensible retry/refetch rules
- [x] Application shell with sidebar, top navigation, API status indicator
- [x] Portfolio dashboard: KPIs, charts, priority customer table
- [x] Customers page with search, segment filter, table/card views
- [x] Customer 360 page: risk scores, evidence, accounts, credit, transactions, freshness
- [x] Recommendation panel and RM action workflows
- [x] Rules-only and full analysis with bounded execution polling
- [x] INR/date/risk formatting utilities
- [x] Loading, empty, and error states across API-backed sections
- [x] Frontend tests with MSW (34 tests passing)
- [x] README frontend documentation

### Not yet started (Prompt 13)

- [ ] WebSocket alerts UI
- [ ] RM Copilot chat UI
- [ ] Event simulator page
- [ ] System status page
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
npm run test -- --run
npm run dev
```

### End-to-end smoke

```bash
curl http://127.0.0.1:8001/api/v1/health
curl http://127.0.0.1:8001/api/v1/portfolio/summary
curl http://127.0.0.1:8001/api/v1/customers/C001/360
```

## Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Seed not auto-loaded on API startup | Low | Run `scripts/reset_database.py --reset` before testing API |
| Frontend default API port is 8001 | Low | Configure `VITE_API_BASE_URL` if backend uses another port |
| Revenue-by-product chart is estimated | Expected | Grouped from trigger/offer fields, not ledger data |
| Alerts/Copilot/Simulator/System nav stubs only | Expected | Full pages deferred to Prompt 13 |
| asyncio.Queue is non-durable | Expected MVP | Events in queue are lost on process stop |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use **Prompt 13** to add:

1. WebSocket alerts panel and live notification UX
2. RM Copilot chat UI consuming `POST /api/v1/chat`
3. Event simulator and system status pages
4. Docker deployment configuration
5. Update `IMPLEMENTATION_STATUS.md` when tests pass

Follow all rules in `PROJECT_REQUIREMENTS.md`.

---
