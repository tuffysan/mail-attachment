#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ -f .env ]]; then
  echo '.env already exists; no changes made.'
  exit 0
fi

command -v openssl >/dev/null 2>&1 || {
  echo 'openssl is required.' >&2
  exit 1
}

postgres_password="$(openssl rand -base64 36 | tr -d '\n/=+' | cut -c1-32)"
app_secret="$(openssl rand -hex 32)"

cp .env.example .env
python3 - "$postgres_password" "$app_secret" <<'PY'
from pathlib import Path
import sys

path = Path('.env')
text = path.read_text(encoding='utf-8')
text = text.replace('change-this-postgres-password', sys.argv[1])
text = text.replace('replace-with-at-least-32-random-characters', sys.argv[2])
path.write_text(text, encoding='utf-8')
PY
chmod 600 .env
echo 'Created .env with generated secrets.'
