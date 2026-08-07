#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/mail-attachment-hub}"
CREDENTIALS_FILE="${CREDENTIALS_FILE:-/root/mailhub-credentials.env}"
COMPOSE=(-f compose.yml -f compose.override.lxc.yml)

[[ $EUID -eq 0 ]] || {
  echo "Kör som root inne i Mail Attachment Hub-LXC:n."
  exit 1
}

cd "$APP_DIR"

load_credentials() {
  if [[ -f "$CREDENTIALS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CREDENTIALS_FILE"
  fi

  WEB_PORT="${WEB_PORT:-$(sed -n 's/^FRONTEND_PORT=//p' .env 2>/dev/null | tail -1)}"
  API_PORT="${API_PORT:-$(sed -n 's/^BACKEND_PORT=//p' .env 2>/dev/null | tail -1)}"
  ADMIN_EMAIL="${ADMIN_EMAIL:-$(sed -n 's/^ADMIN_EMAIL=//p' .env 2>/dev/null | tail -1)}"

  WEB_PORT="${WEB_PORT:-3000}"
  API_PORT="${API_PORT:-8080}"
  ADMIN_EMAIL="${ADMIN_EMAIL:-unknown}"
}

primary_ip() {
  hostname -I 2>/dev/null | awk '{print $1}'
}

print_credentials() {
  load_credentials
  local ip
  ip="$(primary_ip)"
  ip="${ip:-CONTAINER-IP}"

  echo "============================================================"
  echo " Mail Attachment Hub"
  echo "============================================================"
  echo "Web UI:   http://${ip}:${WEB_PORT}"
  echo "API:      http://${ip}:${API_PORT}"
  echo "Login:    ${ADMIN_EMAIL}"

  if [[ -f "$CREDENTIALS_FILE" ]]; then
    local password
    password="$(sed -n 's/^ADMIN_PASSWORD=//p' "$CREDENTIALS_FILE" | tail -1)"
    echo "Password: ${password:-unknown}"
  else
    echo "Password: unavailable (${CREDENTIALS_FILE} saknas)"
  fi

  echo
  echo "LXC IP:   ${ip}"
  echo "Hostname: $(hostname)"
  echo "============================================================"
}

compose_cmd() {
  docker compose --env-file .env "${COMPOSE[@]}" "$@"
}

doctor() {
  load_credentials
  local failures=0
  local ip
  ip="$(primary_ip)"
  ip="${ip:-127.0.0.1}"

  echo "============================================================"
  echo " Mail Attachment Hub - Doctor"
  echo "============================================================"

  echo
  echo "[1/7] Git repository"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "OK commit=$(git rev-parse --short HEAD)"
  else
    echo "FAIL: ${APP_DIR} är inte ett Git repository."
    failures=$((failures + 1))
  fi

  echo
  echo "[2/7] Docker"
  if command -v docker >/dev/null 2>&1 &&
     docker compose version >/dev/null 2>&1; then
    echo "OK $(docker compose version --short 2>/dev/null || true)"
  else
    echo "FAIL: Docker Compose saknas."
    failures=$((failures + 1))
  fi

  echo
  echo "[3/7] Containers"
  if compose_cmd ps; then
    :
  else
    echo "FAIL: kunde inte läsa Docker-status."
    failures=$((failures + 1))
  fi

  echo
  echo "[4/7] Backend"
  if curl -fsS "http://127.0.0.1:${API_PORT}/health/live" >/dev/null 2>&1; then
    echo "OK http://${ip}:${API_PORT}"
  else
    echo "FAIL: backend svarar inte på port ${API_PORT}."
    failures=$((failures + 1))
  fi

  echo
  echo "[5/7] Frontend"
  if curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1; then
    echo "OK http://${ip}:${WEB_PORT}"
  else
    echo "FAIL: frontend svarar inte på port ${WEB_PORT}."
    failures=$((failures + 1))
  fi

  echo
  echo "[6/7] Storage"
  if [[ -x scripts/storage-self-test.sh ]] &&
     scripts/storage-self-test.sh; then
    :
  else
    echo "FAIL: storage self-test misslyckades."
    failures=$((failures + 1))
  fi

  echo
  echo "[7/7] Update agent"
  if systemctl is-enabled mailhub-update-agent.path >/dev/null 2>&1 &&
     systemctl is-active mailhub-update-agent.path >/dev/null 2>&1 &&
     [[ -s /var/lib/mailhub-control/status.json ]] &&
     jq -e . /var/lib/mailhub-control/status.json >/dev/null 2>&1; then
    echo "OK"
    echo "state=$(jq -r '.state // "unknown"' /var/lib/mailhub-control/status.json)"
  else
    echo "FAIL: update-agent eller status.json är inte frisk."
    failures=$((failures + 1))
  fi

  echo
  echo "============================================================"
  if [[ "$failures" -eq 0 ]]; then
    echo " Doctor: ALL CHECKS PASSED"
  else
    echo " Doctor: ${failures} CHECK(S) FAILED"
  fi
  echo "============================================================"

  [[ "$failures" -eq 0 ]]
}

usage() {
  cat <<'HELP'
Mail Attachment Hub CLI

Kommandon:
  mailhub credentials
      Visa IP, portar och administratörsinloggning.

  mailhub status
      Visa Docker Compose-status.

  mailhub doctor
      Kontrollera Docker, backend, frontend, storage och update-agent.

  mailhub logs [service]
      Följ loggar. Exempel: mailhub logs backend

  mailhub restart [service]
      Starta om hela stacken eller en specifik service.

  mailhub update
      Kör LXC-uppdateraren manuellt.

  mailhub repair storage
      Reparera /data/attachments och /data/routed.

  mailhub repair update-agent
      Reparera GitHub update-agent.

  mailhub update-status
      Visa aktuell update-agent JSON.

  mailhub help
HELP
}

case "${1:-help}" in
  credentials|info)
    print_credentials
    ;;

  status)
    compose_cmd ps
    ;;

  doctor)
    doctor
    ;;

  logs)
    shift || true
    compose_cmd logs -f --tail=200 "$@"
    ;;

  restart)
    shift || true
    if [[ "$#" -gt 0 ]]; then
      compose_cmd restart "$@"
    else
      compose_cmd restart
    fi
    ;;

  update)
    chmod +x scripts/lxc-update.sh
    exec scripts/lxc-update.sh
    ;;

  update-status)
    if [[ -s /var/lib/mailhub-control/status.json ]]; then
      jq . /var/lib/mailhub-control/status.json
    else
      echo "/var/lib/mailhub-control/status.json saknas eller är tom." >&2
      exit 1
    fi
    ;;

  repair)
    case "${2:-}" in
      storage)
        chmod +x scripts/repair-storage-permissions.sh
        exec scripts/repair-storage-permissions.sh
        ;;
      update-agent)
        chmod +x scripts/repair-update-agent.sh
        exec scripts/repair-update-agent.sh
        ;;
      *)
        echo "Använd: mailhub repair storage | update-agent" >&2
        exit 2
        ;;
    esac
    ;;

  help|-h|--help)
    usage
    ;;

  *)
    echo "Okänt kommando: $1" >&2
    echo
    usage
    exit 2
    ;;
esac
