#!/usr/bin/env bash
set -Eeuo pipefail

CTID="${1:-${CTID:-}}"
[[ $EUID -eq 0 ]] || {
  echo "Kör som root på Proxmox."
  exit 1
}
[[ -n "$CTID" ]] || {
  echo "Användning: $0 CTID"
  exit 1
}

read -r -p "Ta bort LXC ${CTID} och all Mail Attachment Hub-data? [y/N] " answer
[[ "$answer" =~ ^[Yy]$ ]] || exit 0

pct stop "$CTID" 2>/dev/null || true
pct destroy "$CTID" --purge
echo "LXC ${CTID} borttagen."
