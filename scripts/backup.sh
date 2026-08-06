#!/usr/bin/env bash
set -Eeuo pipefail
source .env
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="${1:-backups/mailhub-$timestamp}"
mkdir -p "$output"
docker compose --env-file .env -f compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$output/database.dump"
docker run --rm -v "${COMPOSE_PROJECT_NAME:-mail-attachment-hub}_attachment_data:/source:ro" \
  -v "$(pwd)/$output:/backup" alpine tar czf /backup/attachments.tgz -C /source .
docker run --rm -v "${COMPOSE_PROJECT_NAME:-mail-attachment-hub}_routed_data:/source:ro" \
  -v "$(pwd)/$output:/backup" alpine tar czf /backup/routed.tgz -C /source .
cp .env "$output/env.backup"
chmod 600 "$output/env.backup"
sha256sum "$output"/* > "$output/SHA256SUMS"
echo "Backup created: $output"
