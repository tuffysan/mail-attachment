# Mail Attachment Hub

Mail Attachment Hub is an open-source service for collecting email attachments, applying rules, and delivering files to one or more storage systems.

## Current delivery

**Sprint 0 · Step 002 — Infrastructure dependencies**

This step provides a reproducible local infrastructure foundation:

- PostgreSQL 16
- Redis 7
- Docker Compose health checks
- generated local secrets
- localhost-only database ports
- CI validation and startup test

The backend and frontend are intentionally introduced in later steps. This commit is independently testable and should remain green before application code is added.

## Requirements

- Git
- Docker Engine 24+ with Docker Compose v2
- GNU Make
- Bash
- Python 3
- OpenSSL

## Start

```bash
make init
make check
make up
make ps
```

PostgreSQL and Redis are bound to `127.0.0.1`, not all host interfaces.

## Stop

```bash
make down
```

Delete all development data:

```bash
make reset
```

## Repository roadmap

- Step 001: repository foundation
- **Step 002: PostgreSQL, Redis and Docker Compose**
- Step 003: FastAPI backend and health API
- Step 004: database models and Alembic
- Step 005: React frontend shell
- Step 006: authentication foundation
- Step 007: Proxmox installer foundation

See [docs/roadmap.md](docs/roadmap.md).

## Security

Do not commit `.env`. Report vulnerabilities according to [SECURITY.md](SECURITY.md).

## License

MIT
