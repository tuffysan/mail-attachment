# Mail Attachment Hub

Mail Attachment Hub is an open-source service for collecting email attachments and routing them to configured storage destinations. The project is being built incrementally, with every step remaining runnable and reviewable.

## Current delivery

**Sprint 0 · Step 004 — asynchronous database layer and Alembic migrations**

The repository currently provides:

- FastAPI backend in a dedicated Docker image
- PostgreSQL 16 and Redis 7
- SQLAlchemy 2 asynchronous engine and sessions
- Alembic schema migrations
- initial `system_metadata` table
- automatic migration on backend startup
- JSON logging
- liveness and dependency-aware readiness endpoints
- Docker Compose healthchecks
- backend unit tests and migration integration tests
- GitHub Actions CI for `main` and `master`

Email accounts, attachment rules, OAuth, storage integrations, workers, frontend and Proxmox installation intentionally arrive in later steps.

## Requirements

- Git
- Docker Engine with Docker Compose v2
- GNU Make and Bash for the documented convenience commands

Windows users can run the commands through WSL 2 or Git Bash, or invoke Docker Compose directly.

## Start locally

```bash
make init
make check
make test
make up
make api-smoke
make migration-smoke
```

The API is then available at:

- `http://127.0.0.1:8080/`
- `http://127.0.0.1:8080/health/live`
- `http://127.0.0.1:8080/health/ready`
- `http://127.0.0.1:8080/docs`

## Database migrations

```bash
make migrate
make migration-smoke
make migration-cycle
```

`make migration-cycle` temporarily downgrades the development database to the empty base revision and upgrades it back to the latest revision. Do not run that command against a production database.

## Common commands

```bash
make help
make ps
make logs
make down
make reset
```

Read [STEP.md](STEP.md) for the exact scope and acceptance criteria of this delivery.
