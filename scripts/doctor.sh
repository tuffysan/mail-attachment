#!/usr/bin/env bash
set -Eeuo pipefail
source .env
echo "== Docker =="
docker version --format '{{.Server.Version}}'
docker compose version
echo "== Configuration =="
docker compose --env-file .env -f compose.yml config --quiet
echo "== Services =="
docker compose --env-file .env -f compose.yml ps
echo "== Health =="
curl -fsS "http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}/health/ready"
echo
echo "== Migration =="
docker compose --env-file .env -f compose.yml exec -T backend alembic current
echo "Diagnostics passed."
