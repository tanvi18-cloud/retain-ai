# Docker

Docker deployment is configured at the repository root.

See [docs/DOCKER_SETUP.md](../docs/DOCKER_SETUP.md) for prerequisites, commands, and troubleshooting.

Quick start:

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

Services: `backend` (:8000), `frontend` (:8080), `mailpit` (:8025).
