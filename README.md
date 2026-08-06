# Mail Attachment Hub

Mail Attachment Hub is an open-source service for collecting email attachments and routing them to configured storage destinations. The project is built incrementally, with every step remaining runnable and reviewable.

## Current delivery

**Sprint 0 · Step 006 — React login and dashboard**

The repository currently provides:

- React 19 + TypeScript web interface
- responsive login page and protected dashboard
- FastAPI backend and JWT authentication
- administrator bootstrap on first start
- PostgreSQL 16, Redis 7 and SQLAlchemy 2
- Alembic migrations
- Nginx reverse proxy between the browser and backend
- JSON logging and dependency-aware health checks
- backend tests plus full-stack smoke checks in GitHub Actions

Email accounts, attachment rules, OAuth, storage integrations, workers and Proxmox installation intentionally arrive in later steps.

## Requirements

- Git
- Docker Engine with Docker Compose v2
- GNU Make and Bash for convenience commands

Windows users can run the commands through WSL 2 or Git Bash, or invoke Docker Compose directly.

## Start locally

```bash
make init
make check
make test
make up
make api-smoke
make migration-smoke
make auth-smoke
make frontend-smoke
```

The web interface is available at `http://127.0.0.1:3000`.
The API and Swagger documentation are available at `http://127.0.0.1:8080/docs` in development mode.

`make init` writes generated administrator credentials to the local `.env` file. Do not commit `.env`.

Read [STEP.md](STEP.md) for the scope and acceptance criteria of this delivery.
