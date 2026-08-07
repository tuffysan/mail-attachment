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

if [[ -f "$CREDENTIALS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CREDENTIALS_FILE"
fi

WEB_PORT="${WEB_PORT:-$(sed -n 's/^FRONTEND_PORT=//p' .env 2>/dev/null | tail -1)}"
API_PORT="${API_PORT:-$(sed -n 's/^BACKEND_PORT=//p' .env 2>/dev/null | tail -1)}"
WEB_PORT="${WEB_PORT:-3000}"
API_PORT="${API_PORT:-8080}"

VERSION="$(cat VERSION 2>/dev/null || echo unknown)"
COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

# Installer-managed chmod operations must not count as source modifications.
git config core.fileMode false 2>/dev/null || true
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
IP="${IP:-127.0.0.1}"

failures=0

pass() {
  printf '[OK]   %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1" >&2
  failures=$((failures + 1))
}

echo "============================================================"
echo " Mail Attachment Hub - Post Install Check"
echo "============================================================"
echo "Version: ${VERSION}"
echo "Commit:  ${COMMIT}"
echo "IP:      ${IP}"
echo

if git diff --quiet && git diff --cached --quiet; then
  pass "Git working tree clean"
else
  fail "Git working tree contains local changes"
  git status --short || true
fi

if docker compose --env-file .env "${COMPOSE[@]}" config >/dev/null; then
  pass "Docker Compose configuration"
else
  fail "Docker Compose configuration"
fi

for service in postgres redis backend worker frontend; do
  container_id="$(
    docker compose --env-file .env "${COMPOSE[@]}" ps -q "$service" 2>/dev/null || true
  )"

  if [[ -n "$container_id" ]] &&
     [[ "$(docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null || true)" == "true" ]]; then
    pass "Container running: ${service}"
  else
    fail "Container not running: ${service}"
  fi
done

if curl -fsS "http://127.0.0.1:${API_PORT}/health/live" >/dev/null; then
  pass "Backend live endpoint"
else
  fail "Backend live endpoint"
fi

if curl -fsS "http://127.0.0.1:${API_PORT}/health/ready" >/dev/null; then
  pass "Backend readiness endpoint"
else
  fail "Backend readiness endpoint"
fi

if curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null; then
  pass "Frontend HTTP"
else
  fail "Frontend HTTP"
fi

if [[ -x scripts/storage-self-test.sh ]] && scripts/storage-self-test.sh; then
  pass "Storage permissions"
else
  fail "Storage permissions"
fi

if systemctl is-enabled mailhub-update-agent.path >/dev/null 2>&1 &&
   systemctl is-active mailhub-update-agent.path >/dev/null 2>&1; then
  pass "Update agent systemd path"
else
  fail "Update agent systemd path"
fi

if [[ -s /var/lib/mailhub-control/status.json ]] &&
   jq -e . /var/lib/mailhub-control/status.json >/dev/null 2>&1; then
  pass "Update agent status.json"
else
  fail "Update agent status.json"
fi

if [[ -s /root/mailhub-install-info.txt ]]; then
  pass "Installation info"
else
  fail "Installation info"
fi

echo
echo "Web UI: http://${IP}:${WEB_PORT}"
echo "API:    http://${IP}:${API_PORT}"
echo

if [[ "$failures" -eq 0 ]]; then
  echo "============================================================"
  echo " POST INSTALL CHECK: ALL CHECKS PASSED"
  echo "============================================================"
  exit 0
fi

echo "============================================================"
echo " POST INSTALL CHECK: ${failures} CHECK(S) FAILED"
echo "============================================================"
exit 1
