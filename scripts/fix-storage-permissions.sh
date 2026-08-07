#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
COMPOSE=(
  --env-file .env
  -f compose.yml
  -f compose.override.lxc.yml
)

[[ $EUID -eq 0 ]] || {
  echo "Kör scriptet som root inne i LXC:n."
  exit 1
}

cd "$APP_DIR"

echo
echo "============================================================"
echo " Mail Attachment Hub - Storage Permission Repair"
echo "============================================================"
echo

echo "1. Kör storage-init..."
docker compose "${COMPOSE[@]}" run --rm storage-init

echo
echo "2. Startar om backend och worker..."
docker compose "${COMPOSE[@]}" up -d --force-recreate backend worker

echo
echo "3. Väntar på backend..."
for attempt in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8080/health/live >/dev/null 2>&1; then
    echo "Backend: OK"
    break
  fi
  printf "\rKontroll %02d/60" "$attempt"
  sleep 2
done
echo

echo "4. Verifierar rättigheter som backend-användaren..."
docker compose "${COMPOSE[@]}" exec -T backend python - <<'PY'
import os
from pathlib import Path

failed = False

for value in ("/data/routed", "/data/attachments"):
    path = Path(value)
    stat = path.stat()
    print(
        f"{value}: "
        f"uid={stat.st_uid} "
        f"gid={stat.st_gid} "
        f"mode={oct(stat.st_mode & 0o777)} "
        f"writable={os.access(path, os.W_OK)}"
    )

    probe = path / ".mailhub-permission-test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        print(f"  write test: OK")
    except OSError as exc:
        failed = True
        print(f"  write test: FAILED - {exc}")

if failed:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " Storage permissions repaired successfully"
echo "============================================================"
