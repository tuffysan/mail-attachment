#!/usr/bin/env bash
set -Eeuo pipefail
file="${1:-.env.example}"
[[ -f "$file" ]] || { echo "Missing $file" >&2; exit 1; }
required=(POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD REDIS_MAXMEMORY APP_SECRET_KEY TZ)
for key in "${required[@]}"; do
  grep -qE "^${key}=" "$file" || { echo "Missing variable ${key} in ${file}" >&2; exit 1; }
done
echo "Environment checks passed for ${file}."
