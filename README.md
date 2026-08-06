# Mail Attachment Hub

Mail Attachment Hub is an open-source service that securely collects email attachments and routes them to configured storage destinations.

## Current delivery
**Sprint 0 · Step 008 — complete email ingestion engine**

This snapshot includes:
- FastAPI, React, PostgreSQL and Redis
- local administrator login and JWT
- encrypted multi-account IMAP configuration
- Gmail and Microsoft 365 OAuth/XOAUTH2 foundations
- scheduled worker and manual sync
- UID-based incremental mailbox scanning
- MIME and attachment extraction
- bounded ZIP expansion
- duplicate protection, retry runs and activity history
- persistent attachment staging volume
- Docker Compose and GitHub Actions tests

Rules and external storage routing arrive in Steps 009–010.

## Start
```bash
make init
make check
make test
make up
make mail-engine-smoke
```

Open:
- UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8080/docs`

## OAuth
Add OAuth app credentials to `.env`:
```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_TENANT_ID=common
```
Register callback URLs shown by the API host:
- `/api/v1/oauth/google/callback`
- `/api/v1/oauth/microsoft/callback`

## Data safety
Passwords and OAuth tokens are encrypted with a key derived from `APP_SECRET_KEY`. Never change that secret after accounts have been configured unless credentials are re-entered.
