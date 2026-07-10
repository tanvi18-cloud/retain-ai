# Security — RetainAI

Security posture for the **MVP prototype**. Not production-ready without the controls in [PRODUCTION_ROADMAP.md](./PRODUCTION_ROADMAP.md).

## Data classification

| Rule | Status |
|------|--------|
| Synthetic data only | Enforced in seed dataset |
| No real PII | Demo names/IDs are fictional |
| No raw transaction exposure | Aggregated features only in API |
| No production customer records | Repository contains no bank data |

## Secret handling

- Secrets via **environment variables** only (`.env`, not committed)
- `.env.example` uses placeholders — no real credentials
- Docker images do **not** bake `.env` or API keys
- `QWEN_API_KEY` default is `not-required-for-local`

**Never commit:** `.env`, API keys, SMTP passwords, production connection strings.

## Environment variables

All configuration flows through `Settings` in `app/core/config.py`. Unknown env keys are ignored (`extra="ignore"`).

Review `.env.example` before deployment. Rotate keys if accidentally exposed.

## LLM privacy

- Customer context sent to Qwen only when `MOCK_LLM_MODE=false`
- In production, use **on-prem or VPC-hosted** models with data-processing agreements
- Mock mode sends no external LLM traffic
- Chat responses include **evidence references**, not raw prompts

## Prompt-injection concerns

RM Copilot accepts free-text questions. Mitigations in MVP:

- Bounded tool calls (`CHAT_MAX_TOOL_CALLS`)
- Tools read only approved repositories (no arbitrary code)
- System prompts not exposed in API responses
- No chain-of-thought stored or returned

**Production:** input sanitization, output filtering, per-RM rate limits.

## Tool restrictions

Chat tools can:

- Look up customer summaries
- Fetch recommendations and analysis results
- List approved offers

Chat tools cannot:

- Execute SQL
- Modify recommendations without RM action endpoints
- Send email or contact customers
- Approve offers automatically

## No arbitrary SQL

All database access uses SQLModel repositories with parameterized queries. Agents have no database write tools.

## No automatic customer contact

- Email goes to configured `RM_EMAIL` (demo inbox via Mailpit)
- No SMS, push, or customer-facing email
- Notifications require explicit `notifications_enabled` on events

## Human approval

Recommendations require RM **approve / reject / defer** via authenticated endpoints (auth not yet implemented — open in MVP).

## Audit logging

`AuditLogService` records:

- Event completion
- Recommendation state changes
- Key entity mutations

**Production:** immutable audit store, retention policy, SIEM integration.

## Role-based access (future)

MVP has **no authentication**. Planned roles:

| Role | Access |
|------|--------|
| RM | Own portfolio, approve recommendations |
| Supervisor | Team portfolio, override analytics |
| Admin | System config, audit export |
| Read-only | Dashboards only |

## Encryption (production requirements)

| Layer | MVP | Production |
|-------|-----|------------|
| Transit | HTTP local demo | TLS 1.2+ everywhere |
| Rest | SQLite file | Encrypted DB, KMS |
| Secrets | .env file | Vault / cloud secret manager |
| Backups | None | Encrypted, tested restore |

## Data retention

- SQLite file persists until `docker compose down -v` or manual delete
- Chat history TTL: `CHAT_CONVERSATION_TTL_HOURS` (default 24h)
- **Production:** policy-driven retention per regulation (e.g. RBI guidelines)

## Model hosting

- Default: local Qwen via OpenAI-compatible API
- Docker: `host.docker.internal:9000`
- Do not expose Qwen to public internet without authentication

## Regulatory and policy review

This prototype **has not** undergone:

- Legal/compliance sign-off
- Fair lending review
- Model risk management (SR 11-7 equivalent)
- Customer consent workflows

Any production use requires bank-specific policy embedding and regulatory review.

## API security

| Control | MVP |
|---------|-----|
| CORS | Single `FRONTEND_ORIGIN` |
| Error responses | No raw stack traces to clients |
| Security headers | Nginx CSP, X-Frame-Options (Docker frontend) |
| Rate limiting | Not implemented |
| Input validation | Pydantic on all endpoints |

## Known MVP limitations

1. No authentication or authorization
2. No encryption at rest
3. Non-durable event queue
4. SMTP without TLS in local demo
5. WebSocket open without token
6. No penetration test performed
7. `npm audit` / dependency review — see FINAL_REVIEW.md

## Security review checklist (prototype)

- [x] No credentials in repository
- [x] Synthetic data only
- [x] Deterministic eligibility separate from LLM
- [x] No automatic offer application
- [x] No automatic customer contact
- [x] Audit log on key actions
- [ ] Authentication (deferred)
- [ ] Encryption at rest (deferred)
- [ ] Formal security assessment (deferred)
