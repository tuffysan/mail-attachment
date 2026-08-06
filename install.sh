#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Mail Attachment Hub - Proxmox LXC installer
# ============================================================
#
# One-liner:
# bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
#
# Optional:
# CTID=134 MEMORY_MB=6144 CORES=4 DISK_GB=40 \
# ADMIN_EMAIL=admin@example.com \
# bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
#

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

UNPRIVILEGED="${UNPRIVILEGED:-1}"
START_ON_BOOT="${START_ON_BOOT:-1}"

IPV4="${IPV4:-dhcp}"
GATEWAY="${GATEWAY:-}"
DNS_SERVER="${DNS_SERVER:-}"

INSTALL_DIR="${INSTALL_DIR:-/opt/mail-attachment-hub}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
TZ="${TZ:-Europe/Stockholm}"

WEB_PORT="${WEB_PORT:-3000}"
API_PORT="${API_PORT:-8080}"

CURRENT_STEP="start"
CREATED_CT=0
DOWNLOADED_TEMPLATE=""

on_error() {
  local exit_code=$?

  echo >&2
  echo "============================================================" >&2
  echo " Installationen misslyckades" >&2
  echo "============================================================" >&2
  echo "Steg: ${CURRENT_STEP}" >&2
  echo "Rad: ${BASH_LINENO[0]}" >&2
  echo "Exitkod: ${exit_code}" >&2

  if [[ "$CREATED_CT" == "1" ]]; then
    echo >&2
    echo "LXC ${CTID} skapades men installationen slutfördes inte." >&2
    echo "Du kan fortsätta felsöka i containern med:" >&2
    echo "  pct enter ${CTID}" >&2
    echo >&2
    echo "Ta annars bort den med:" >&2
    echo "  pct stop ${CTID} 2>/dev/null || true" >&2
    echo "  pct destroy ${CTID} --purge" >&2
  fi

  exit "$exit_code"
}
trap on_error ERR

log() {
  printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*" >&2
}

require_root() {
  [[ $EUID -eq 0 ]] || {
    echo "Kör scriptet som root på Proxmox-värden." >&2
    exit 1
  }
}

require_proxmox() {
  local command_name

  for command_name in pct pvesh pveam pvesm; do
    command -v "$command_name" >/dev/null 2>&1 || {
      echo "${command_name} hittades inte." >&2
      echo "Scriptet måste köras direkt på en Proxmox VE-värd." >&2
      exit 1
    }
  done
}

choose_ctid() {
  if [[ -z "$CTID" ]]; then
    CTID="$(pvesh get /cluster/nextid)"
  fi

  if pct status "$CTID" >/dev/null 2>&1; then
    echo "LXC-ID ${CTID} används redan." >&2
    exit 1
  fi
}

validate_storage() {
  if ! pvesm status --storage "$STORAGE" >/dev/null 2>&1; then
    echo "Storage '${STORAGE}' finns inte." >&2
    echo "Tillgänglig storage:" >&2
    pvesm status >&2
    exit 1
  fi

  if ! pvesm status --storage "$TEMPLATE_STORAGE" >/dev/null 2>&1; then
    echo "Template storage '${TEMPLATE_STORAGE}' finns inte." >&2
    echo "Tillgänglig storage:" >&2
    pvesm status >&2
    exit 1
  fi
}

download_template() {
  CURRENT_STEP="hämtar Debian-template"
  log "Hämtar aktuell Debian 12-template"

  pveam update >/dev/null

  DOWNLOADED_TEMPLATE="$(
    pveam available --section system |
      awk '/debian-12-standard/ {print $2}' |
      sort -V |
      tail -n 1
  )"

  if [[ -z "$DOWNLOADED_TEMPLATE" ]]; then
    echo "Ingen Debian 12-template hittades." >&2
    exit 1
  fi

  if ! pveam list "$TEMPLATE_STORAGE" |
      awk '{print $1}' |
      grep -q "/${DOWNLOADED_TEMPLATE}$"; then
    log "Laddar ner ${DOWNLOADED_TEMPLATE}"
    pveam download "$TEMPLATE_STORAGE" "$DOWNLOADED_TEMPLATE"
  else
    log "Template ${DOWNLOADED_TEMPLATE} finns redan lokalt"
  fi
}

