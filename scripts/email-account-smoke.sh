#!/usr/bin/env bash
set -Eeuo pipefail

source .env

base_url="http://${BACKEND_BIND_ADDRESS:-127.0.0.1}:${BACKEND_PORT:-8080}"
token="$(
  curl -fsS -X POST "$base_url/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

created="$(
  curl -fsS -X POST "$base_url/api/v1/email-accounts" \
    -H "Authorization: Bearer $token" \
    -H 'Content-Type: application/json' \
    -d '{"name":"Smoke account","email_address":"smoke@example.com","host":"imap.example.invalid","port":993,"username":"smoke@example.com","password":"not-a-real-password","mailbox":"INBOX","use_ssl":true,"is_enabled":true}'
)"
account_id="$(printf '%s' "$created" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

curl -fsS "$base_url/api/v1/email-accounts" \
  -H "Authorization: Bearer $token" |
  python3 -c 'import json,sys; data=json.load(sys.stdin); assert any(x["name"]=="Smoke account" for x in data)'

curl -fsS -X DELETE "$base_url/api/v1/email-accounts/$account_id" \
  -H "Authorization: Bearer $token"

printf '%s\n' "Email account CRUD smoke test passed."
