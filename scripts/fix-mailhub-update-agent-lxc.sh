#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CONTROL_DIR="${CONTROL_DIR:-/var/lib/mailhub-control}"
BACKEND_UID="${BACKEND_UID:-10001}"
BACKEND_GID="${BACKEND_GID:-10001}"

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i LXC:n."
  exit 1
}

echo "============================================================"
echo " Mail Attachment Hub - Fix GitHub Update Agent"
echo "============================================================"

cd "$APP_DIR"

echo
echo "[1/7] Kontrollerar filer..."
for f in \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh
do
  if [[ ! -f "$f" ]]; then
    echo "Saknar $f"
    echo "Hämta först senaste kod:"
    echo "  git pull --ff-only origin main"
    exit 1
  fi
done

echo
echo "[2/7] Sätter rättigheter på kontrollkatalog..."
mkdir -p "$CONTROL_DIR"
rm -f "$CONTROL_DIR/request.json" "$CONTROL_DIR"/.request-*.tmp
chown -R "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR"
chmod 0770 "$CONTROL_DIR"

echo
echo "[3/7] Installerar update-agent..."
chmod +x \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh

./scripts/install-update-agent.sh

echo
echo "[4/7] Verifierar systemd..."
systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path

echo "Enabled: $(systemctl is-enabled mailhub-update-agent.path)"
echo "Active:  $(systemctl is-active mailhub-update-agent.path)"

echo
echo "[5/7] Återskapar backend med korrekt /control mount..."
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --force-recreate backend

echo
echo "[6/7] Verifierar backend-skrivåtkomst..."
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend python - <<'PY'
import os
from pathlib import Path

control = Path("/control")
s = control.stat()

print("Backend identity:")
print("  UID:", os.getuid())
print("  GID:", os.getgid())

print("Control directory:")
print("  UID:", s.st_uid)
print("  GID:", s.st_gid)
print("  Mode:", oct(s.st_mode & 0o777))
print("  Writable:", os.access(control, os.W_OK))

probe = control / ".mailhub-write-test"
probe.write_text("ok", encoding="utf-8")
probe.unlink()

print("Write test: OK")
PY

echo
echo "[7/7] Testar update-agent..."
cat > "$CONTROL_DIR/request.json" <<EOF
{"action":"check","requested_at":"manual-repair"}
EOF

chown "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR/request.json"
chmod 0660 "$CONTROL_DIR/request.json"

for attempt in $(seq 1 30); do
  if [[ ! -f "$CONTROL_DIR/request.json" ]]; then
    break
  fi
  sleep 1
done

echo
echo "Status:"
if [[ -f "$CONTROL_DIR/status.json" ]]; then
  jq . "$CONTROL_DIR/status.json"
else
  echo "status.json saknas."
  journalctl -u mailhub-update-agent.service --no-pager -n 100
  exit 1
fi

echo
echo "============================================================"
echo " GitHub Update Agent fungerar"
echo "============================================================"
