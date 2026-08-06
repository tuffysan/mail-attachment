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
    UNPRIVILEGED="${UNPRIVILEGED:-1}"
    IPV4="${IPV4:-dhcp}"
    GATEWAY="${GATEWAY:-}"
    DNS_SERVER="${DNS_SERVER:-}"
    START_ON_BOOT="${START_ON_BOOT:-1}"
    INSTALL_DIR="${INSTALL_DIR:-/opt/mail-attachment-hub}"
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
    TZ="${TZ:-Europe/Stockholm}"

    CURRENT_STEP="start"
    CREATED_CT=0

    on_error() {
      local exit_code=$?
      echo
      echo "Fel under steg: ${CURRENT_STEP}"
      echo "Rad ${BASH_LINENO[0]}, exitkod ${exit_code}."
      if [[ "$CREATED_CT" == "1" ]]; then
        echo "LXC ${CTID} skapades men installationen slutfördes inte."
        echo "Ta bort den med:"
        echo "  pct stop ${CTID} 2>/dev/null || true"
        echo "  pct destroy ${CTID} --purge"
      fi
      exit "$exit_code"
    }
    trap on_error ERR

    log() {
      printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"
    }

    require_root() {
      [[ $EUID -eq 0 ]] || {
        echo "Kör detta script som root på Proxmox-värden."
        exit 1
      }
    }

    require_proxmox() {
      command -v pct >/dev/null 2>&1 || {
        echo "pct hittades inte. Scriptet måste köras på en Proxmox VE-värd."
        exit 1
      }
      command -v pvesh >/dev/null 2>&1 || {
        echo "pvesh hittades inte."
        exit 1
      }
    }

    choose_ctid() {
      if [[ -z "$CTID" ]]; then
        CTID="$(pvesh get /cluster/nextid)"
      fi
      if pct status "$CTID" >/dev/null 2>&1; then
        echo "LXC-ID ${CTID} används redan."
        exit 1
      fi
    }

    validate_storage() {
      pvesm status --storage "$STORAGE" >/dev/null 2>&1 || {
        echo "Storage '${STORAGE}' finns inte."
        echo "Tillgänglig storage:"
        pvesm status
        exit 1
      }
      pvesm status --storage "$TEMPLATE_STORAGE" >/dev/null 2>&1 || {
        echo "Template storage '${TEMPLATE_STORAGE}' finns inte."
        exit 1
      }
    }

    download_template() {
      CURRENT_STEP="hämtar Debian-template"
      log "Hämtar aktuell Debian 12-template"
      pveam update >/dev/null
      local template
      template="$(
        pveam available --section system |
        awk '/debian-12-standard/ {print $2}' |
        sort -V |
        tail -1
      )"
      [[ -n "$template" ]] || {
        echo "Ingen Debian 12-template hittades."
        exit 1
      }
      if ! pveam list "$TEMPLATE_STORAGE" | awk '{print $1}' | grep -q "/${template}$"; then
        pveam download "$TEMPLATE_STORAGE" "$template"
      fi
      printf '%s' "$template"
    }

    create_container() {
      local template="$1"
      CURRENT_STEP="skapar LXC"
      log "Skapar LXC ${CTID}"

      local net="name=eth0,bridge=${BRIDGE},ip=${IPV4}"
      if [[ -n "$GATEWAY" ]]; then
        net+=",gw=${GATEWAY}"
      fi

      pct create "$CTID" "${TEMPLATE_STORAGE}:vztmpl/${template}" \
        --hostname "$HOSTNAME" \
        --ostype debian \
        --arch amd64 \
        --unprivileged "$UNPRIVILEGED" \
        --features "nesting=1,keyctl=1" \
        --cores "$CORES" \
        --memory "$MEMORY_MB" \
        --swap "$SWAP_MB" \
        --rootfs "${STORAGE}:${DISK_GB}" \
        --net0 "$net" \
        --onboot "$START_ON_BOOT" \
        --start 1

      CREATED_CT=1

      if [[ -n "$DNS_SERVER" ]]; then
        pct set "$CTID" --nameserver "$DNS_SERVER"
      fi

      # Docker in unprivileged LXC benefits from these mappings/settings.
      local config="/etc/pve/lxc/${CTID}.conf"
      grep -q '^lxc.apparmor.profile:' "$config" || echo 'lxc.apparmor.profile: unconfined' >> "$config"
      grep -q '^lxc.cgroup2.devices.allow: a' "$config" || echo 'lxc.cgroup2.devices.allow: a' >> "$config"
      grep -q '^lxc.cap.drop:' "$config" || echo 'lxc.cap.drop:' >> "$config"

      pct reboot "$CTID"
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
      echo "Containern fick inte fungerande nätverk/DNS."
      exit 1
    }

    install_inside_container() {
      CURRENT_STEP="installerar applikationen"
      log "Installerar Mail Attachment Hub i LXC ${CTID}"

      pct exec "$CTID" -- env \
        REPO="$REPO" \
        BRANCH="$BRANCH" \
        INSTALL_DIR="$INSTALL_DIR" \
        ADMIN_EMAIL="$ADMIN_EMAIL" \
        TZ="$TZ" \
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
            make \
            openssl \
            jq \
            locales

          locale-gen C.UTF-8 >/dev/null 2>&1 || true

          if ! command -v docker >/dev/null 2>&1; then
            curl -fsSL https://get.docker.com | sh
          fi

          systemctl enable --now docker

          if ! docker compose version >/dev/null 2>&1; then
            apt-get install -y docker-compose-plugin
          fi

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

            POSTGRES_PASSWORD="$(openssl rand -base64 36 | tr -d "\n" | tr "/+" "_-")"
            APP_SECRET_KEY="$(openssl rand -hex 48)"
            ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -d "\n" | tr "/+" "_-")"

            sed -i \
              -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" \
              -e "s|^APP_SECRET_KEY=.*|APP_SECRET_KEY=${APP_SECRET_KEY}|" \
              -e "s|^ADMIN_EMAIL=.*|ADMIN_EMAIL=${ADMIN_EMAIL}|" \
              -e "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD}|" \
              -e "s|^TZ=.*|TZ=${TZ}|" \
              .env

            cat > /root/mailhub-credentials.txt <<EOF
