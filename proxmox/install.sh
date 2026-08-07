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
TMP_INNER=""

cleanup() {
  [[ -z "$TMP_INNER" || ! -f "$TMP_INNER" ]] || rm -f "$TMP_INNER"
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
    echo "LXC ${CTID} finns kvar." >&2
    echo "Logg: pct exec ${CTID} -- cat /root/mailhub-install.log" >&2
    echo "Status: pct exec ${CTID} -- cat /root/mailhub-install.status" >&2
  fi
  exit "$code"
}
trap on_error ERR

log() {
  printf '\n[%(%H:%M:%S)T] %s\n' -1 "$*"
}

require_environment() {
  [[ $EUID -eq 0 ]] || { echo "Kör som root på Proxmox."; exit 1; }
  for cmd in pct pvesh pveam pvesm; do
    command -v "$cmd" >/dev/null 2>&1 || {
      echo "${cmd} saknas. Kör på Proxmox-värden."
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

  return 0
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

wait_for_network() {
  CURRENT_STEP="väntar på nätverk"
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

build_inner_script() {
  TMP_INNER="$(mktemp /tmp/mailhub-inner.XXXXXX.sh)"
  cat > "$TMP_INNER" <<'INNER'
#!/usr/bin/env bash
set -Eeuo pipefail

exec > >(tee -a /root/mailhub-install.log) 2>&1
echo "RUNNING" > /root/mailhub-install.status

fail() {
  local code=$?
  echo "FAILED:${code}" > /root/mailhub-install.status
  exit "$code"
}
trap fail ERR

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
apt-get update
apt-get install -y ca-certificates curl git jq openssl iproute2 util-linux

step "Installerar Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

step "Hämtar projektet"
rm -rf "$INSTALL_DIR"
git clone --branch "$BRANCH" "https://github.com/${REPO}.git" "$INSTALL_DIR"

cd "$INSTALL_DIR"

echo
echo "============================================================"
echo " Installing MailHub Update Agent"
echo "============================================================"

for required_script in \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh \
  scripts/storage-self-test.sh \
  scripts/repair-storage-permissions.sh \
  scripts/mailhub-cli.sh \
  scripts/write-install-info.sh \
  scripts/lxc-rollback.sh
do
  if [[ ! -f "$required_script" ]]; then
    echo "Required update-agent file is missing: $required_script" >&2
    exit 1
  fi
done

chmod +x \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh \
  scripts/storage-self-test.sh \
  scripts/repair-storage-permissions.sh \
  scripts/mailhub-cli.sh \
  scripts/write-install-info.sh \
  scripts/lxc-rollback.sh

echo "Running scripts/install-update-agent.sh..."
./scripts/install-update-agent.sh

systemctl daemon-reload
systemctl enable --now mailhub-update-agent.path

UPDATE_AGENT_ENABLED="$(systemctl is-enabled mailhub-update-agent.path 2>/dev/null || true)"
UPDATE_AGENT_ACTIVE="$(systemctl is-active mailhub-update-agent.path 2>/dev/null || true)"

echo
echo "Update agent status:"
echo "  enabled: ${UPDATE_AGENT_ENABLED}"
echo "  active:  ${UPDATE_AGENT_ACTIVE}"

if [[ "$UPDATE_AGENT_ENABLED" != "enabled" ]]; then
  echo "mailhub-update-agent.path was not enabled." >&2
  exit 1
fi

if [[ "$UPDATE_AGENT_ACTIVE" != "active" ]]; then
  echo "mailhub-update-agent.path is not active." >&2
  systemctl --no-pager --full status mailhub-update-agent.path || true
  exit 1
fi

if [[ ! -d /var/lib/mailhub-control ]]; then
  echo "/var/lib/mailhub-control was not created." >&2
  exit 1
fi

CONTROL_OWNER="$(stat -c '%u:%g' /var/lib/mailhub-control)"
CONTROL_MODE="$(stat -c '%a' /var/lib/mailhub-control)"

echo "  control owner: ${CONTROL_OWNER}"
echo "  control mode:  ${CONTROL_MODE}"

if [[ "$CONTROL_OWNER" != "10001:10001" ]]; then
  echo "Wrong owner on /var/lib/mailhub-control: ${CONTROL_OWNER}" >&2
  exit 1
fi

if ! setpriv --reuid=10001 --regid=10001 --clear-groups \
  sh -c 'touch /var/lib/mailhub-control/.installer-write-test && rm -f /var/lib/mailhub-control/.installer-write-test'
then
  echo "/var/lib/mailhub-control is not writable by UID/GID 10001." >&2
  exit 1
fi

echo "Update agent control directory: writable"

cp .env.example .env

POSTGRES_PASSWORD="$(openssl rand -base64 36 | tr -d '\n' | tr '/+' '_-')"
APP_SECRET_KEY="$(openssl rand -hex 48)"
ADMIN_PASSWORD="$(openssl rand -base64 24 | tr -d '\n' | tr '/+' '_-')"

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

step "Bygger images"
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml build --pull

step "Förbereder lagring"
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml run --rm --no-deps storage-init

step "Startar tjänster"
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml up -d

echo
echo "============================================================"
echo " Verifying MailHub Update Agent"
echo "============================================================"

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend sh -c '
    set -e
    echo "Backend identity:"
    id
    echo
    echo "Control directory:"
    ls -ldn /control
    echo
    touch /control/.mailhub-install-test
    rm -f /control/.mailhub-install-test
    echo "Update agent control directory: writable"
  '

step "Verifierar lagringsrättigheter"
./scripts/storage-self-test.sh

step "Självtestar GitHub update-agent"

# Send the exact kind of request the backend/UI uses.
REQUEST_TMP="/var/lib/mailhub-control/.request-installer.tmp"
jq -n \
  --arg requested_at "$(date --iso-8601=seconds)" \
  '{action:"check", requested_at:$requested_at}' > "$REQUEST_TMP"
chown 10001:10001 "$REQUEST_TMP"
chmod 0660 "$REQUEST_TMP"
mv -f "$REQUEST_TMP" /var/lib/mailhub-control/request.json

agent_done=0
for attempt in $(seq 1 45); do
  if [[ ! -f /var/lib/mailhub-control/request.json ]] &&
     [[ -s /var/lib/mailhub-control/status.json ]] &&
     jq -e . /var/lib/mailhub-control/status.json >/dev/null 2>&1; then
    agent_state="$(jq -r '.state // empty' /var/lib/mailhub-control/status.json)"
    if [[ "$agent_state" != "checking" && "$agent_state" != "idle" && -n "$agent_state" ]]; then
      agent_done=1
      break
    fi
  fi

  printf '\rUpdate-agent %02d/45' "$attempt"
  sleep 1
done
echo

if [[ "$agent_done" != 1 ]]; then
  echo "Update-agent self-test timed out." >&2
  echo "systemd status:" >&2
  systemctl --no-pager --full status mailhub-update-agent.path || true
  systemctl --no-pager --full status mailhub-update-agent.service || true
  echo "status.json:" >&2
  cat /var/lib/mailhub-control/status.json 2>/dev/null || true
  echo "update.log:" >&2
  tail -100 /var/lib/mailhub-control/update.log 2>/dev/null || true
  exit 1
fi

case "$agent_state" in
  up_to_date|update_available|success)
    ;;
  error)
    echo "Update-agent svarade men GitHub-kontrollen misslyckades." >&2
    cat /var/lib/mailhub-control/status.json | jq . >&2 || true
    tail -100 /var/lib/mailhub-control/update.log >&2 || true
    exit 1
    ;;
  *)
    echo "Oväntad update-agent status: $agent_state" >&2
    cat /var/lib/mailhub-control/status.json | jq . >&2 || true
    exit 1
    ;;
esac

# Verify that backend sees the exact same non-empty valid status.
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec -T backend python - <<'PY'
import json
from pathlib import Path

path = Path("/control/status.json")
if not path.exists():
    raise SystemExit("/control/status.json saknas")

if path.stat().st_size <= 0:
    raise SystemExit("/control/status.json är tom")

data = json.loads(path.read_text(encoding="utf-8"))
state = data.get("state")

if state not in {"up_to_date", "update_available", "success"}:
    raise SystemExit(f"Oväntad update-agent state i backend: {state!r}")

print("Update agent end-to-end: OK")
print("State:", state)
print("Installed:", data.get("installed_commit"))
print("Latest:", data.get("latest_commit"))
PY


step "Väntar på webbgränssnitt och API"
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

  [[ "$api_ok" == 1 && "$frontend_ok" == 1 ]] && break
  sleep 2
done
echo

docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml ps

[[ "$api_ok" == 1 && "$frontend_ok" == 1 ]] || {
  docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml logs --tail=150 backend frontend
  exit 1
}

ss -lnt | grep -qE "0\.0\.0\.0:${WEB_PORT}|:::${WEB_PORT}" || {
  echo "Frontend-port ${WEB_PORT} exponeras inte."
  ss -lnt
  exit 1
}

ss -lnt | grep -qE "0\.0\.0\.0:${API_PORT}|:::${API_PORT}" || {
  echo "API-port ${API_PORT} exponeras inte."
  ss -lnt
  exit 1
}

step "Installerar mailhub-kommandot"
install -m 0755 scripts/mailhub-cli.sh /usr/local/bin/mailhub

step "Sparar installationsinformation"
chmod +x scripts/write-install-info.sh
scripts/write-install-info.sh >/root/mailhub-install-info.txt.tmp
mv -f /root/mailhub-install-info.txt.tmp /root/mailhub-install-info.txt
chmod 0600 /root/mailhub-install-info.txt

step "Kör slutlig systemkontroll"
mailhub doctor

echo "COMPLETE" > /root/mailhub-install.status
step "Installation klar"
INNER
  chmod +x "$TMP_INNER"
}

