# Sprint 0 · Step 006

## Goal

Provide the first user-facing web interface for Mail Attachment Hub and connect it to the authentication and health APIs delivered in earlier steps.

## Included

- React 19 and TypeScript frontend
- Vite production build
- Nginx static hosting and reverse proxy
- responsive Swedish login page
- JWT login through `/api/v1/auth/login`
- protected dashboard using `/api/v1/auth/me`
- PostgreSQL and Redis status cards
- session-scoped token storage
- Docker Compose frontend service
- frontend build and smoke checks in CI
- all Step 005 authentication functionality

## Not included yet

- password reset and user administration UI
- email accounts
- IMAP or Gmail OAuth
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
make migration-smoke
make auth-smoke
make frontend-smoke
```

Open `http://127.0.0.1:3000`, log in with the generated administrator credentials, and confirm that the dashboard displays the current user and healthy PostgreSQL and Redis connections.
