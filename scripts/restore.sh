#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"

backup="${1:?Usage: scripts/restore.sh BACKUP_DIRECTORY}"

if [[ "$backup" != /* ]]; then
  backup="$APP_DIR/$backup"
fi
backup="$(readlink -f "$backup")"

test -d "$backup"
test -s "$backup/database.dump"
test -s "$backup/env.backup"
test -s "$backup/SHA256SUMS"

echo "Verifying backup checksums..."
(
  cd "$backup"
  sha256sum -c SHA256SUMS
)

# Preserve infrastructure settings that identify the CURRENT PostgreSQL
# cluster, Docker volumes and externally exposed ports. The backup's
# APP_SECRET_KEY and application settings are restored because encrypted
# credentials in the database depend on the matching secret key.
source .env

CURRENT_POSTGRES_DB="${POSTGRES_DB}"
CURRENT_POSTGRES_USER="${POSTGRES_USER}"
CURRENT_POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
CURRENT_COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-mail-attachment-hub}"
CURRENT_FRONTEND_BIND_ADDRESS="${FRONTEND_BIND_ADDRESS:-0.0.0.0}"
CURRENT_FRONTEND_PORT="${FRONTEND_PORT:-3000}"
CURRENT_BACKEND_BIND_ADDRESS="${BACKEND_BIND_ADDRESS:-0.0.0.0}"
CURRENT_BACKEND_PORT="${BACKEND_PORT:-8080}"

replace_env() {
  local file="$1"
  local key="$2"
  local value="$3"

  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

echo "Stopping application services before restore..."
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
  stop backend worker frontend || true

echo "Starting current PostgreSQL cluster..."
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
  up -d postgres redis

for attempt in $(seq 1 60); do
  if docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
    exec -T postgres \
    pg_isready -U "$CURRENT_POSTGRES_USER" -d "$CURRENT_POSTGRES_DB" \
    >/dev/null 2>&1
  then
    break
  fi

  [[ "$attempt" == 60 ]] && {
    echo "PostgreSQL blev inte redo för restore." >&2
    exit 1
  }

  sleep 1
done

echo "Restoring database..."
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
  exec -T postgres \
  pg_restore \
    -U "$CURRENT_POSTGRES_USER" \
    -d "$CURRENT_POSTGRES_DB" \
    --clean \
    --if-exists \
    --no-owner \
  < "$backup/database.dump"

restore_volume() {
  local volume="$1"
  local archive="$2"

  [[ -s "$backup/$archive" ]] || return 0

  docker run --rm \
    -v "${CURRENT_COMPOSE_PROJECT_NAME}_${volume}:/target" \
    -v "$backup:/backup:ro" \
    alpine:3.22 \
    sh -ec \
    "find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar xzf /backup/$archive -C /target"
}

echo "Restoring attachments..."
restore_volume attachment_data attachments.tgz

echo "Restoring routed files..."
restore_volume routed_data routed.tgz

echo "Restoring matching application environment..."
cp "$backup/env.backup" .env
chmod 0600 .env

replace_env .env POSTGRES_DB "$CURRENT_POSTGRES_DB"
replace_env .env POSTGRES_USER "$CURRENT_POSTGRES_USER"
replace_env .env POSTGRES_PASSWORD "$CURRENT_POSTGRES_PASSWORD"
replace_env .env COMPOSE_PROJECT_NAME "$CURRENT_COMPOSE_PROJECT_NAME"
replace_env .env FRONTEND_BIND_ADDRESS "$CURRENT_FRONTEND_BIND_ADDRESS"
replace_env .env FRONTEND_PORT "$CURRENT_FRONTEND_PORT"
replace_env .env BACKEND_BIND_ADDRESS "$CURRENT_BACKEND_BIND_ADDRESS"
replace_env .env BACKEND_PORT "$CURRENT_BACKEND_PORT"

echo "Repairing application storage permissions..."
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
  run --rm --no-deps storage-init

echo "Starting restored stack..."
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml \
  up -d --build --remove-orphans

echo "Restore completed."