create_container() {
  CURRENT_STEP="skapar LXC"
  log "Skapar LXC ${CTID}"

  local network_config
  network_config="name=eth0,bridge=${BRIDGE},ip=${IPV4}"

  if [[ -n "$GATEWAY" ]]; then
    network_config+=",gw=${GATEWAY}"
  fi

  pct create "$CTID" "${TEMPLATE_STORAGE}:vztmpl/${DOWNLOADED_TEMPLATE}" \
    --hostname "$HOSTNAME" \
    --ostype debian \
    --arch amd64 \
    --unprivileged "$UNPRIVILEGED" \
    --features "nesting=1,keyctl=1" \
    --cores "$CORES" \
    --memory "$MEMORY_MB" \
    --swap "$SWAP_MB" \
    --rootfs "${STORAGE}:${DISK_GB}" \
    --net0 "$network_config" \
    --onboot "$START_ON_BOOT"

  CREATED_CT=1

  if [[ -n "$DNS_SERVER" ]]; then
    pct set "$CTID" --nameserver "$DNS_SERVER"
  fi

  local config_file="/etc/pve/lxc/${CTID}.conf"

  grep -q '^lxc.apparmor.profile:' "$config_file" ||
    echo 'lxc.apparmor.profile: unconfined' >> "$config_file"

  grep -q '^lxc.cgroup2.devices.allow: a' "$config_file" ||
    echo 'lxc.cgroup2.devices.allow: a' >> "$config_file"

  grep -q '^lxc.cap.drop:' "$config_file" ||
    echo 'lxc.cap.drop:' >> "$config_file"

  pct start "$CTID"
}

wait_for_container() {
  CURRENT_STEP="väntar på LXC"
  log "Väntar på att LXC ${CTID} ska starta"

  for _ in {1..60}; do
    if pct exec "$CTID" -- true >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done

  echo "LXC ${CTID} startade inte korrekt." >&2
  exit 1
}

wait_for_network() {
  CURRENT_STEP="väntar på nätverk"
  log "Väntar på nätverk och DNS"

  for _ in {1..60}; do
    if pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done

  echo "Containern fick inte fungerande nätverk eller DNS." >&2
  echo "Kontrollera bridge, gateway och DNS." >&2
  exit 1
}

install_application() {
  CURRENT_STEP="installerar applikationen"
  log "Installerar Mail Attachment Hub i LXC ${CTID}"

  pct exec "$CTID" -- env \
    REPO="$REPO" \
    BRANCH="$BRANCH" \
    INSTALL_DIR="$INSTALL_DIR" \
    ADMIN_EMAIL="$ADMIN_EMAIL" \
    TZ="$TZ" \
    WEB_PORT="$WEB_PORT" \
    API_PORT="$API_PORT" \
    bash -lc '
      set -Eeuo pipefail

      export DEBIAN_FRONTEND=noninteractive
      export LANG=C.UTF-8
      export LC_ALL=C.UTF-8

      apt-get update

      apt-get install -y \
        ca-certificates \
        curl \
        git \
        jq \
        locales \
        make \
        openssl \
        iproute2

      locale-gen C.UTF-8 >/dev/null 2>&1 || true

      if ! command -v docker >/dev/null 2>&1; then
        curl -fsSL https://get.docker.com | sh
      fi

      systemctl enable --now docker

      if ! docker compose version >/dev/null 2>&1; then
        apt-get update
        apt-get install -y docker-compose-plugin
      fi

      if [[ -d "${INSTALL_DIR}/.git" ]]; then
        git -C "$INSTALL_DIR" fetch origin "$BRANCH"
        git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
      else
        rm -rf "$INSTALL_DIR"

        git clone \
          --branch "$BRANCH" \
          "https://github.com/${REPO}.git" \
          "$INSTALL_DIR"
      fi

      cd "$INSTALL_DIR"

      if [[ ! -f .env ]]; then
        cp .env.example .env

        POSTGRES_PASSWORD="$(
          openssl rand -base64 36 |
            tr -d "\n" |
            tr "/+" "_-"
        )"

        APP_SECRET_KEY="$(openssl rand -hex 48)"

        ADMIN_PASSWORD="$(
          openssl rand -base64 24 |
            tr -d "\n" |
            tr "/+" "_-"
        )"

        replace_env() {
          local key="$1"
          local value="$2"

          if grep -q "^${key}=" .env; then
            sed -i "s|^${key}=.*|${key}=${value}|" .env
          else
            printf "%s=%s\n" "$key" "$value" >> .env
          fi
        }

        replace_env POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
        replace_env APP_SECRET_KEY "$APP_SECRET_KEY"
        replace_env ADMIN_EMAIL "$ADMIN_EMAIL"
        replace_env ADMIN_PASSWORD "$ADMIN_PASSWORD"
        replace_env TZ "$TZ"
        replace_env FRONTEND_BIND_ADDRESS "0.0.0.0"
        replace_env BACKEND_BIND_ADDRESS "0.0.0.0"
        replace_env FRONTEND_PORT "$WEB_PORT"
        replace_env BACKEND_PORT "$API_PORT"

        cat > /root/mailhub-credentials.txt <<EOF
