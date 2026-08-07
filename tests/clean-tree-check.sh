#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

failed=0

# Paths that are always generated locally and must never be committed.
for path in \
  .env \
  mailhub-credentials.env \
  mailhub-install-info.txt \
  frontend/node_modules \
  frontend/dist \
  backend/.pytest_cache
do
  if [[ -e "$path" ]]; then
    echo "Generated/local path must not be committed: $path" >&2
    failed=1
  fi
done

# 002F release structure.
required=(
  "proxmox/install.sh"
  "scripts/install-update-agent.sh"
  "scripts/update-agent.sh"
  "scripts/lxc-update.sh"
  "scripts/lxc-rollback.sh"
  "scripts/mailhub-cli.sh"
  "scripts/storage-self-test.sh"
  "scripts/post-install-check.sh"
  "compose.yml"
  "compose.override.lxc.yml"
  "backend"
  "frontend"
)

for path in "${required[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "Required 002F release path is missing: $path" >&2
    failed=1
  fi
done

# Detect accidental cache/build artifacts anywhere in the repository.
if find . \
  -path './.git' -prune -o \
  -path './frontend/node_modules' -print -o \
  -path './frontend/dist' -print -o \
  -name '__pycache__' -print -o \
  -name '*.pyc' -print |
  grep -q .
then
  echo "Generated build/cache artifacts detected." >&2
  failed=1
fi

[[ "$failed" -eq 0 ]] || exit 1
echo "Clean repository tree checks passed."
