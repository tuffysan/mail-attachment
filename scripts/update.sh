#!/usr/bin/env bash
set -Eeuo pipefail
branch="${BRANCH:-main}"
git fetch origin "$branch"
scripts/backup.sh
git pull --ff-only origin "$branch"
docker compose --env-file .env -f compose.yml build --pull
docker compose --env-file .env -f compose.yml up -d
docker compose --env-file .env -f compose.yml exec -T backend alembic upgrade head
scripts/doctor.sh
