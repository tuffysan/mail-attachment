#!/usr/bin/env bash
set -Eeuo pipefail
source .env
base="http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}"
response=$(curl -fsS -X POST "$base/api/v1/auth/login" -H 'Content-Type: application/json' -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
token=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])' <<<"$response")
curl -fsS "$base/api/v1/auth/me" -H "Authorization: Bearer $token" | grep -q '"is_admin":true'
echo "Authentication smoke test passed."
