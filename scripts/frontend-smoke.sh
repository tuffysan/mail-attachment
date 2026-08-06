#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE="${ENV_FILE:-.env}"
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE. Run make init first." >&2; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"
BASE_URL="http://${FRONTEND_BIND_ADDRESS:-127.0.0.1}:${FRONTEND_PORT:-3000}"

html="$(curl --fail --silent --show-error "$BASE_URL/")"
grep -q 'Mail Attachment Hub' <<<"$html"

ready="$(curl --fail --silent --show-error "$BASE_URL/health/ready")"
grep -q '"status":"ok"' <<<"$ready"

echo "Frontend and reverse proxy smoke checks passed."
