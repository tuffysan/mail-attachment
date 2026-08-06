#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${REPO:-tuffysan/mail-attachment}"
BRANCH="${BRANCH:-main}"

CTID="${CTID:-}"
HOSTNAME="${HOSTNAME:-mail-attachment-hub}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
BRIDGE="${BRIDGE:-vmbr0}"
DISK_GB="${DISK_GB:-24}"
MEMORY_MB="${MEMORY_MB:-4096}"
SWAP_MB="${SWAP_MB:-512}"
CORES="${CORES:-2}"
IPV4="${IPV4:-dhcp}"
GATEWAY="${GATEWAY:-}"
DNS_SERVER="${DNS_SERVER:-}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
TZ="${TZ:-Europe/Stockholm}"
WEB_PORT="${WEB_PORT:-3000}"
API_PORT="${API_PORT:-8080}"

CURRENT_STEP="start"
CREATED_CT=0
DOWNLOADED_TEMPLATE=""
TEMP_INNER_SCRIPT=""

cleanup() {
  [[ -n "$TEMP_INNER_SCRIPT" && -f "$TEMP_INNER_SCRIPT" ]] && rm -f "$TEMP_INNER_SCRIPT"
}
trap cleanup EXIT

on_error() {
  local code=$?
  echo >&2
  echo "============================================================" >&2
  echo " Installationen misslyckades" >&2
  echo "============================================================" >&2
  echo "Steg: ${CURRENT_STEP}" >&2
  echo "Rad: ${BASH_LINENO[0]}" >&2
  echo "Exitkod: ${code}" >&2
  if [[ "$CREATED_CT" == "1" ]]; then
    echo >&2
    echo "LXC ${CTID} finns kvar för felsökning." >&2
    echo "Öppna den med: pct enter ${CTID}" >&2
    echo "Visa loggen med:" >&2
    echo "  pct exec ${CTID} -- cat /root/mailhub-install.log" >&2
    echo >&2
    echo "Ta bort containern med:" >&2
    echo "  pct stop ${CTID} 2>/dev/null || true" >&2
    echo "  pct destroy ${CTID} --purge" >&2
  fi
  exit "$code"
}
trap on_error ERR

log() {
  printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"
}

require_root_and_proxmox() {
  [[ $EUID -eq 0 ]] || { echo "Kör som root på Proxmox."; exit 1; }
  for cmd in pct pvesh pveam pvesm; do
    command -v "$cmd" >/dev/null 2>&1 || {
      echo "${cmd} saknas. Kör scriptet direkt på Proxmox-värden."
      exit 1
    }
  done
}

choose_ctid() {
  [[ -n "$CTID" ]] || CTID="$(pvesh get /cluster/nextid)"
  if pct status "$CTID" >/dev/null 2>&1; then
    echo "LXC-ID ${CTID} används redan."
    exit 1
  fi
}

validate_storage() {
  pvesm status --storage "$STORAGE" >/dev/null 2>&1 || {
    echo "Storage '${STORAGE}' finns inte."
    pvesm status
    exit 1
  }
  pvesm status --storage "$TEMPLATE_STORAGE" >/dev/null 2>&1 || {
    echo "Template storage '${TEMPLATE_STORAGE}' finns inte."
    pvesm status
    exit 1
  }
}

download_template() {
  CURRENT_STEP="hämtar Debian 12-template"
  log "$CURRENT_STEP"
  pveam update >/dev/null

  DOWNLOADED_TEMPLATE="$(
    pveam available --section system |
      awk '/debian-12-standard/ {print $2}' |
      sort -V |
      tail -n 1
  )"

  [[ -n "$DOWNLOADED_TEMPLATE" ]] || {
    echo "Ingen Debian 12-template hittades."
    exit 1
  }

  if ! pveam list "$TEMPLATE_STORAGE" | awk '{print $1}' |
      grep -q "/${DOWNLOADED_TEMPLATE}$"; then
    pveam download "$TEMPLATE_STORAGE" "$DOWNLOADED_TEMPLATE"
  fi

  log "Vald template: ${DOWNLOADED_TEMPLATE}"
}

create_container() {
  CURRENT_STEP="skapar LXC ${CTID}"
  log "$CURRENT_STEP"

  local net="name=eth0,bridge=${BRIDGE},ip=${IPV4}"
  [[ -z "$GATEWAY" ]] || net+=",gw=${GATEWAY}"

  pct create "$CTID" "${TEMPLATE_STORAGE}:vztmpl/${DOWNLOADED_TEMPLATE}" \
    --hostname "$HOSTNAME" \
    --ostype debian \
    --arch amd64 \
    --unprivileged 1 \
    --features "nesting=1,keyctl=1" \
    --cores "$CORES" \
    --memory "$MEMORY_MB" \
    --swap "$SWAP_MB" \
    --rootfs "${STORAGE}:${DISK_GB}" \
    --net0 "$net" \
    --onboot 1

  CREATED_CT=1
  [[ -z "$DNS_SERVER" ]] || pct set "$CTID" --nameserver "$DNS_SERVER"

  local cfg="/etc/pve/lxc/${CTID}.conf"
  grep -q '^lxc.apparmor.profile:' "$cfg" ||
    echo 'lxc.apparmor.profile: unconfined' >> "$cfg"
  grep -q '^lxc.cgroup2.devices.allow: a' "$cfg" ||
    echo 'lxc.cgroup2.devices.allow: a' >> "$cfg"
  grep -q '^lxc.cap.drop:' "$cfg" ||
    echo 'lxc.cap.drop:' >> "$cfg"

  pct start "$CTID"
}

