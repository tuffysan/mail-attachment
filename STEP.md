# Sprint 0 · Step 004

## Goal

Add a production-shaped asynchronous database layer and versioned PostgreSQL schema migrations to the FastAPI backend.

## Included

- SQLAlchemy 2 asynchronous engine and sessions
- deterministic database constraint naming
- Alembic asynchronous migration environment
- initial `system_metadata` table
- automatic `alembic upgrade head` before backend startup
- migration smoke test
- downgrade/upgrade migration-cycle test
- database model unit tests
- CI verification of the current schema revision

## Not included yet

- application users or authentication
- frontend
- email accounts
- attachment rules
- storage integrations
- background job workers
- Proxmox installation

## Acceptance criteria

```bash
make init
make check
make test
make up
make api-smoke
make migration-smoke
make migration-cycle
```

All commands must complete successfully from a clean checkout with Docker available. After startup, PostgreSQL must report Alembic revision `0001` and the `system_metadata` table must exist.
