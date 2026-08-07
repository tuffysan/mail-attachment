# Commit 002F – Part 1E
## Backend integration and self-test

Apply after Parts 1A–1D.

### Fix: pytest production-function collection

`tests/test_storage_platform.py` imported the production function
`test_destination` under a name beginning with `test_`.

Pytest then incorrectly collected the imported production function as a test
and attempted to resolve its parameters as pytest fixtures:

```text
fixture 'provider' not found
```

The production function is now imported as `run_destination_test`, preventing
accidental collection.

### Runtime dependency manifest regression test

Adds `tests/test_dependency_manifest.py` to ensure the backend continues to
declare critical runtime dependencies:

- asyncpg
- redis
- pwdlib
- fastapi
- sqlalchemy
- httpx
- cryptography

### Backend self-test

Adds:

```text
backend/scripts/backend-self-test.sh
```

The script:

1. verifies the runtime Python dependencies can actually be imported;
2. compiles the complete backend source;
3. runs the complete backend pytest suite.

Run it in a backend development/runtime environment where project dependencies
are installed.

### Verification performed while building Part 1E

The broad suite that does not require packages missing from the packaging
environment passes completely.

The packaging environment itself does not include `asyncpg`, `redis`, or
`pwdlib`. All three are already declared in `pyproject.toml`. Their dependent
tests therefore cannot be meaningfully executed in this external packaging
environment; use `backend-self-test.sh` in the real backend/container
environment for that final check.

### Apply

```powershell
git add backend/tests/test_storage_platform.py `
        backend/tests/test_dependency_manifest.py `
        backend/scripts/backend-self-test.sh

git update-index --chmod=+x backend/scripts/backend-self-test.sh

git commit -m "test(backend): stabilize integration suite and add self-test"
git push origin main
```

### LXC verification

After rebuilding the backend:

```bash
pct enter 134
cd /opt/mail-attachment-hub

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend sh -lc '
    cd /app
    python -m compileall -q /app
  '
```

For a source/development environment with pytest installed:

```bash
cd /opt/mail-attachment-hub/backend
./scripts/backend-self-test.sh
```
