# RetainAI — Implementation Status

## Current Phase

**Phase 2 — Customer API and Customer 360 (partial)**

Customer list/detail/360 endpoints and aggregation service are complete. Churn scoring and agentic copilot are not yet implemented.

## Completed Work

### Phase 0

- [x] Initialized git repository and core project documentation

### Phase 1

- [x] Monorepo scaffold with backend FastAPI shell and frontend Vite app
- [x] SQLModel domain models, repositories, API schemas, and exception handling
- [x] Synthetic seed data for 10 fictional customers and 8 approved offers
- [x] Idempotent seed loader and `scripts/reset_database.py`

### Phase 2 (in progress)

- [x] Freshness thresholds in `app/core/config.py` and `.env.example`
- [x] `FreshnessStatus` enum (`FRESH`, `STALE`, `MISSING`)
- [x] Repository methods for accounts, credit profiles, transaction features, bureau triggers
- [x] Customer repository sorting support
- [x] `Customer360Service` with freshness calculation and data warnings
- [x] Customer API endpoints:
  - `GET /api/v1/customers`
  - `GET /api/v1/customers/{customer_id}`
  - `GET /api/v1/customers/{customer_id}/360`
- [x] OpenAPI summaries, response models, and documented 404 responses
- [x] Customer 360 and customer API tests (64 tests passing)
- [x] README Customer 360 API examples

### Not yet started

- [ ] Deterministic churn and retention scoring services
- [ ] Recommendation and alert generation pipeline
- [ ] CrewAI copilot integration
- [ ] Frontend customer portfolio and 360 views

## Validation Commands

### Backend (current)

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pytest
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

curl "http://localhost:8000/api/v1/customers?page_size=100"
curl http://localhost:8000/api/v1/customers/C001
curl http://localhost:8000/api/v1/customers/C001/360
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
| Transaction seed timestamps may appear stale vs. runtime clock | Low | Expected for demo data; warnings surface in Customer 360 |
| No scoring or recommendations generated yet | Expected | Added in next phase |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 2 — Deterministic scoring services**:

---

**Phase 2 — Deterministic scoring services**

1. Add `app/services/churn_scoring_service.py` and `app/services/value_scoring_service.py` with deterministic, auditable calculations.
2. Add `app/services/offer_eligibility_service.py` returning only approved offers from the catalog.
3. Expose scores via internal service methods and pytest coverage for each scenario customer (C001–C010).
4. Do not allow the LLM to alter calculated scores.
5. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`. Do not add CrewAI agents or WebSockets yet.

---