MAIL_ATTACHMENT_HUB_CREDENTIALS_VERSION=1
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
WEB_PORT=${WEB_PORT}
API_PORT=${API_PORT}
EOF

        chmod 600 /root/mailhub-credentials.txt
      fi

      replace_env() {
        local key="$1"
        local value="$2"

        if grep -q "^${key}=" .env; then
          sed -i "s|^${key}=.*|${key}=${value}|" .env
        else
          printf "%s=%s\n" "$key" "$value" >> .env
        fi
      }

      replace_env FRONTEND_BIND_ADDRESS "0.0.0.0"
      replace_env BACKEND_BIND_ADDRESS "0.0.0.0"
      replace_env FRONTEND_PORT "$WEB_PORT"
      replace_env BACKEND_PORT "$API_PORT"

      docker compose \
        --env-file .env \
        -f compose.yml \
        pull --ignore-buildable || true

      docker compose \
        --env-file .env \
        -f compose.yml \
        build --pull

      docker compose \
        --env-file .env \
        -f compose.yml \
        up -d

      echo
      echo "Väntar på backend och frontend..."

      API_LIVE=0
      FRONTEND_LIVE=0

      for attempt in $(seq 1 60); do
        if curl -fsS \
          "http://127.0.0.1:${API_PORT}/health/live" \
          >/dev/null 2>&1; then
          API_LIVE=1
        fi

        if curl -fsS \
          "http://127.0.0.1:${WEB_PORT}/" \
          >/dev/null 2>&1; then
          FRONTEND_LIVE=1
        fi

        printf "\rKontroll %02d/60 - API: %s - Frontend: %s" \
          "$attempt" \
          "$([[ "$API_LIVE" == "1" ]] && echo OK || echo väntar)" \
          "$([[ "$FRONTEND_LIVE" == "1" ]] && echo OK || echo väntar)"

        if [[ "$API_LIVE" == "1" && "$FRONTEND_LIVE" == "1" ]]; then
          echo
          break
        fi

        sleep 2
      done

      echo

      if [[ "$API_LIVE" != "1" || "$FRONTEND_LIVE" != "1" ]]; then
        echo "En eller flera webbtjänster svarar inte ännu." >&2
        docker compose --env-file .env -f compose.yml ps >&2
        docker compose --env-file .env -f compose.yml logs --tail=80 backend frontend >&2
        exit 1
      fi

      echo "Backend live: OK"
      echo "Frontend: OK"

      if curl -fsS \
        "http://127.0.0.1:${API_PORT}/health/ready" \
        >/tmp/mailhub-readiness.json 2>/dev/null; then
        echo "Backend readiness: OK"
      else
        echo "Backend readiness är tillfälligt degraderad; installationen fortsätter."
        curl -sS \
          "http://127.0.0.1:${API_PORT}/health/ready" \
          >/tmp/mailhub-readiness.json 2>/dev/null || true
      fi

      if ! ss -lnt | grep -qE "0\.0\.0\.0:${WEB_PORT}|:::${WEB_PORT}"; then
        echo "Frontend-port ${WEB_PORT} är inte exponerad på LXC-nätverket." >&2
        ss -lnt >&2
        exit 1
      fi

      if ! ss -lnt | grep -qE "0\.0\.0\.0:${API_PORT}|:::${API_PORT}"; then
        echo "Backend-port ${API_PORT} är inte exponerad på LXC-nätverket." >&2
        ss -lnt >&2
        exit 1
      fi

      cat > /usr/local/bin/mailhub <<'"'"'EOF'"'"'
#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/mail-attachment-hub"
CREDENTIAL_FILE="/root/mailhub-credentials.txt"

cd "$APP_DIR"

cmd="${1:-help}"
shift || true

