#!/usr/bin/env bash
set -Eeuo pipefail
source .env
base="http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}"
token="$(curl -fsS -X POST "$base/api/v1/auth/login" -H 'Content-Type: application/json'       -d "{"email":"${ADMIN_EMAIL}","password":"${ADMIN_PASSWORD}"}" |
  python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')"
curl -fsS "$base/api/v1/messages" -H "Authorization: Bearer $token" | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'
curl -fsS "$base/api/v1/activity" -H "Authorization: Bearer $token" | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'
docker compose --env-file .env -f compose.yml ps worker | grep -q worker
echo "Mail engine API and worker smoke test passed."
