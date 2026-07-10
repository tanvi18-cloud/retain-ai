# API Overview — RetainAI

Summary of REST and WebSocket endpoints. Full specification: http://localhost:8000/docs (or `/docs` via Docker frontend proxy).

**Base path:** `/api/v1`  
**Disclaimer:** All data is **synthetic**. Scores and offers are for demonstration — not production credit decisions.

---

## Health

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/health` | GET | Root health (Docker probe) | `status`, `service`, `environment`, `version` |
| `/api/v1/health` | GET | Versioned health | Same as above |

No authentication. Safe for load balancers.

---

## Customers

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/customers` | GET | Paginated customer list | `items[]`, `total`, filters: segment, search |
| `/api/v1/customers/{id}` | GET | Customer profile | Demographics, segment, relationship dates |
| `/api/v1/customers/{id}/360` | GET | Customer 360 view | Core banking, credit, bureau, transactions, staleness |

**Disclaimer:** 360 aggregates are read-only snapshots — not live core banking.

---

## Portfolio

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/portfolio/summary` | GET | Portfolio KPIs | Intervention counts, revenue at risk, decision breakdown |
| `/api/v1/portfolio/revenue-by-product` | GET | Revenue breakdown | Estimated product-level revenue (synthetic) |

---

## Analysis

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/analysis/{customer_id}/rules-only` | POST | Synchronous deterministic analysis | Churn, value, priority, eligibility, financials |
| `/api/v1/analysis/{customer_id}` | POST | Queue agentic analysis | **202** — `execution_id`, `status_url` |
| `/api/v1/analysis/executions/{id}` | GET | Execution status | Status, recommendation_id, errors |
| `/api/v1/analysis/executions` | GET | List executions | Paginated execution history |

**Disclaimer:** Rules-only does not persist recommendations or call LLM. Agentic path uses CrewAI (mock or Qwen).

---

## Events

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/events` | POST | Ingest inbound event | **202** — `event_id`, `status` |
| `/api/v1/events` | GET | List events | Paginated with filters |
| `/api/v1/events/{id}` | GET | Event detail | Payload, `analysis_result_json`, status |
| `/api/v1/events/{id}/retry` | POST | Retry failed event | **202** — re-queued event |

**Disclaimer:** Events are processed asynchronously via in-memory queue (non-durable in MVP).

---

## Alerts

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/alerts` | GET | List retention alerts | Priority, customer, notification status |
| `/api/v1/alerts/{id}` | GET | Alert detail | Linked recommendation, delivery metadata |
| `/api/v1/alerts/{id}` | PATCH | Update alert (e.g. acknowledge) | Updated alert |

---

## Recommendations

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/recommendations` | GET | List recommendations | Filter by status, decision, priority |
| `/api/v1/recommendations/{id}` | GET | Recommendation detail | Scores, offer, narrative, status |
| `/api/v1/recommendations/{id}/review` | POST | Mark reviewed | Updated status + audit |
| `/api/v1/recommendations/{id}/approve` | POST | RM approve for discussion | **Does not apply offer to account** |
| `/api/v1/recommendations/{id}/reject` | POST | Reject with reason | Requires `rejection_reason` |
| `/api/v1/recommendations/{id}/contacted` | POST | Log customer contact | Channel, response, follow-up |
| `/api/v1/recommendations/{id}/close` | POST | Close recommendation | Closing note required |

**Disclaimer:** Approve means RM may discuss — no automatic product change or customer outreach.

---

## RM Chat

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/chat` | POST | Copilot message | `answer`, `evidence[]`, `intent`, `customer_ids` |
| `/api/v1/chat/conversations` | GET | List RM conversations | Requires `rm_id` query param |
| `/api/v1/chat/conversations/{id}` | GET | Conversation detail | Messages (bounded history) |
| `/api/v1/chat/conversations/{id}/close` | POST | Close conversation | No further messages |

**Disclaimer:** Answers ground in evidence — not chain-of-thought. Mock mode when `MOCK_LLM_MODE=true`.

---

## System

| Endpoint | Method | Purpose | Main response |
|----------|--------|---------|---------------|
| `/api/v1/system/queue-status` | GET | Event queue metrics | Depth, workers, processed count |
| `/api/v1/system/notification-status` | GET | Notification config | Email enabled, SMTP host, thresholds |
| `/api/v1/system/llm-status` | GET | LLM connectivity | `mode` (mock/live), model, base URL |

**Disclaimer:** System endpoints expose configuration status — not secrets (API keys redacted).

---

## WebSocket

| Endpoint | Protocol | Purpose | Messages |
|----------|----------|---------|----------|
| `/ws/alerts` | WebSocket | Live retention alerts | `CONNECTED`, `RETENTION_ALERT`, `PING`/`PONG` |

Connect from browser: `ws://localhost:8080/ws/alerts` (Docker) or `ws://127.0.0.1:8001/ws/alerts` (local).

**Disclaimer:** No auth token in MVP — suitable for local demo only.

---

## Common patterns

- **Pagination:** `page`, `page_size` (max 100)
- **Idempotency:** `idempotency_key` on events and some actions
- **Errors:** `ApiErrorResponse` with `detail` — no stack traces
- **Async:** 202 Accepted for events and agentic analysis — poll status endpoints

## Related

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [SECURITY.md](./SECURITY.md)
- [VALIDATION.md](./VALIDATION.md)
