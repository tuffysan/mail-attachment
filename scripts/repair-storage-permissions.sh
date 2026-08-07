#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i LXC:n."
  exit 1
}

cd "$APP_DIR"

echo "============================================================"
echo " Mail Attachment Hub - Repair Storage Permissions"
echo "============================================================"

echo
echo "[1/3] Reparerar ägare och Unix-rättigheter..."
docker compose \
  --env-file .env \
  "${COMPOSE[@]}" \
  run --rm --no-deps storage-init

echo
echo "[2/3] Återskapar backend och worker så mounts verifieras på nytt..."
docker compose \
  --env-file .env \
  "${COMPOSE[@]}" \
  up -d --force-recreate backend worker

echo
echo "[3/3] Kör self-test..."
chmod +x scripts/storage-self-test.sh
./scripts/storage-self-test.sh

echo
echo "Storage permissions repaired successfully."
