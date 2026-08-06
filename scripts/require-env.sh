#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env ]] || {
  echo 'Missing .env. Run: make init' >&2
  exit 1
}
