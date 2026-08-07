#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/backend"

echo "============================================================"
echo " Mail Attachment Hub - Backend CI"
echo "============================================================"

python -m pip install --upgrade pip
python -m pip install -e '.[test]'

echo
echo "[1/2] Python compile"
python -m compileall -q src tests

echo
echo "[2/2] Pytest"
pytest -q

echo
echo "Backend CI: PASSED"