Mail Attachment Hub
Admin email: ${ADMIN_EMAIL}
Admin password: ${ADMIN_PASSWORD}
EOF
            chmod 600 /root/mailhub-credentials.txt
          fi

          docker compose --env-file .env -f compose.yml pull --ignore-buildable || true
          docker compose --env-file .env -f compose.yml build --pull
          docker compose --env-file .env -f compose.yml up -d

          for _ in $(seq 1 90); do
            if curl -fsS http://127.0.0.1:8080/health/ready >/dev/null 2>&1; then
              break
            fi
            sleep 2
          done

          curl -fsS http://127.0.0.1:8080/health/ready >/dev/null

          cat > /usr/local/bin/mailhub <<'"'"'EOF'"'"'
#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="/opt/mail-attachment-hub"
cd "$APP_DIR"
cmd="${1:-help}"
shift || true

case "$cmd" in
  status)
    docker compose --env-file .env -f compose.yml ps
    curl -fsS http://127.0.0.1:8080/health/ready | jq .
    ;;
  logs)
    docker compose --env-file .env -f compose.yml logs -f --tail=200 "$@"
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
    ./scripts/backup.sh
    git fetch origin main
    git pull --ff-only origin main
    docker compose --env-file .env -f compose.yml build --pull
    docker compose --env-file .env -f compose.yml up -d
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
    cat /root/mailhub-credentials.txt
    ;;
  *)
    cat <<HELP
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

    show_result() {
      CURRENT_STEP="slutför installation"
      local ip
      ip="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
      local credentials
      credentials="$(pct exec "$CTID" -- cat /root/mailhub-credentials.txt)"

      log "Installation klar"
      echo
      echo "LXC-ID:       ${CTID}"
      echo "IP-adress:    ${ip}"
      echo "Webbgränssnitt: http://${ip}:3000"
      echo "API:            http://${ip}:8080"
      echo
      echo "$credentials"
      echo
      echo "Administrationskommandon inne i containern:"
      echo "  pct enter ${CTID}"
      echo "  mailhub status"
      echo "  mailhub logs"
      echo "  mailhub update"
      echo "  mailhub backup"
      echo "  mailhub doctor"
    }

    main() {
      require_root
      require_proxmox
      choose_ctid
      validate_storage
      local template
      template="$(download_template)"
      create_container "$template"
      wait_for_network
      install_inside_container
      show_result
    }

    main "$@"
