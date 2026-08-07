#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CONTROL_DIR="/var/lib/mailhub-control"

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i LXC:n."
  exit 1
}

command -v jq >/dev/null 2>&1 || {
  apt-get update
  apt-get install -y jq
}

command -v flock >/dev/null 2>&1 || {
  apt-get update
  apt-get install -y util-linux
}

mkdir -p "$CONTROL_DIR"
chown 10001:10001 "$CONTROL_DIR"
chmod 0770 "$CONTROL_DIR"

if [[ ! -f "$CONTROL_DIR/status.json" ]]; then
  cat > "$CONTROL_DIR/status.json" <<EOF
{
  "state": "idle",
  "installed_commit": null,
  "latest_commit": null,
  "update_available": false,
  "message": "Uppdateringshanteraren är installerad. Kontrollera GitHub från webbgränssnittet."
}
EOF
fi

chown 10001:10001 "$CONTROL_DIR/status.json"
chmod 0644 "$CONTROL_DIR/status.json"

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
EOF

cat > /etc/systemd/system/mailhub-update-agent.path <<EOF
[Unit]
Description=Watch for Mail Attachment Hub web update requests

[Path]
PathChanged=${CONTROL_DIR}/request.json
Unit=mailhub-update-agent.service

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path

echo "Mail Attachment Hub web update agent installed."
echo "Control directory: ${CONTROL_DIR}"
