#!/usr/bin/env bash
set -Eeuo pipefail

forbidden=("install.sh" "requirements.txt" "app" "systemd" "plugins")
failed=0
for path in "${forbidden[@]}"; do
  if [[ -e "$path" ]]; then
    echo "Legacy prototype path must not exist in Step 006: $path" >&2
    failed=1
  fi
done

if [[ -d installer ]]; then
  unexpected="$(find installer -mindepth 1 -type f ! -name README.md -print -quit)"
  if [[ -n "$unexpected" ]]; then
    echo "Unexpected installer file before its planned sprint step: $unexpected" >&2
    failed=1
  fi
fi

[[ "$failed" -eq 0 ]] || exit 1
echo "Clean repository tree checks passed."
