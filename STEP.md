# Sprint 0 · Step 003

## Goal

Introduce a small but production-shaped FastAPI backend that can prove the application process and its infrastructure dependencies are healthy.

## Included

- FastAPI Docker image
- typed environment configuration
- JSON container logging
- liveness endpoint
- PostgreSQL and Redis readiness checks
- backend unit tests
- Docker Compose backend service
- CI build, test, startup and smoke test

## Not included yet

- database schema or migrations
- users or authentication
- frontend
- email accounts
- attachment rules
- storage integrations
- Proxmox installation

## Acceptance criteria

```bash
make init
make check
make test
make up
make api-smoke
```

All commands must complete successfully from a clean checkout with Docker available.
