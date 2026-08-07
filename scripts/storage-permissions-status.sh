#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
cd "$APP_DIR"

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend python - <<'PY'
import os
from pathlib import Path

for value in ("/data/routed", "/data/attachments"):
    path = Path(value)
    info = path.stat()
    print(
        f"{value}\n"
        f"  UID:      {info.st_uid}\n"
        f"  GID:      {info.st_gid}\n"
        f"  Mode:     {oct(info.st_mode & 0o777)}\n"
        f"  Writable: {os.access(path, os.W_OK)}"
    )
PY
