#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
required=(README.md LICENSE SECURITY.md CONTRIBUTING.md CODE_OF_CONDUCT.md compose.yml .env.example Makefile)
for file in "${required[@]}"; do
  [[ -s "$file" ]] || { echo "Missing or empty: $file" >&2; exit 1; }
done
if grep -RIn --exclude-dir=.git --exclude='.env.example' -E '(BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AIza[0-9A-Za-z_-]{30,}|ghp_[0-9A-Za-z]{30,})' .; then
  echo 'Possible committed secret detected.' >&2
  exit 1
fi
echo 'Repository checks passed.'
