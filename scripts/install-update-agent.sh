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

STATUS_FILE="$CONTROL_DIR/status.json"

# Repair a missing, empty or invalid status file. A zero-byte status.json was
# the root cause of the UI incorrectly reporting that the agent was missing.
if [[ ! -s "$STATUS_FILE" ]] || ! jq -e . "$STATUS_FILE" >/dev/null 2>&1; then
  STATUS_TMP="${STATUS_FILE}.install.tmp"
  jq -n \
    --arg message "Uppdateringshanteraren är installerad. Kontrollera GitHub." \
    '{
      state: "idle",
      installed_commit: null,
      latest_commit: null,
      update_available: false,
      latest_message: null,
      latest_date: null,
      checked_at: null,
      started_at: null,
      finished_at: null,
      message: $message
    }' > "$STATUS_TMP"

  [[ -s "$STATUS_TMP" ]] || {
    echo "Kunde inte skapa en giltig status.json." >&2
    exit 1
  }

  jq -e . "$STATUS_TMP" >/dev/null
  chown "${BACKEND_UID}:${BACKEND_GID}" "$STATUS_TMP"
  chmod 0660 "$STATUS_TMP"
  mv -f "$STATUS_TMP" "$STATUS_FILE"
fi

chown "${BACKEND_UID}:${BACKEND_GID}" "$STATUS_FILE"
chmod 0660 "$STATUS_FILE"

touch "$CONTROL_DIR/update.log"
chown "${BACKEND_UID}:${BACKEND_GID}" "$CONTROL_DIR/update.log"
chmod 0660 "$CONTROL_DIR/update.log"

touch "$CONTROL_DIR/update.lock"
chown root:root "$CONTROL_DIR/update.lock"
chmod 0644 "$CONTROL_DIR/update.lock"

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

# Final installer-side validation.
[[ "$(stat -c '%u:%g' "$CONTROL_DIR")" == "${BACKEND_UID}:${BACKEND_GID}" ]] || {
  echo "Fel ägare på ${CONTROL_DIR}." >&2
  exit 1
}

[[ -s "$STATUS_FILE" ]] || {
  echo "${STATUS_FILE} är tom." >&2
  exit 1
}

jq -e . "$STATUS_FILE" >/dev/null || {
  echo "${STATUS_FILE} innehåller ogiltig JSON." >&2
  exit 1
}

[[ "$(systemctl is-enabled mailhub-update-agent.path 2>/dev/null || true)" == "enabled" ]] || {
  echo "mailhub-update-agent.path är inte enabled." >&2
  exit 1
}

[[ "$(systemctl is-active mailhub-update-agent.path 2>/dev/null || true)" == "active" ]] || {
  echo "mailhub-update-agent.path är inte active." >&2
  exit 1
}

echo
echo "Mail Attachment Hub web update agent installerad."
echo "Control directory: ${CONTROL_DIR}"
echo "Owner: $(stat -c '%u:%g' "$CONTROL_DIR")"
echo "Mode:  $(stat -c '%a' "$CONTROL_DIR")"
echo "Status JSON: valid ($(stat -c '%s' "$STATUS_FILE") bytes)"
echo "Watcher: $(systemctl is-active mailhub-update-agent.path)"
