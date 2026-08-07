#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"

[[ $EUID -eq 0 ]] || { echo "Run as root."; exit 1; }

chmod +x \
  "$APP_DIR/scripts/mailhub" \
  "$APP_DIR/scripts/lxc-update.sh" \
  "$APP_DIR/scripts/lxc-rollback.sh"

ln -sf "$APP_DIR/scripts/mailhub" /usr/local/bin/mailhub

echo "Mail Attachment Hub CLI installed."
echo "Use: mailhub update"
