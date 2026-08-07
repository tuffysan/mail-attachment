#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "============================================================"
echo " Mail Attachment Hub - Release Gate"
echo "============================================================"

echo
echo "[1/5] Shell syntax"
while IFS= read -r file; do
  bash -n "$file"
done < <(
  {
    printf '%s\n' proxmox/install.sh
    find scripts tests -type f -name '*.sh' -print
  } | sort -u
)

echo
echo "[2/5] Static repository checks"
make check

echo
echo "[3/5] Release self-test"
bash ./scripts/release-self-test.sh

echo
echo "[4/5] Critical files"
for file in \
  VERSION \
  .env.example \
  compose.yml \
  compose.override.lxc.yml \
  backend/alembic/versions/0008_timestamp_defaults.py \
  scripts/install-update-agent.sh \
  scripts/storage-self-test.sh \
  scripts/post-install-check.sh \
  scripts/lxc-rollback.sh
do
  test -s "$file" || {
    echo "Missing or empty critical file: $file" >&2
    exit 1
  }
done

echo
echo "[5/5] Release manifest JSON"
python - <<'PY'
import json
from pathlib import Path

path = Path("release-manifest-002F.json")
data = json.loads(path.read_text(encoding="utf-8"))
assert data.get("release") == "002F"
assert data.get("files")
print(f"Manifest entries: {len(data['files'])}")
PY

echo
echo "Release Gate: PASSED"
