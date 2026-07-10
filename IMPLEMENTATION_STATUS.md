# RetainAI — Implementation Status

## Current Phase

**Phase 3 — Asynchronous event processing and notifications (complete)**

Event ingestion, idempotency, asyncio queue workers, event-driven Customer 360 updates, rules-only reanalysis, preview alerts, WebSocket broadcasts, SMTP email notifications, and audit logging are implemented with full test coverage.

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

### Phase 3

- [x] Extended `IncomingEvent` model with idempotency, execution tracking, analysis snapshot, and timestamps
- [x] Extended `Alert` model with event linkage, notification status, and rules-preview fields
- [x] `AuditLog` model and audit logging service
- [x] Event payload validation per event type (`app/schemas/events.py`)
- [x] `EventApplicationService` — applies events to synthetic source records with transactional audit logs
- [x] `EventQueue` — application-scoped asyncio queue with configurable workers and graceful shutdown
- [x] `EventProcessor` — status progression, rules-only reanalysis, preview alerts, post-commit notifications
- [x] `AlertService` — deterministic preview alerts with deduplication and acknowledgement
- [x] `WebSocketManager` and `WS /ws/alerts` with CONNECTED, PING/PONG, and RETENTION_ALERT broadcasts
- [x] `EmailService` — aiosmtplib multipart emails with safe content and retry handling
- [x] `NotificationService` — WebSocket + email orchestration with SENT/PARTIAL/FAILED/NOT_REQUIRED outcomes
- [x] API endpoints:
  - `POST /api/v1/events` (202 Accepted)
  - `GET /api/v1/events`
  - `GET /api/v1/events/{event_id}`
  - `POST /api/v1/events/{event_id}/retry`
  - `GET /api/v1/alerts`
  - `GET /api/v1/alerts/{alert_id}`
  - `PATCH /api/v1/alerts/{alert_id}/acknowledge`
  - `GET /api/v1/system/queue-status`
  - `GET /api/v1/system/notification-status`
- [x] FastAPI lifespan startup/shutdown for queue workers and WebSocket cleanup
- [x] Configuration: `QUEUE_WORKER_COUNT`, `EVENT_MAX_RETRIES`, `EMAIL_NOTIFICATIONS_ENABLED`, etc.
- [x] Comprehensive tests (160 tests passing)
- [x] README event-processing architecture documentation

### Not yet started

- [ ] CrewAI agentic recommendation workflow (Qwen integration)
- [ ] Recommendation persistence from agentic flow
- [ ] Frontend customer portfolio, alerts, and 360 views
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

curl "http://localhost:8000/api/v1/customers?page_size=100"
curl http://localhost:8000/api/v1/customers/C001/360
curl -X POST http://localhost:8000/api/v1/analysis/C001/rules-only
curl http://localhost:8000/api/v1/portfolio/summary

# Event ingestion
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C001","event_type":"EXTERNAL_HOME_LOAN_INQUIRY","source_system":"CREDIT_BUREAU","payload":{"severity":"HIGH"}}'

curl http://localhost:8000/api/v1/system/queue-status
curl http://localhost:8000/api/v1/system/notification-status
curl "http://localhost:8000/api/v1/alerts?customer_id=C001"
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
| Existing SQLite DB needs reset after model changes | Low | `create_all` does not alter existing tables; use `--reset` |
| asyncio.Queue is non-durable | Expected MVP | Events in queue are lost on process stop |
| Transaction seed timestamps may appear stale vs. runtime clock | Low | Expected for demo data; warnings surface in Customer 360 |
| Recommendations list empty until agentic phase | Expected | Read API works; agent recommendations not yet persisted |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 4 — CrewAI agentic recommendation workflow**:

---

**Phase 4 — CrewAI agentic recommendation workflow**

1. Integrate CrewAI Flow with Qwen (or mock mode) for agentic retention recommendations.
2. Persist agent recommendations linked to events and alerts (`AGENT_RECOMMENDATION` alert type).
3. Replace or augment rules-preview alerts with final agentic outputs where appropriate.
4. Add copilot chat endpoints grounded in Customer 360 and approved offers.
5. Add tests for agent flow, structured Pydantic outputs, and mock LLM mode.
6. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`. Do not add frontend views yet unless requested.

---