case "$cmd" in
  status)
    docker compose --env-file .env -f compose.yml ps
    echo

    source "$CREDENTIAL_FILE"

    curl -fsS \
      "http://127.0.0.1:${API_PORT:-8080}/health/ready" |
      jq .
    ;;

  logs)
    docker compose \
      --env-file .env \
      -f compose.yml \
      logs -f --tail=200 "$@"
    ;;

  restart)
    docker compose --env-file .env -f compose.yml restart
    ;;

  stop)
    docker compose --env-file .env -f compose.yml down
    ;;

  start)
    docker compose --env-file .env -f compose.yml up -d
    ;;

  update)
    ./scripts/backup.sh || true
    git fetch origin main
    git pull --ff-only origin main

    docker compose \
      --env-file .env \
      -f compose.yml \
      build --pull

    docker compose \
      --env-file .env \
      -f compose.yml \
      up -d
    ;;

  backup)
    ./scripts/backup.sh "$@"
    ;;

  restore)
    ./scripts/restore.sh "$@"
    ;;

  doctor)
    ./scripts/doctor.sh
    ;;

  credentials)
    source "$CREDENTIAL_FILE"

    IP_ADDRESS="$(hostname -I | awk "{print \$1}")"

    cat <<INFO
============================================================
 Mail Attachment Hub
============================================================

Web UI:
  http://${IP_ADDRESS}:${WEB_PORT}

API:
  http://${IP_ADDRESS}:${API_PORT}

Login:
  Email:    ${ADMIN_EMAIL}
  Password: ${ADMIN_PASSWORD}

Credentials file:
  ${CREDENTIAL_FILE}

============================================================
INFO
    ;;

  *)
    cat <<HELP
Mail Attachment Hub administration

mailhub status
mailhub logs [service]
mailhub restart
mailhub stop
mailhub start
mailhub update
mailhub backup
mailhub restore <backup-directory>
mailhub doctor
mailhub credentials
HELP
    ;;
esac
EOF

      chmod +x /usr/local/bin/mailhub

      cat > /etc/systemd/system/mailhub-compose.service <<EOF
[Unit]
Description=Mail Attachment Hub Docker Compose stack
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
    '
}

get_container_ip() {
  local ip_address=""

  for _ in {1..30}; do
    ip_address="$(
      pct exec "$CTID" -- hostname -I 2>/dev/null |
        awk '{print $1}'
    )"

    if [[ -n "$ip_address" ]]; then
      printf '%s\n' "$ip_address"
      return
    fi

    sleep 2
  done

  return 1
}

read_credential_value() {
  local key="$1"

  pct exec "$CTID" -- awk -F= \
    -v requested_key="$key" \
    '$1 == requested_key {
      sub(/^[^=]*=/, "")
      print
      exit
    }' \
    /root/mailhub-credentials.txt
}

show_result() {
  CURRENT_STEP="visar installationsinformation"

  local ip_address
  local admin_email
  local admin_password
  local web_port
  local api_port

  ip_address="$(get_container_ip)"
  admin_email="$(read_credential_value ADMIN_EMAIL)"
  admin_password="$(read_credential_value ADMIN_PASSWORD)"
  web_port="$(read_credential_value WEB_PORT)"
  api_port="$(read_credential_value API_PORT)"

  log "Installation klar"

  echo
  echo "============================================================"
  echo " Mail Attachment Hub installerades korrekt"
  echo "============================================================"
  echo
  echo "Proxmox"
  echo "  LXC-ID:       ${CTID}"
  echo "  Hostname:     ${HOSTNAME}"
  echo "  IP-adress:    ${ip_address}"
  echo
  echo "Webbgränssnitt"
  echo "  http://${ip_address}:${web_port}"
  echo
  echo "API"
  echo "  http://${ip_address}:${api_port}"
  echo
  echo "Inloggning"
  echo "  E-post:       ${admin_email}"
  echo "  Lösenord:     ${admin_password}"
  echo
  echo "Inloggningsuppgifterna finns även i:"
  echo "  /root/mailhub-credentials.txt"
  echo
  echo "Öppna containern:"
  echo "  pct enter ${CTID}"
  echo
  echo "Användbara kommandon:"
  echo "  mailhub status"
  echo "  mailhub logs"
  echo "  mailhub credentials"
  echo "  mailhub doctor"
  echo "  mailhub update"
  echo "  mailhub backup"
  echo
  echo "============================================================"
}

main() {
  require_root
  require_proxmox
  choose_ctid
  validate_storage
  download_template

  log "Vald template: ${DOWNLOADED_TEMPLATE}"

  create_container
  wait_for_container
  wait_for_network
  install_application
  show_result
}

main "$@"