start_install_job() {
  CURRENT_STEP="startar installationstjänst i LXC"
  log "$CURRENT_STEP"

  pct push "$CTID" "$TMP_INNER" /root/mailhub-install-inside.sh --perms 0755

  pct exec "$CTID" -- bash -lc "
    rm -f /root/mailhub-install.status /root/mailhub-install.log
    systemd-run \
      --unit=mailhub-install \
      --property=Type=exec \
      --setenv=REPO='${REPO}' \
      --setenv=BRANCH='${BRANCH}' \
      --setenv=ADMIN_EMAIL='${ADMIN_EMAIL}' \
      --setenv=TZ='${TZ}' \
      --setenv=WEB_PORT='${WEB_PORT}' \
      --setenv=API_PORT='${API_PORT}' \
      /root/mailhub-install-inside.sh
  "
}

monitor_install_job() {
  CURRENT_STEP="installerar applikationen"
  log "$CURRENT_STEP"

  local last_lines=""
  for attempt in $(seq 1 300); do
    local status
    status="$(pct exec "$CTID" -- bash -lc 'cat /root/mailhub-install.status 2>/dev/null || echo STARTING')"

    printf "\rStatus: %-12s  Kontroll %03d/300" "$status" "$attempt"

    if [[ "$status" == "COMPLETE" ]]; then
      echo
      return
    fi

    if [[ "$status" == FAILED:* ]]; then
      echo
      echo "Installationstjänsten rapporterade fel: ${status}"
      pct exec "$CTID" -- tail -n 160 /root/mailhub-install.log
      exit 1
    fi

    # Every 10 seconds show the latest meaningful progress line.
    if (( attempt % 5 == 0 )); then
      local current
      current="$(pct exec "$CTID" -- bash -lc "grep -E '^\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]' /root/mailhub-install.log 2>/dev/null | tail -1" || true)"
      if [[ -n "$current" && "$current" != "$last_lines" ]]; then
        echo
        echo "$current"
        last_lines="$current"
      fi
    fi

    sleep 2
  done

  echo
  echo "Installationen tog längre än 10 minuter."
  pct exec "$CTID" -- tail -n 160 /root/mailhub-install.log
  exit 1
}

