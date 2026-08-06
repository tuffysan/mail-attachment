#!/usr/bin/env bash
set -Eeuo pipefail

compose=(docker compose --env-file .env -f compose.yml)

"${compose[@]}" exec -T backend alembic downgrade base
"${compose[@]}" exec -T backend alembic upgrade head
"${compose[@]}" exec -T backend alembic check

printf '%s\n' 'Database migration downgrade/upgrade cycle passed.'
