#!/usr/bin/env bash
set -Eeuo pipefail

required=(
  backend/alembic.ini
  backend/alembic/env.py
  backend/alembic/versions/0001_create_system_metadata.py
  backend/alembic/versions/0002_create_users.py
  backend/src/mailhub/db/base.py
  backend/src/mailhub/db/models.py
  backend/src/mailhub/db/session.py
  backend/entrypoint.sh
  scripts/migration-smoke.sh
  scripts/migration-cycle.sh
)

for path in "${required[@]}"; do
  [[ -f "$path" ]] || { printf 'Missing migration file: %s\n' "$path" >&2; exit 1; }
done

grep -q 'alembic upgrade head' backend/entrypoint.sh
grep -q 'postgresql+asyncpg://' compose.yml
grep -q 'sqlalchemy\[asyncio\]' backend/pyproject.toml
grep -q 'alembic>=' backend/pyproject.toml
grep -q 'system_metadata' backend/alembic/versions/0001_create_system_metadata.py
grep -q 'users' backend/alembic/versions/0002_create_users.py

printf '%s\n' 'Migration static checks passed.'
