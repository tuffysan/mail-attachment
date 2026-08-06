# Sprint 0 · Step 005

## Goal
Add secure local users, first-run administrator bootstrap and JWT authentication to the FastAPI backend.

## Included
- `users` database table and Alembic revision `0002`
- Argon2 password hashing
- bootstrap administrator from environment variables
- JWT access tokens
- `POST /api/v1/auth/login`
- protected `GET /api/v1/auth/me`
- authentication unit and smoke tests

## Not included yet
- browser frontend
- password reset and invitations
- email accounts, rules or storage integrations

## Acceptance criteria

```bash
make init
make check
make test
make up
make api-smoke
make migration-smoke
make auth-smoke
```
