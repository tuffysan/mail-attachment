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

cd "$APP_DIR"

echo "============================================================"
echo " Mail Attachment Hub - Repair Update Agent"
echo "============================================================"

chmod +x \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh

./scripts/install-update-agent.sh

echo
echo "[1/4] Systemd"
systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path
echo "enabled: $(systemctl is-enabled mailhub-update-agent.path)"
echo "active:  $(systemctl is-active mailhub-update-agent.path)"

echo
echo "[2/4] Control directory"
stat -c 'owner=%u:%g mode=%a path=%n' "$CONTROL_DIR"
jq -e . "$CONTROL_DIR/status.json" >/dev/null
echo "status.json: valid ($(stat -c '%s' "$CONTROL_DIR/status.json") bytes)"

echo
echo "[3/4] Backend mount"
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --force-recreate backend

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend sh -ec '
    test -r /control/status.json
    test -s /control/status.json
    touch /control/.repair-write-test
    rm -f /control/.repair-write-test
    echo "Backend /control: READ_OK WRITE_OK"
  '

echo
echo "[4/4] End-to-end GitHub check"
tmp="$CONTROL_DIR/.repair-request.tmp"
jq -n \
  --arg requested_at "$(date --iso-8601=seconds)" \
  '{action:"check", requested_at:$requested_at}' > "$tmp"
chown "$BACKEND_UID:$BACKEND_GID" "$tmp"
chmod 0660 "$tmp"
mv -f "$tmp" "$CONTROL_DIR/request.json"

done_flag=0
for attempt in $(seq 1 45); do
  if [[ ! -f "$CONTROL_DIR/request.json" ]] &&
     [[ -s "$CONTROL_DIR/status.json" ]] &&
     jq -e . "$CONTROL_DIR/status.json" >/dev/null 2>&1; then
    state="$(jq -r '.state // empty' "$CONTROL_DIR/status.json")"
    if [[ -n "$state" && "$state" != "idle" && "$state" != "checking" ]]; then
      done_flag=1
      break
    fi
  fi
  sleep 1
done

if [[ "$done_flag" != 1 ]]; then
  echo "Agenttest timeout." >&2
  journalctl -u mailhub-update-agent.service --no-pager -n 100 || true
  exit 1
fi

cat "$CONTROL_DIR/status.json" | jq .

if [[ "$state" == "error" ]]; then
  echo "GitHub-kontrollen gav fel. Se $CONTROL_DIR/update.log." >&2
  tail -100 "$CONTROL_DIR/update.log" || true
  exit 1
fi

echo
echo "Update Agent: OK"
