#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
required=(
  backend/Dockerfile
  backend/pyproject.toml
  backend/src/mailhub/main.py
  backend/src/mailhub/config.py
  backend/src/mailhub/health.py
  backend/tests/test_api.py
)
for file in "${required[@]}"; do
  [[ -s "$file" ]] || { echo "Missing or empty backend file: $file" >&2; exit 1; }
done
grep -q 'health/live' backend/src/mailhub/main.py
grep -q 'health/ready' backend/src/mailhub/main.py
python3 -m compileall -q backend/src backend/tests
echo 'Backend static checks passed.'
