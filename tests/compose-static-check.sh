#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
for token in 'postgres:16-alpine' 'redis:7-alpine' 'healthcheck:' 'postgres_data:' 'redis_data:' '127.0.0.1:'; do
  grep -q "$token" compose.yml || { echo "compose.yml is missing: $token" >&2; exit 1; }
done
echo 'Static Compose checks passed.'
