#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/frontend"

echo "============================================================"
echo " Mail Attachment Hub - Frontend CI"
echo "============================================================"

node --version
npm --version

# The repository currently has no package-lock.json. Use npm install until a
# lockfile is committed, then npm ci automatically becomes available.
if [[ -f package-lock.json ]]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi

npm run build

echo
echo "Frontend CI: PASSED"
