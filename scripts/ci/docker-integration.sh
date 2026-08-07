#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

cleanup() {
  docker compose --env-file .env -f compose.yml down --volumes --remove-orphans \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "============================================================"
echo " Mail Attachment Hub - Docker Integration CI"
echo "============================================================"

make init
make config

echo
echo "[1/9] Build and start"
make up

echo
echo "[2/9] API"
make api-smoke

echo
echo "[3/9] Database migrations"
make migration-smoke
make migration-cycle

echo
echo "[4/9] Authentication"
make auth-smoke

echo
echo "[5/9] Frontend"
make frontend-smoke

echo
echo "[6/9] Email accounts"
make email-account-smoke

echo
echo "[7/9] Mail engine"
make mail-engine-smoke

echo
echo "[8/9] Rules"
make rule-engine-smoke

echo
echo "[9/9] Storage platform"
make storage-platform-smoke

echo
docker compose --env-file .env -f compose.yml ps

echo
echo "Docker Integration CI: PASSED"
