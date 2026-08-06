# Mail Attachment Hub

Mail Attachment Hub is an open-source service for collecting email attachments, applying rules, and delivering files to one or more storage systems.

## Current delivery

**Sprint 0 · Step 003 — FastAPI backend and health API**

This step adds a production-shaped backend foundation:

- FastAPI application running in Docker
- PostgreSQL 16 and Redis 7 dependencies
- `/health/live` process liveness endpoint
- `/health/ready` dependency readiness endpoint
- structured JSON logging
- environment-based configuration
- backend unit tests
- full-stack CI smoke test
- CI support for both `master` and `main`

Email collection, storage providers, authentication, rules, and the frontend are intentionally introduced in later steps.

## Requirements

- Git
- Docker Engine 24+ with Docker Compose v2
- GNU Make
- Bash
- Python 3
- OpenSSL
- curl

## Start

```bash
make init
make check
make test
make up
make api-smoke
make ps
```

Open the development API documentation at:

```text
http://127.0.0.1:8080/docs
```

Health endpoints:

```text
http://127.0.0.1:8080/health/live
http://127.0.0.1:8080/health/ready
```

PostgreSQL, Redis, and the backend are bound to `127.0.0.1` by default.

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
- Step 002: PostgreSQL, Redis and Docker Compose
- **Step 003: FastAPI backend and health API**
- Step 004: database models and Alembic
- Step 005: React frontend shell
- Step 006: authentication foundation
- Step 007: Proxmox installer foundation

See [docs/roadmap.md](docs/roadmap.md).

## Security

Do not commit `.env`. Report vulnerabilities according to [SECURITY.md](SECURITY.md).

## License

MIT
