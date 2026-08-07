#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
BRANCH="${BRANCH:-main}"
REMOTE="${REMOTE:-origin}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

log() {
  printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"
}

ROLLBACK_READY=0
ROLLBACK_RUNNING=0
BACKUP_DIR=""
on_update_error() {
  local code=$?
  echo "Update failed with exit code ${code}." >&2
  if [[ "$ROLLBACK_RUNNING" == 0 && "$ROLLBACK_READY" == 1 && -n "$BACKUP_DIR" && -x ./scripts/lxc-rollback.sh ]]; then
    echo "Automatic rollback starting..." >&2
    ROLLBACK_RUNNING=1
    trap - ERR
    ./scripts/lxc-rollback.sh "$BACKUP_DIR" || echo "Automatic rollback failed." >&2
  fi
  exit "$code"
}
trap on_update_error ERR

[[ $EUID -eq 0 ]] || { echo "Run as root inside the LXC."; exit 1; }

cd "$APP_DIR"

command -v git >/dev/null 2>&1 || { echo "git is not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is not installed."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "docker compose is unavailable."; exit 1; }

CURRENT_COMMIT="$(git rev-parse HEAD)"

log "Checking GitHub"
git fetch "$REMOTE" "$BRANCH"
TARGET_COMMIT="$(git rev-parse "${REMOTE}/${BRANCH}")"

if [[ "$CURRENT_COMMIT" == "$TARGET_COMMIT" ]]; then
  echo "Mail Attachment Hub is already up to date."
  echo "Commit: ${CURRENT_COMMIT}"
  exit 0
fi

echo "Current commit: ${CURRENT_COMMIT}"
echo "Target commit:  ${TARGET_COMMIT}"

log "Checking local changes"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Local changes detected. Update aborted."
  git status --short
  exit 1
fi

log "Creating pre-update backup"
BACKUP_DIR="/root/mailhub-update-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
chmod 0700 "$BACKUP_DIR"
cp .env "$BACKUP_DIR/.env"
chmod 0600 "$BACKUP_DIR/.env"
printf '%s\n' "$CURRENT_COMMIT" > "$BACKUP_DIR/previous-commit.txt"
printf '%s\n' "$TARGET_COMMIT" > "$BACKUP_DIR/target-commit.txt"
printf '%s\n' "$(date --iso-8601=seconds)" > "$BACKUP_DIR/created-at.txt"
if [[ -x "./scripts/backup.sh" ]]; then ./scripts/backup.sh "$BACKUP_DIR/application-backup"; fi
ROLLBACK_READY=1

chmod +x ./scripts/lxc-rollback.sh

log "Updating source"
git reset --hard "${REMOTE}/${BRANCH}"

log "Building updated images"
docker compose --env-file .env "${COMPOSE[@]}" build --pull

log "Preparing storage permissions"
docker compose   --env-file .env   "${COMPOSE[@]}"   run --rm --no-deps storage-init

log "Refreshing CLI"
[[ ! -f scripts/mailhub-cli.sh ]] || install -m 0755 scripts/mailhub-cli.sh /usr/local/bin/mailhub

log "Starting updated stack"
docker compose --env-file .env "${COMPOSE[@]}" up -d --remove-orphans

log "Checking backend"
backend_ok=0
for attempt in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8080/health/live >/dev/null 2>&1; then
    backend_ok=1
    break
  fi
  printf "\rBackend %02d/60" "$attempt"
  sleep 2
done
echo

if [[ "$backend_ok" != 1 ]]; then
  echo "Backend did not become healthy."
  docker compose --env-file .env "${COMPOSE[@]}" ps
  docker compose --env-file .env "${COMPOSE[@]}" logs --tail=150 backend
  echo "Rollback with: mailhub rollback ${CURRENT_COMMIT}"
  exit 1
fi

log "Checking frontend"
frontend_ok=0
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:3000/ >/dev/null 2>&1; then
    frontend_ok=1
    break
  fi
  printf "\rFrontend %02d/30" "$attempt"
  sleep 2
done
echo

if [[ "$frontend_ok" != 1 ]]; then
  echo "Frontend did not become reachable."
  docker compose --env-file .env "${COMPOSE[@]}" ps
  docker compose --env-file .env "${COMPOSE[@]}" logs --tail=150 frontend
  echo "Rollback with: mailhub rollback ${CURRENT_COMMIT}"
  exit 1
fi

log "Checking storage permissions"
chmod +x ./scripts/storage-self-test.sh
./scripts/storage-self-test.sh

docker image prune -f >/dev/null 2>&1 || true

ROLLBACK_READY=0
trap - ERR

NEW_COMMIT="$(git rev-parse HEAD)"
if [[ -x scripts/write-install-info.sh ]]; then scripts/write-install-info.sh >/root/mailhub-install-info.txt.tmp; mv -f /root/mailhub-install-info.txt.tmp /root/mailhub-install-info.txt; chmod 0600 /root/mailhub-install-info.txt; fi

IP="$(hostname -I | awk '{print $1}')"

echo
echo "============================================================"
echo " Mail Attachment Hub updated successfully"
echo "============================================================"
echo "Previous: ${CURRENT_COMMIT}"
echo "Current:  ${NEW_COMMIT}"
echo
echo "Web UI:   http://${IP}:3000"
echo "API:      http://${IP}:8080"
echo
echo "Rollback: mailhub rollback ${CURRENT_COMMIT}"
echo "============================================================"
