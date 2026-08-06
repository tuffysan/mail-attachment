#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./scripts/require-env.sh
# shellcheck disable=SC1091
source .env
base_url="http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}"
curl --fail --silent --show-error "$base_url/health/live" | grep -q '"status":"ok"'
curl --fail --silent --show-error "$base_url/health/ready" | grep -q '"status":"ok"'
echo "Backend live and ready checks passed."
