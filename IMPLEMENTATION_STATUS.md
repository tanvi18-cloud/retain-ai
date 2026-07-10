# RetainAI — Implementation Status

## Current Phase

**Phase 1 — Backend foundation (near complete)**

Synthetic seed data system is implemented. Public CRUD/list API endpoints are not yet wired to repositories.

## Completed Work

### Phase 0

- [x] Initialized git repository
- [x] Created `PROJECT_REQUIREMENTS.md` with stack, principles, and planned phases
- [x] Created `IMPLEMENTATION_STATUS.md` (this file)
- [x] Created `.gitignore`, `.editorconfig`, and root `README.md`

### Phase 1

- [x] Monorepo layout: `backend/`, `frontend/`, `scripts/`, `docs/`, `docker/`
- [x] Backend FastAPI shell with health endpoints, config, logging, and exception handlers
- [x] SQLModel domain models with central enums and indexes
- [x] API schemas separated from database models
- [x] Repository layer for customers, offers, recommendations, alerts, events, interactions
- [x] Synthetic seed JSON datasets for 10 fictional customers and 8 approved offers
- [x] `app/seed/seed_database.py` — validated, idempotent, FK-safe seed loader
- [x] `scripts/reset_database.py` — seed and `--reset` modes with readable summary output
- [x] Seed tests covering scenario constraints, idempotency, and reset behavior
- [x] Root `README.md` scenario table and synthetic-data disclaimer

### Not yet started (Phase 1 remainder)

- [ ] Public API routes wired to repositories
- [ ] Optional automatic seed on application startup in development

## Validation Commands

### Backend (current)

```bash
cd backend
uv sync --all-groups
uv run ruff check .
uv run pytest
uv run python ../scripts/reset_database.py --reset
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/health
```

Or with Make:

```bash
cd backend
make lint
make test
make run
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
| No public CRUD endpoints yet | Expected | Repositories and seed data ready |
| Seed not auto-loaded on API startup | Low | Run `scripts/reset_database.py` manually for now |
| Python 3.13 used locally | Low | `requires-python = ">=3.11"` |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 2 — Customer API routes and scoring services**:

---

**Phase 2 — Customer API routes**

1. Add `app/api/routes/customers.py` exposing list/get customer endpoints using repositories and response schemas.
2. Add route tests verifying pagination, search, segment filters, and standard error envelopes.
3. Wire routers into `app/api/router.py`.
4. Optionally auto-run idempotent seed on startup when `APP_ENV=development`.
5. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`. Do not add churn scoring, CrewAI agents, or WebSockets yet.

---
