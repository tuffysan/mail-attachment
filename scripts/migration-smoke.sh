#!/usr/bin/env bash
set -Eeuo pipefail

compose=(docker compose --env-file .env -f compose.yml)

"${compose[@]}" exec -T backend alembic current | grep -q '0002 (head)'
"${compose[@]}" exec -T postgres sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT to_regclass('"'"'public.system_metadata'"'"')"' \
  | grep -qx 'system_metadata'

printf '%s\n' 'Database migration smoke test passed.'
