#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./scripts/require-env.sh

services=(postgres redis backend)
for attempt in {1..60}; do
  all_healthy=1
  for service in "${services[@]}"; do
    container_id="$(docker compose --env-file .env -f compose.yml ps -q "$service")"
    if [[ -z "$container_id" ]]; then
      all_healthy=0
      continue
    fi
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
    if [[ "$health" != "healthy" ]]; then
      all_healthy=0
    fi
  done
  if [[ "$all_healthy" -eq 1 ]]; then
    echo "PostgreSQL, Redis and backend are healthy."
    exit 0
  fi
  sleep 2
done

echo "Services did not become healthy in time." >&2
docker compose --env-file .env -f compose.yml ps >&2
docker compose --env-file .env -f compose.yml logs --tail=100 >&2
exit 1
