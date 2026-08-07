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

for package in jq util-linux; do
  dpkg -s "$package" >/dev/null 2>&1 || {
    apt-get update
    apt-get install -y "$package"
  }
done

[[ -d "$APP_DIR" ]] || {
  echo "Applikationskatalogen saknas: $APP_DIR"
  exit 1
}

mkdir -p "$CONTROL_DIR"

# Remove stale request files before enabling the watcher.
rm -f "$CONTROL_DIR/request.json" "$CONTROL_DIR"/.request-*.tmp

# The Docker backend runs as 10001:10001.
chown -R "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR"
chmod 0770 "$CONTROL_DIR"

if [[ ! -f "$CONTROL_DIR/status.json" ]]; then
  cat > "$CONTROL_DIR/status.json" <<EOF
{
  "state": "idle",
  "installed_commit": null,
  "latest_commit": null,
  "update_available": false,
  "message": "Uppdateringshanteraren är installerad. Kontrollera GitHub."
}
EOF
fi

chown "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR/status.json"
chmod 0660 "$CONTROL_DIR/status.json"

touch "$CONTROL_DIR/update.log"
chown "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR/update.log"
chmod 0660 "$CONTROL_DIR/update.log"

chmod +x \
  "$APP_DIR/scripts/update-agent.sh" \
  "$APP_DIR/scripts/lxc-update.sh"

cat > /etc/systemd/system/mailhub-update-agent.service <<EOF
[Unit]
Description=Mail Attachment Hub update agent
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/scripts/update-agent.sh
User=root
Group=root
EOF

cat > /etc/systemd/system/mailhub-update-agent.path <<EOF
[Unit]
Description=Watch for Mail Attachment Hub web update requests

[Path]
PathExists=${CONTROL_DIR}/request.json
Unit=mailhub-update-agent.service

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path

# Verify host-side write permissions from the numeric backend identity.
if command -v setpriv >/dev/null 2>&1; then
  setpriv \
    --reuid="$BACKEND_UID" \
    --regid="$BACKEND_GID" \
    --clear-groups \
    sh -c "touch '$CONTROL_DIR/.host-write-test' && rm -f '$CONTROL_DIR/.host-write-test'"
fi

echo
echo "Mail Attachment Hub web update agent installerad."
echo "Control directory: ${CONTROL_DIR}"
echo "Owner: $(stat -c '%u:%g' "$CONTROL_DIR")"
echo "Mode:  $(stat -c '%a' "$CONTROL_DIR")"
echo "Watcher: $(systemctl is-active mailhub-update-agent.path)"
