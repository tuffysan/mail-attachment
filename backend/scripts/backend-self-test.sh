#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$BACKEND_DIR"

echo "============================================================"
echo " Mail Attachment Hub - Backend Self Test"
echo "============================================================"
echo

python - <<'PY'
import importlib
import sys

required = {
    "asyncpg": "PostgreSQL async driver",
    "redis": "Redis client",
    "pwdlib": "Password hashing",
    "fastapi": "API framework",
    "sqlalchemy": "ORM",
    "httpx": "HTTP/OAuth client",
    "cryptography": "Credential encryption",
}

missing = []
for module, purpose in required.items():
    try:
        imported = importlib.import_module(module)
        version = getattr(imported, "__version__", "installed")
        print(f"[OK] {module}: {version} ({purpose})")
    except Exception as exc:
        missing.append((module, purpose, str(exc)))
        print(f"[FAIL] {module}: {exc}")

if missing:
    print()
    print("Missing backend runtime dependencies:")
    for module, purpose, error in missing:
        print(f"  - {module}: {purpose} ({error})")
    raise SystemExit(1)
PY

echo
echo "Compiling backend source..."
python -m compileall -q src
echo "[OK] Python compilation"

echo
echo "Running backend test suite..."
PYTHONPATH=src python -m pytest -q

echo
echo "============================================================"
echo " Backend self test passed"
echo "============================================================"