show_result() {
  CURRENT_STEP="visar installationsinformation"
  log "$CURRENT_STEP"
  echo
  echo "============================================================"
  echo " Mail Attachment Hub installerades korrekt"
  echo "============================================================"
  echo "LXC-ID: ${CTID}"
  echo
  if pct exec "$CTID" -- test -s /root/mailhub-install-info.txt >/dev/null 2>&1; then
    pct exec "$CTID" -- cat /root/mailhub-install-info.txt || true
  else
    local ip email password
    ip="$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}' || true)"
    email="$(pct exec "$CTID" -- sed -n 's/^ADMIN_EMAIL=//p' /root/mailhub-credentials.env 2>/dev/null || true)"
    password="$(pct exec "$CTID" -- sed -n 's/^ADMIN_PASSWORD=//p' /root/mailhub-credentials.env 2>/dev/null || true)"
    ip="${ip:-unknown}"; email="${email:-unknown}"; password="${password:-unknown}"
    echo "IP:       ${ip}"
    echo "Web UI:   http://${ip}:${WEB_PORT}"
    echo "API:      http://${ip}:${API_PORT}"
    echo "Login:    ${email}"
    echo "Password: ${password}"
  fi
  echo
  echo "Credentials: pct exec ${CTID} -- mailhub credentials"
  echo "Doctor:      pct exec ${CTID} -- mailhub doctor"
  echo "============================================================"
}

main() {
  require_environment
  choose_ctid
  validate_storage
  download_template
  create_container
  wait_for_network
  build_inner_script
  start_install_job
  monitor_install_job
  show_result
}

main "$@"
