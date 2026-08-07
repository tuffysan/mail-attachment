#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
TARGET_COMMIT="${1:-}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

[[ $EUID -eq 0 ]] || { echo "Run as root inside the LXC."; exit 1; }
[[ -n "$TARGET_COMMIT" ]] || { echo "Usage: mailhub rollback <git-commit>"; exit 1; }

cd "$APP_DIR"

git cat-file -e "${TARGET_COMMIT}^{commit}" 2>/dev/null || {
  echo "Commit '${TARGET_COMMIT}' does not exist locally."
  exit 1
}

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Local changes detected. Rollback aborted."
  git status --short
  exit 1
fi

echo "Rolling back to ${TARGET_COMMIT}..."
git reset --hard "$TARGET_COMMIT"

docker compose --env-file .env "${COMPOSE[@]}" build
docker compose --env-file .env "${COMPOSE[@]}" up -d --remove-orphans

for attempt in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8080/health/live >/dev/null 2>&1; then
    echo "Rollback completed successfully."
    exit 0
  fi
  printf "\rBackend %02d/60" "$attempt"
  sleep 2
done
echo

echo "Rollback completed, but backend health check did not pass."
exit 1
