# Backend

FastAPI backend introduced in Sprint 0 · Step 003.

## Endpoints

- `GET /` — service metadata
- `GET /health/live` — process liveness
- `GET /health/ready` — PostgreSQL and Redis readiness

## Local tests

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
```

The supported project workflow uses Docker Compose from the repository root.
