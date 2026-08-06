#!/usr/bin/env bash
set -Eeuo pipefail
backup="${1:?Usage: scripts/restore.sh BACKUP_DIRECTORY}"
source .env
test -f "$backup/database.dump"
docker compose --env-file .env -f compose.yml up -d postgres
docker compose --env-file .env -f compose.yml exec -T postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$backup/database.dump"
for name in attachment_data routed_data; do
  archive="$backup/${name%_data}s.tgz"
  test -f "$archive" || continue
  docker run --rm -v "${COMPOSE_PROJECT_NAME:-mail-attachment-hub}_${name}:/target" \
    -v "$(pwd)/$backup:/backup:ro" alpine sh -c "rm -rf /target/* && tar xzf /backup/$(basename "$archive") -C /target"
done
docker compose --env-file .env -f compose.yml up -d --build
echo "Restore completed."
