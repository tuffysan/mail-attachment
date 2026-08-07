#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
BACKUP_ROOT="${BACKUP_ROOT:-/root/mailhub-update-backups}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

CREDENTIALS_FILE="${CREDENTIALS_FILE:-/root/mailhub-credentials.env}"
if [[ -f "$CREDENTIALS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CREDENTIALS_FILE"
fi
WEB_PORT="${WEB_PORT:-$(sed -n 's/^FRONTEND_PORT=//p' .env 2>/dev/null | tail -1)}"
API_PORT="${API_PORT:-$(sed -n 's/^BACKEND_PORT=//p' .env 2>/dev/null | tail -1)}"
WEB_PORT="${WEB_PORT:-3000}"
API_PORT="${API_PORT:-8080}"
[[ $EUID -eq 0 ]] || { echo "Kör som root inne i LXC:n."; exit 1; }
cd "$APP_DIR"
TARGET="${1:-latest}"
if [[ "$TARGET" == latest ]]; then BACKUP_DIR="$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null | sort -nr | awk 'NR==1 {print $2}')"; elif [[ -d "$TARGET" ]]; then BACKUP_DIR="$TARGET"; elif [[ -d "$BACKUP_ROOT/$TARGET" ]]; then BACKUP_DIR="$BACKUP_ROOT/$TARGET"; else BACKUP_DIR=""; fi
[[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]] || { echo "Ingen rollback-backup hittades: $TARGET" >&2; exit 1; }
[[ -s "$BACKUP_DIR/previous-commit.txt" ]] || { echo "previous-commit.txt saknas." >&2; exit 1; }
PREVIOUS_COMMIT="$(tr -d '\r\n' < "$BACKUP_DIR/previous-commit.txt")"
git cat-file -e "${PREVIOUS_COMMIT}^{commit}" 2>/dev/null || git fetch --all --prune
git cat-file -e "${PREVIOUS_COMMIT}^{commit}" 2>/dev/null || { echo "Commit saknas: $PREVIOUS_COMMIT" >&2; exit 1; }
[[ ! -f "$BACKUP_DIR/.env" ]] || cp "$BACKUP_DIR/.env" .env
chmod 0600 .env
git reset --hard "$PREVIOUS_COMMIT"
docker compose --env-file .env "${COMPOSE[@]}" run --rm --no-deps storage-init
docker compose --env-file .env "${COMPOSE[@]}" build
docker compose --env-file .env "${COMPOSE[@]}" up -d --remove-orphans
for i in $(seq 1 60); do curl -fsS http://127.0.0.1:${API_PORT}/health/live >/dev/null 2>&1 && break; [[ $i == 60 ]] && exit 1; sleep 2; done
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:${WEB_PORT}/ >/dev/null 2>&1 && break; [[ $i == 30 ]] && exit 1; sleep 2; done
[[ ! -x scripts/storage-self-test.sh ]] || scripts/storage-self-test.sh
if [[ -x scripts/write-install-info.sh ]]; then scripts/write-install-info.sh >/root/mailhub-install-info.txt.tmp; mv -f /root/mailhub-install-info.txt.tmp /root/mailhub-install-info.txt; chmod 0600 /root/mailhub-install-info.txt; fi
echo "Rollback slutförd. Commit: $(git rev-parse HEAD)"