wait_for_container() {
  CURRENT_STEP="väntar på LXC och nätverk"
  log "$CURRENT_STEP"

  for attempt in $(seq 1 60); do
    printf "\rKontroll %02d/60" "$attempt"
    if pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1; then
      echo " - OK"
      return
    fi
    sleep 2
  done
  echo
  echo "LXC:n fick inte fungerande nätverk eller DNS."
  exit 1
}

create_inner_script() {
  TEMP_INNER_SCRIPT="$(mktemp /tmp/mailhub-inside.XXXXXX.sh)"

  cat > "$TEMP_INNER_SCRIPT" <<'INNER_SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail

exec > >(tee -a /root/mailhub-install.log) 2>&1

REPO="${REPO:?}"
BRANCH="${BRANCH:?}"
ADMIN_EMAIL="${ADMIN_EMAIL:?}"
TZ="${TZ:?}"
WEB_PORT="${WEB_PORT:?}"
API_PORT="${API_PORT:?}"
INSTALL_DIR="/opt/mail-attachment-hub"

step() {
  printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"
}

replace_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

step "Installerar systempaket"
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

apt-get update
apt-get install -y \
  ca-certificates curl git jq locales openssl iproute2

locale-gen C.UTF-8 >/dev/null 2>&1 || true

step "Installerar Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

if ! docker compose version >/dev/null 2>&1; then
  apt-get update
  apt-get install -y docker-compose-plugin
fi

step "Hämtar Mail Attachment Hub"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "$INSTALL_DIR" fetch origin "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
else
  rm -rf "$INSTALL_DIR"
  git clone --branch "$BRANCH" "https://github.com/${REPO}.git" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

POSTGRES_PASSWORD="$(openssl rand -base64 36 | tr -d '\n' | tr '/+' '_-')"
APP_SECRET_KEY="$(openssl rand -hex 48)"
ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -d '\n' | tr '/+' '_-')"

# Preserve existing generated secrets on rerun.
existing_postgres="$(sed -n 's/^POSTGRES_PASSWORD=//p' .env | head -1)"
existing_secret="$(sed -n 's/^APP_SECRET_KEY=//p' .env | head -1)"
existing_admin_password="$(sed -n 's/^ADMIN_PASSWORD=//p' .env | head -1)"

[[ -z "$existing_postgres" || "$existing_postgres" == change-* ]] ||
  POSTGRES_PASSWORD="$existing_postgres"
[[ -z "$existing_secret" || "$existing_secret" == replace-* ]] ||
  APP_SECRET_KEY="$existing_secret"
[[ -z "$existing_admin_password" || "$existing_admin_password" == replace-* ]] ||
  ADMIN_PASSWORD="$existing_admin_password"

replace_env POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
replace_env APP_SECRET_KEY "$APP_SECRET_KEY"
replace_env ADMIN_EMAIL "$ADMIN_EMAIL"
replace_env ADMIN_PASSWORD "$ADMIN_PASSWORD"
replace_env TZ "$TZ"
replace_env FRONTEND_BIND_ADDRESS "0.0.0.0"
replace_env BACKEND_BIND_ADDRESS "0.0.0.0"
replace_env FRONTEND_PORT "$WEB_PORT"
replace_env BACKEND_PORT "$API_PORT"

cat > /root/mailhub-credentials.env <<EOF
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
WEB_PORT=${WEB_PORT}
API_PORT=${API_PORT}
EOF
chmod 600 /root/mailhub-credentials.env

step "Bygger Docker-images"
docker compose --env-file .env -f compose.yml build --pull

step "Startar tjänster"
docker compose --env-file .env -f compose.yml up -d

step "Kontrollerar tjänster"
api_ok=0
frontend_ok=0

for attempt in $(seq 1 90); do
  curl -fsS "http://127.0.0.1:${API_PORT}/health/live" >/dev/null 2>&1 &&
    api_ok=1 || true
  curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 &&
    frontend_ok=1 || true

  printf '\rKontroll %02d/90 - API: %s - Frontend: %s' \
    "$attempt" \
    "$([[ "$api_ok" == 1 ]] && echo OK || echo väntar)" \
    "$([[ "$frontend_ok" == 1 ]] && echo OK || echo väntar)"

  if [[ "$api_ok" == 1 && "$frontend_ok" == 1 ]]; then
    echo
    break
  fi
  sleep 2
