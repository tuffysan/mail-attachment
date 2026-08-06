#!/usr/bin/env bash
set -Eeuo pipefail
source .env
base="http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}"
token="$(
  curl -fsS -X POST "$base/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

curl -fsS "$base/api/v1/storage/providers" \
  -H "Authorization: Bearer $token" |
  python3 -c 'import json,sys; data=json.load(sys.stdin); assert any(x["key"]=="drive" for x in data); assert any(x["key"]=="sftp" for x in data)'

created="$(
  curl -fsS -X POST "$base/api/v1/storage/destinations" \
    -H "Authorization: Bearer $token" \
    -H 'Content-Type: application/json' \
    -d '{"name":"Smoke local storage","provider":"local","base_path":"/data/routed/smoke","config":{},"is_enabled":true}'
)"
id="$(printf '%s' "$created" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

curl -fsS -X POST "$base/api/v1/storage/destinations/$id/test" \
  -H "Authorization: Bearer $token" |
  python3 -c 'import json,sys; assert json.load(sys.stdin)["status"]=="ok"'

curl -fsS -X DELETE "$base/api/v1/storage/destinations/$id" \
  -H "Authorization: Bearer $token"

docker compose --env-file .env -f compose.yml exec -T backend rclone version >/dev/null
echo "Storage platform CRUD, test and rclone smoke test passed."
