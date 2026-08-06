# Backend

FastAPI backend for Mail Attachment Hub.

## Development

The backend runs in Docker and connects asynchronously to PostgreSQL and Redis.

```bash
make init
make test
make up
make api-smoke
make migration-smoke
```

Swagger is available at `http://127.0.0.1:8080/docs` in development mode.

## Database migrations

Apply migrations:

```bash
make migrate
```

Verify the installed revision and first table:

```bash
make migration-smoke
```

Test a full downgrade and upgrade cycle:

```bash
make migration-cycle
```

Create future revisions from inside the backend container:

```bash
docker compose --env-file .env -f compose.yml exec backend \
  alembic revision --autogenerate -m "describe change"
```