done
echo

docker compose --env-file .env -f compose.yml ps

if [[ "$api_ok" != 1 || "$frontend_ok" != 1 ]]; then
  echo "Tjänsterna startade men svarar inte korrekt."
  docker compose --env-file .env -f compose.yml logs --tail=120 backend frontend
  exit 1
fi

if ! ss -lnt | grep -qE "0\.0\.0\.0:${WEB_PORT}|:::${WEB_PORT}"; then
  echo "Frontend-port ${WEB_PORT} exponeras inte på nätverket."
  ss -lnt
  exit 1
fi

if ! ss -lnt | grep -qE "0\.0\.0\.0:${API_PORT}|:::${API_PORT}"; then
  echo "Backend-port ${API_PORT} exponeras inte på nätverket."
  ss -lnt
  exit 1
fi

step "Installerar administrationskommando"
cat > /usr/local/bin/mailhub <<'MAILHUB_CLI'
#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/mail-attachment-hub
source /root/mailhub-credentials.env
IP="$(hostname -I | awk '{print $1}')"

case "${1:-help}" in
  status)
    docker compose --env-file .env -f compose.yml ps
    curl -sS "http://127.0.0.1:${API_PORT}/health/ready" | jq . || true
    ;;
  logs)
    shift || true
    docker compose --env-file .env -f compose.yml logs -f --tail=200 "$@"
    ;;
  restart)
    docker compose --env-file .env -f compose.yml restart
    ;;
  start)
    docker compose --env-file .env -f compose.yml up -d
    ;;
  stop)
    docker compose --env-file .env -f compose.yml down
    ;;
  credentials)
    cat <<INFO
============================================================
 Mail Attachment Hub
============================================================
Web UI:  http://${IP}:${WEB_PORT}
API:     http://${IP}:${API_PORT}
Login:   ${ADMIN_EMAIL}
Password: ${ADMIN_PASSWORD}
============================================================
INFO
    ;;
  *)
    echo "mailhub status|logs|restart|start|stop|credentials"
    ;;
esac
MAILHUB_CLI
chmod +x /usr/local/bin/mailhub

cat > /etc/systemd/system/mailhub-compose.service <<EOF
[Unit]
Description=Mail Attachment Hub
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker compose --env-file .env -f compose.yml up -d
ExecStop=/usr/bin/docker compose --env-file .env -f compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mailhub-compose.service

touch /root/mailhub-install-complete
step "Installationen i LXC är klar"
INNER_SCRIPT

  chmod +x "$TEMP_INNER_SCRIPT"
}

run_inner_script() {
  CURRENT_STEP="installerar applikationen i LXC"
  log "$CURRENT_STEP"

  pct push "$CTID" "$TEMP_INNER_SCRIPT" /root/mailhub-install-inside.sh \
    --perms 0755

  pct exec "$CTID" -- env \
    REPO="$REPO" \
    BRANCH="$BRANCH" \
    ADMIN_EMAIL="$ADMIN_EMAIL" \
    TZ="$TZ" \
    WEB_PORT="$WEB_PORT" \
    API_PORT="$API_PORT" \
    /root/mailhub-install-inside.sh
}

show_result() {
  CURRENT_STEP="visar installationsinformation"
  log "$CURRENT_STEP"

  local ip email password web_port api_port
  ip="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
  email="$(pct exec "$CTID" -- sed -n 's/^ADMIN_EMAIL=//p' /root/mailhub-credentials.env)"
  password="$(pct exec "$CTID" -- sed -n 's/^ADMIN_PASSWORD=//p' /root/mailhub-credentials.env)"
  web_port="$(pct exec "$CTID" -- sed -n 's/^WEB_PORT=//p' /root/mailhub-credentials.env)"
  api_port="$(pct exec "$CTID" -- sed -n 's/^API_PORT=//p' /root/mailhub-credentials.env)"

  echo
  echo "============================================================"
  echo " Mail Attachment Hub installerades korrekt"
  echo "============================================================"
  echo "LXC-ID:       ${CTID}"
  echo "IP-adress:    ${ip}"
  echo
  echo "Web UI:       http://${ip}:${web_port}"
  echo "API:          http://${ip}:${api_port}"
  echo
  echo "Login:        ${email}"
  echo "Password:     ${password}"
  echo
  echo "Senare visning:"
  echo "  pct enter ${CTID}"
  echo "  mailhub credentials"
  echo "============================================================"
}

main() {
  require_root_and_proxmox
  choose_ctid
  validate_storage
  download_template
  create_container
  wait_for_container
  create_inner_script
  run_inner_script
  show_result
}

main "$@"
