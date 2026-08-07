#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CREDENTIALS_FILE="${CREDENTIALS_FILE:-/root/mailhub-credentials.env}"
OUTPUT_FILE="${OUTPUT_FILE:-/root/mailhub-install-info.txt}"

cd "$APP_DIR"

if [[ -f "$CREDENTIALS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CREDENTIALS_FILE"
fi

WEB_PORT="${WEB_PORT:-$(sed -n 's/^FRONTEND_PORT=//p' .env | tail -1)}"
API_PORT="${API_PORT:-$(sed -n 's/^BACKEND_PORT=//p' .env | tail -1)}"
ADMIN_EMAIL="${ADMIN_EMAIL:-$(sed -n 's/^ADMIN_EMAIL=//p' .env | tail -1)}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(sed -n 's/^ADMIN_PASSWORD=//p' "$CREDENTIALS_FILE" 2>/dev/null | tail -1)}"

WEB_PORT="${WEB_PORT:-3000}"
API_PORT="${API_PORT:-8080}"
ADMIN_EMAIL="${ADMIN_EMAIL:-unknown}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-unknown}"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
IP="${IP:-CONTAINER-IP}"
VERSION="$(cat VERSION 2>/dev/null || echo unknown)"
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

umask 077
cat > "$OUTPUT_FILE" <<EOF
============================================================
 Mail Attachment Hub
============================================================
Hostname:  $(hostname)
IP:        ${IP}
Web UI:    http://${IP}:${WEB_PORT}
API:       http://${IP}:${API_PORT}

Login:
Email:     ${ADMIN_EMAIL}
Password:  ${ADMIN_PASSWORD}

Version:
${VERSION}

Installed commit:
${COMMIT}

Useful commands:
mailhub credentials
mailhub status
mailhub doctor
mailhub verify
mailhub logs backend
mailhub update
mailhub backups
mailhub rollback latest
mailhub repair storage
mailhub repair update-agent
============================================================
EOF

chmod 0600 "$OUTPUT_FILE"
cat "$OUTPUT_FILE"
