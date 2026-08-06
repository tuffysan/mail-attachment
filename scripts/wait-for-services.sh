#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./scripts/require-env.sh

for service in postgres redis; do
  echo "Waiting for ${service}..."
  for attempt in $(seq 1 60); do
    container_id="$(docker compose --env-file .env -f compose.yml ps -q "$service")"
    if [[ -n "$container_id" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
      if [[ "$status" == 'healthy' ]]; then
        echo "${service} is healthy."
        break
      fi
    fi
    if [[ "$attempt" -eq 60 ]]; then
      echo "${service} did not become healthy." >&2
      docker compose --env-file .env -f compose.yml logs --tail=100 "$service" >&2
      exit 1
    fi
    sleep 2
  done
done
