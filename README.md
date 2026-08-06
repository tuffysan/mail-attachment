# Mail Attachment Hub

Mail Attachment Hub is an open-source service for collecting email attachments and routing them to configured storage destinations. The project is built incrementally, with every step remaining runnable and reviewable.

## Current delivery

**Sprint 0 · Step 007 — multiple IMAP accounts and connection testing**

The repository currently provides:

- FastAPI backend and React web interface
- local administrator login with JWT
- PostgreSQL 16 and Redis 7
- asynchronous SQLAlchemy and Alembic migrations
- multiple encrypted IMAP email accounts
- authenticated email-account CRUD API
- IMAP mailbox connection testing
- Swedish account-management interface
- liveness and dependency-aware readiness endpoints
- Docker Compose healthchecks and GitHub Actions CI

Gmail OAuth, mailbox polling, attachment extraction, routing rules, storage integrations and the Proxmox production installer arrive in later steps.

## Requirements

- Git
- Docker Engine with Docker Compose v2
- GNU Make and Bash for convenience commands

Windows users can use WSL 2 or Git Bash, or invoke Docker Compose directly.

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
make email-account-smoke
```

Open:

- Web UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8080/docs`

The generated administrator credentials are written to the local `.env` file by `make init`. Never commit `.env`.

## IMAP accounts

After signing in, open **E-postkonton**. For Gmail with an app password use:

- Server: `imap.gmail.com`
- Port: `993`
- SSL/TLS: enabled
- Username: full Gmail address
- Password: Google app password

Native Gmail OAuth/XOAUTH2 is planned for the next OAuth delivery.

## Common commands

```bash
make help
make ps
make logs
make down
make reset
```

Read `STEP.md` for the exact scope and acceptance criteria.
