#!/usr/bin/env bash
set -Eeuo pipefail
forbidden=("install.sh" "requirements.txt" "app" "systemd" "plugins")
failed=0
for path in "${forbidden[@]}"; do
  if [[ -e "$path" ]]; then
    echo "Legacy prototype path must not exist in Step 003: $path" >&2
    failed=1
  fi
done
for dir in frontend installer; do
  if [[ -d "$dir" ]]; then
    unexpected="$(find "$dir" -mindepth 1 -type f ! -name README.md -print -quit)"
    if [[ -n "$unexpected" ]]; then
      echo "Unexpected application file before its planned sprint step: $unexpected" >&2
      failed=1
    fi
  fi
done
[[ "$failed" -eq 0 ]] || exit 1
echo "Clean repository tree checks passed."
