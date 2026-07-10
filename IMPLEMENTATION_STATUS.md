# RetainAI — Implementation Status

## Current Phase

**Phase 6 — RM Copilot chat backend (complete)**

Safe RM-only chat API with deterministic mock-mode intent handling, Qwen-powered real mode, twelve read-only chat tools, conversation context, evidence-backed answers, safety validation, and full test coverage.

## Completed Work

### Phase 0–5

See prior phases: monorepo scaffold, Customer 360, deterministic scoring, event processing, LLM/agent foundation, Crew/Flow orchestration, recommendation persistence, RM action workflows.

### Phase 6

- [x] Chat configuration (`CHAT_*` settings)
- [x] `ChatConversation` and `ChatMessage` models
- [x] Chat request/response schemas with evidence and suggested questions
- [x] Deterministic `ChatIntent` detection (15 supported intents)
- [x] Twelve safe read-only chat tools (`app/tools/chat_tools.py`)
- [x] Conversation context resolution with history limits and ambiguity handling
- [x] Mock-mode deterministic response generation
- [x] Qwen RM chat agent with pre-fetched tool data
- [x] Chat validation service (approval, account numbers, evidence checks)
- [x] Chat service orchestration with conversation persistence
- [x] Chat API: `POST /api/v1/chat`, conversation list/detail/close
- [x] Comprehensive tests (344 tests passing)
- [x] README RM Copilot documentation

### Not yet started

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

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Why is C001 urgent?","rm_id":"RM-01","customer_id":"C001"}'

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Who should I call today?","rm_id":"RM-01"}'

curl "http://localhost:8000/api/v1/chat/conversations?rm_id=RM-01"
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
| Qwen chat requires live endpoint when MOCK_LLM_MODE=false | Expected | Mock mode is fully functional without Qwen |
| Docker services empty | Expected | Dockerfiles added in a later phase |

## Next Recommended Prompt

Use this prompt to begin **Phase 7 — Frontend integration**:

1. Build React copilot chat UI consuming `POST /api/v1/chat`.
2. Build portfolio and alerts views wired to existing APIs.
3. Wire WebSocket alert UI to `AGENT_RECOMMENDATION` payloads.
4. Add Docker deployment configuration.
5. Update `IMPLEMENTATION_STATUS.md` when tests pass.

Follow all rules in `PROJECT_REQUIREMENTS.md`.

---
