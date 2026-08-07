#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"

[[ $EUID -eq 0 ]] || {
  echo "Run this command as root inside the LXC."
  exit 1
}

cd "$APP_DIR"

echo "Repairing Mail Attachment Hub volume ownership..."
docker compose --env-file .env -f compose.yml run --rm storage-init

echo "Restarting backend and worker..."
docker compose --env-file .env -f compose.yml up -d --force-recreate backend worker

echo
echo "Current permissions:"
docker compose --env-file .env -f compose.yml exec -T backend \
  python -c '
import os
from pathlib import Path
for value in ("/data/routed", "/data/attachments"):
    p = Path(value)
    s = p.stat()
    print(value, "uid=", s.st_uid, "gid=", s.st_gid, "mode=", oct(s.st_mode & 0o777), "writable=", os.access(p, os.W_OK))
'
