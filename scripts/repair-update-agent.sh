#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CONTROL_DIR="${CONTROL_DIR:-/var/lib/mailhub-control}"
COMPOSE=(
  --env-file .env
  -f compose.yml
  -f compose.override.lxc.yml
)

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i LXC:n."
  exit 1
}

cd "$APP_DIR"

echo "1. Installerar/reparerar update-agent..."
chmod +x scripts/install-update-agent.sh scripts/update-agent.sh scripts/lxc-update.sh
./scripts/install-update-agent.sh

echo
echo "2. Återskapar backend så /control-mounten verifieras..."
docker compose "${COMPOSE[@]}" up -d --force-recreate backend

echo
echo "3. Kontrollerar /control från backend..."
docker compose "${COMPOSE[@]}" exec -T backend python - <<'PY'
import json
import os
from pathlib import Path

control = Path("/control")
print("Path:", control)
print("Exists:", control.exists())

info = control.stat()
print("UID:", info.st_uid)
print("GID:", info.st_gid)
print("Mode:", oct(info.st_mode & 0o777))
print("Writable:", os.access(control, os.W_OK))

probe = control / ".backend-write-test"
probe.write_text("ok", encoding="utf-8")
probe.unlink()

status = control / "status.json"
if status.exists():
    print("Status:", json.loads(status.read_text(encoding="utf-8")).get("state"))
print("Backend write test: OK")
PY

echo
echo "4. Kontrollerar systemd-watcher..."
systemctl --no-pager --full status mailhub-update-agent.path || true

echo
echo "============================================================"
echo " Web Update Agent repaired successfully"
echo "============================================================"
