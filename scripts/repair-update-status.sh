#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CONTROL_DIR="${CONTROL_DIR:-/var/lib/mailhub-control}"

[[ $EUID -eq 0 ]] || {
  echo "Kör scriptet som root inne i LXC:n."
  exit 1
}

cd "$APP_DIR"

echo "============================================================"
echo " Mail Attachment Hub - Repair Update Status"
echo "============================================================"

echo
echo "[1/6] Fixar filer och rättigheter..."
chmod +x scripts/update-agent.sh

mkdir -p "$CONTROL_DIR"
chown -R 10001:10001 "$CONTROL_DIR"
chmod 0770 "$CONTROL_DIR"

rm -f \
  "$CONTROL_DIR/request.json" \
  "$CONTROL_DIR/status.json.tmp"

echo
echo "[2/6] Skapar giltig initial status.json..."
cat > "$CONTROL_DIR/status.json" <<'JSON'
{
  "state": "idle",
  "installed_commit": null,
  "latest_commit": null,
  "update_available": false,
  "latest_message": null,
  "latest_date": null,
  "checked_at": null,
  "started_at": null,
  "finished_at": null,
  "message": "Update agent ready. Click Check GitHub."
}
JSON

chown 10001:10001 "$CONTROL_DIR/status.json"
chmod 0660 "$CONTROL_DIR/status.json"

echo
echo "[3/6] Startar om systemd watcher..."
systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path
systemctl restart mailhub-update-agent.path

echo "enabled: $(systemctl is-enabled mailhub-update-agent.path)"
echo "active:  $(systemctl is-active mailhub-update-agent.path)"

echo
echo "[4/6] Skickar test: check GitHub..."
cat > "$CONTROL_DIR/request.json" <<'JSON'
{
  "action": "check",
  "requested_at": "repair"
}
JSON

chown 10001:10001 "$CONTROL_DIR/request.json"
chmod 0660 "$CONTROL_DIR/request.json"

echo "Väntar på agent..."
for attempt in $(seq 1 30); do
  if [[ ! -f "$CONTROL_DIR/request.json" ]] && [[ -s "$CONTROL_DIR/status.json" ]]; then
    STATE="$(jq -r '.state // empty' "$CONTROL_DIR/status.json" 2>/dev/null || true)"
    if [[ -n "$STATE" && "$STATE" != "checking" && "$STATE" != "idle" ]]; then
      break
    fi
  fi
  sleep 1
done

echo
echo "[5/6] Verifierar status.json..."
if [[ ! -s "$CONTROL_DIR/status.json" ]]; then
  echo "ERROR: status.json är fortfarande tom." >&2
  journalctl -u mailhub-update-agent.service --no-pager -n 100
  exit 1
fi

jq -e . "$CONTROL_DIR/status.json" >/dev/null

ls -lh "$CONTROL_DIR/status.json"
cat "$CONTROL_DIR/status.json" | jq .

echo
echo "[6/6] Verifierar backendens vy..."
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend python - <<'PY'
import json
from pathlib import Path

p = Path("/control/status.json")
print("size:", p.stat().st_size)
data = json.loads(p.read_text(encoding="utf-8"))
print("state:", data.get("state"))
print("installed_commit:", data.get("installed_commit"))
print("latest_commit:", data.get("latest_commit"))
print("update_available:", data.get("update_available"))
PY

echo
echo "============================================================"
echo " Update status repair complete"
echo "============================================================"
