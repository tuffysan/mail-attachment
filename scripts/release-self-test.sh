#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"

echo "Checking shell syntax..."
for file in \
  proxmox/install.sh \
  scripts/install-update-agent.sh \
  scripts/update-agent.sh \
  scripts/lxc-update.sh \
  scripts/lxc-rollback.sh \
  scripts/mailhub-cli.sh \
  scripts/write-install-info.sh \
  scripts/storage-self-test.sh \
  scripts/repair-storage-permissions.sh \
  scripts/repair-update-agent.sh \
  scripts/post-install-check.sh
do
  bash -n "$file"
done

echo "Checking installer release invariants..."
grep -Fq 'replace_env APP_ENV "production"' proxmox/install.sh
grep -Fq 'seq 1 900' proxmox/install.sh
grep -Fq 'mailhub doctor' proxmox/install.sh
grep -Fq 'mailhub verify' proxmox/install.sh
grep -Fq 'scripts/post-install-check.sh' proxmox/install.sh
grep -Fq 'storage-self-test.sh' proxmox/install.sh
grep -Fq 'install-update-agent.sh' proxmox/install.sh

echo "Checking configurable port support..."
grep -Fq '${API_PORT}/health/live' scripts/lxc-update.sh
grep -Fq '${WEB_PORT}/' scripts/lxc-update.sh
grep -Fq '${API_PORT}/health/live' scripts/lxc-rollback.sh
grep -Fq '${WEB_PORT}/' scripts/lxc-rollback.sh

echo "Checking migration..."
test -s backend/alembic/versions/0008_timestamp_defaults.py

echo "Release static self-test: OK"
