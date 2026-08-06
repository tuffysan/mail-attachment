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
destination_id="$(
  curl -fsS "$base/api/v1/storage-destinations" \
    -H "Authorization: Bearer $token" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])'
)"
rule="$(
  curl -fsS -X POST "$base/api/v1/rules" \
    -H "Authorization: Bearer $token" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"Smoke PDF rule\",\"priority\":10,\"filename_pattern\":\"\\\\.pdf$\",\"folder_template\":\"{year}/{month}/{sender}\",\"destination_ids\":[\"$destination_id\"]}"
)"
rule_id="$(printf '%s' "$rule" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
curl -fsS -X POST "$base/api/v1/rules/simulate" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d '{"email_account_id":"00000000-0000-0000-0000-000000000000","sender":"invoice@example.com","subject":"Invoice","filename":"invoice.pdf","content_type":"application/pdf","size_bytes":1000}' |
  python3 -c 'import json,sys; data=json.load(sys.stdin); assert any(x["matched"] for x in data)'
curl -fsS -X DELETE "$base/api/v1/rules/$rule_id" -H "Authorization: Bearer $token"
echo "Rule engine CRUD and simulation smoke test passed."
