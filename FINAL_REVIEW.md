# RetainAI — Final Review

Delivery-phase review for the RetainAI MVP prototype. All validation commands were executed on **2026-07-10** unless noted.

## Project summary

RetainAI is an agentic AI customer-retention copilot for retail banking Relationship Managers. It integrates synthetic Customer 360 data, deterministic churn/value/priority scoring, a four-agent CrewAI workflow, async event processing, WebSocket and email alerts, and an RM Copilot chat — all behind a React dashboard and FastAPI backend.

**Data:** 100% synthetic. **Default mode:** `MOCK_LLM_MODE=true` (no live Qwen required).

## Completed capabilities

- Customer 360 aggregation with data-freshness indicators
- Deterministic scoring, eligibility, and approved-offer catalog
- CrewAI Flow with priority-based routing
- Event ingestion, async queue processing, retries
- Recommendation persistence and RM action workflow
- WebSocket alert streaming and SMTP notifications (Mailpit)
- RM Copilot with evidence-grounded mock/Qwen chat
- React operational frontend (portfolio, alerts, simulator, system status)
- Docker Compose stack (backend, frontend, Mailpit)
- Validation, demo, and smoke-test scripts
- Complete documentation set

## Architecture

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md). Key decisions preserved:

- Rules engine controls scores and eligibility
- Agents provide narrative reasoning only
- SQLite + asyncio.Queue for MVP simplicity
- Mock mode for reproducible demos

## Business value

See [docs/BUSINESS_CASE.md](./docs/BUSINESS_CASE.md). Prototype demonstrates proactive retention prioritization and RM productivity aids; financial impact figures are **estimated**, not guaranteed.

## Test results (actual)

| Suite | Command | Result |
|-------|---------|--------|
| Backend lint | `uv run ruff check .` | **PASS** — All checks passed |
| Backend tests | `uv run pytest` | **PASS** — 382 passed (212s) |
| Backend coverage | `uv run pytest --cov=app --cov-report=term-missing` | **PASS** — **87%** total coverage |
| Project validation | `uv run python ../scripts/validate_project.py` | **PASS** |
| Demo validation | `uv run python ../scripts/run_demo_validation.py` | **PASS** — 30 checks |
| Demo script | `uv run python ../scripts/run_demo.py` | **PASS** |
| Frontend build | `npm run build` | **PASS** |
| Frontend tests | `npm exec vitest run` | **PASS** — 90 tests |
| Frontend audit | `npm audit` | **PASS** — 0 vulnerabilities |

## Validation results

- C001 urgent home-loan scenario: PASS
- C004 lending restriction guardrail: PASS
- C008 FD retention: PASS
- C010 no-action: PASS
- RM Copilot evidence citations: PASS (after offer-evidence fix in `chat_tools.py`)
- No secrets in API responses: PASS (smoke test marker scan)

## Security posture

See [docs/SECURITY.md](./docs/SECURITY.md).

| Check | Status |
|-------|--------|
| No credentials committed | Verified |
| Synthetic data only | Verified |
| No unsafe SQL | Verified — SQLModel repositories |
| No arbitrary agent code execution | Verified — bounded tools |
| No hidden prompt exposure | Verified |
| No chain-of-thought storage | Verified |
| No automatic product approval | Verified |
| No automatic customer contact | Verified |
| No raw stack traces in APIs | Verified |

## Known limitations

- No authentication or RBAC
- SQLite and non-durable asyncio.Queue
- Estimated revenue-by-product chart
- Docker not validated on this machine (see below)
- Qwen live endpoint not tested (mock mode validated)

## Deployment options

| Mode | Ports | Use case |
|------|-------|----------|
| Local dev | Backend 8001, Frontend 5173 | Development |
| Docker Compose | Backend 8000, Frontend 8080, Mailpit 8025 | Demos, stakeholder review |

## Production recommendations

See [docs/PRODUCTION_ROADMAP.md](./docs/PRODUCTION_ROADMAP.md): PostgreSQL, durable queue, auth, bank connectors, model governance, Kubernetes.

## Docker validation status

**PENDING** — Docker CLI is not available on the validation host (`docker: command not found`). Docker files are present and `docker compose config` was not executed. Manual verification required on a machine with Docker Desktop:

```bash
docker compose config
docker compose build
docker compose up -d
uv run python ../scripts/smoke_test.py --base-url http://localhost:8000
```

## Qwen status

**Mock mode validated** — all tests and demos pass with `MOCK_LLM_MODE=true`. Live Qwen endpoint was **not** tested in this review.

## Final checklist

- [x] Backend lint passes
- [x] Backend tests pass (382)
- [x] Backend coverage run completes (87%)
- [x] Validation script passes
- [x] Demo script passes
- [x] Frontend build passes
- [x] Frontend tests pass (90)
- [ ] Docker build passes — **PENDING** (Docker not installed)
- [ ] Docker services become healthy — **PENDING**
- [ ] Frontend opens (8080) — **PENDING**
- [ ] Backend docs open — **PENDING**
- [ ] Mailpit opens — **PENDING**
- [ ] WebSocket connects (Docker) — **PENDING**
- [x] C001 demo works
- [x] C004 guardrail works
- [x] C008 FD scenario works
- [x] C010 no-action scenario works
- [x] No secrets detected

## Smoke test (local)

Requires running backend on port 8001:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001
uv run python ../scripts/smoke_test.py --base-url http://127.0.0.1:8001
```

Not executed in this review session (no long-running server started). All smoke-test steps are covered by integration tests and `run_demo_validation.py`.

## Files delivered (final phase)

| Artifact | Status |
|----------|--------|
| `backend/Dockerfile` | Created |
| `backend/.dockerignore` | Created |
| `frontend/Dockerfile` | Created |
| `frontend/.dockerignore` | Created |
| `frontend/nginx.conf` | Created |
| `docker-compose.yml` | Created |
| `.env.example` | Updated |
| `scripts/run_demo.py` | Created |
| `scripts/smoke_test.py` | Created |
| `docs/DOCKER_SETUP.md` | Created |
| `docs/DEMO_SCRIPT.md` | Created |
| `docs/BUSINESS_CASE.md` | Created |
| `docs/ARCHITECTURE.md` | Created |
| `docs/SECURITY.md` | Created |
| `docs/PRODUCTION_ROADMAP.md` | Created |
| `docs/API_OVERVIEW.md` | Created |
| `README.md` | Rewritten |
| `IMPLEMENTATION_STATUS.md` | Updated |

## Conclusion

RetainAI MVP prototype delivery is **complete** for all non-Docker validation criteria. Backend (382 tests, 87% coverage), frontend (90 tests), validation scripts, demo scripts, documentation, and Docker **configuration** are in place. Docker runtime validation remains **pending** until Docker Desktop is available on the host.
