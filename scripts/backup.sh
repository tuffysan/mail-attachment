#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"
source .env

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="${1:-backups/mailhub-$timestamp}"

if [[ "$output" != /* ]]; then
  output="$APP_DIR/$output"
fi

mkdir -p "$output"
output="$(readlink -f "$output")"
chmod 0700 "$output"

echo "Creating database backup..."
docker compose --env-file .env -f compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  > "$output/database.dump"

test -s "$output/database.dump"

echo "Creating attachment backup..."
docker run --rm \
  -v "${COMPOSE_PROJECT_NAME:-mail-attachment-hub}_attachment_data:/source:ro" \
  -v "$output:/backup" \
  alpine:3.22 \
  tar czf /backup/attachments.tgz -C /source .

echo "Creating routed-file backup..."
docker run --rm \
  -v "${COMPOSE_PROJECT_NAME:-mail-attachment-hub}_routed_data:/source:ro" \
  -v "$output:/backup" \
  alpine:3.22 \
  tar czf /backup/routed.tgz -C /source .

cp .env "$output/env.backup"
chmod 0600 "$output/env.backup"

git rev-parse HEAD > "$output/git-commit.txt" 2>/dev/null || true
date --iso-8601=seconds > "$output/created-at.txt"

(
  cd "$output"
  sha256sum database.dump attachments.tgz routed.tgz env.backup \
    > SHA256SUMS
)

(
  cd "$output"
  sha256sum -c SHA256SUMS
)

echo "Backup created: $output"
