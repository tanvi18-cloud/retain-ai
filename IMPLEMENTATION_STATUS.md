# RetainAI — Implementation Status

## Current Phase

**Phase 2 — Deterministic decision engine (complete)**

Rules-only scoring, eligibility, financial projections, analysis, portfolio, and recommendation read APIs are implemented with full test coverage.

## Completed Work

### Phase 0

- [x] Initialized git repository and core project documentation

### Phase 1

- [x] Monorepo scaffold with backend FastAPI shell and frontend Vite app
- [x] SQLModel domain models, repositories, API schemas, and exception handling
- [x] Synthetic seed data for 10 fictional customers and 8 approved offers
- [x] Idempotent seed loader and `scripts/reset_database.py`

### Phase 2

- [x] Freshness thresholds in `app/core/config.py` and `.env.example`
- [x] `FreshnessStatus` enum (`FRESH`, `STALE`, `MISSING`)
- [x] Repository methods for accounts, credit profiles, transaction features, bureau triggers
- [x] Customer repository sorting support
- [x] `Customer360Service` with freshness calculation and data warnings
- [x] Customer API endpoints:
  - `GET /api/v1/customers`
  - `GET /api/v1/customers/{customer_id}`
  - `GET /api/v1/customers/{customer_id}/360`
- [x] Deterministic scoring rules (`app/core/scoring_rules.py`)
- [x] Policy rules (`app/core/policy_rules.py`)
- [x] Scoring, eligibility, financial value, analysis, and portfolio services
- [x] API endpoints:
  - `POST /api/v1/analysis/{customer_id}/rules-only`
  - `GET /api/v1/portfolio/summary`
  - `GET /api/v1/portfolio/customers`
  - `GET /api/v1/recommendations`
  - `GET /api/v1/recommendations/{recommendation_id}`
- [x] Comprehensive tests for all decision-engine components (124 tests passing)
- [x] README scoring, eligibility, and API documentation

### Not yet started

- [ ] Recommendation persistence from analysis pipeline
- [ ] Alert generation from high-priority recommendations
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
curl http://localhost:8000/api/v1/customers/C001/360
curl -X POST http://localhost:8000/api/v1/analysis/C001/rules-only
curl http://localhost:8000/api/v1/portfolio/summary
curl "http://localhost:8000/api/v1/portfolio/customers?page_size=10"
curl http://localhost:8000/api/v1/recommendations
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
| Recommendations list empty until persistence phase | Expected | Read API works; analysis does not persist yet |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 3 — Recommendation persistence and alerts**:

---

**Phase 3 — Recommendation persistence and alerts**

1. Persist rules-only analysis results as `Recommendation` records when requested.
2. Generate RM alerts for customers exceeding `ALERT_PRIORITY_THRESHOLD`.
3. Add write endpoints for recommendation status updates.
4. Add tests for persistence, alert creation, and idempotency.
5. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`. Do not add CrewAI agents or WebSockets yet.

---
