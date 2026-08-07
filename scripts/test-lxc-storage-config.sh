#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"

grep -q 'storage-init:' compose.override.lxc.yml
grep -q '10001:10001' compose.override.lxc.yml
grep -q 'attachment_data:/data/attachments' compose.override.lxc.yml
grep -q 'routed_data:/data/routed' compose.override.lxc.yml
grep -q 'condition: service_completed_successfully' compose.override.lxc.yml

grep -q 'scripts/storage-self-test.sh' proxmox/install.sh
grep -q 'run --rm --no-deps storage-init' proxmox/install.sh
grep -q 'scripts/storage-self-test.sh' scripts/lxc-update.sh
grep -q 'run --rm --no-deps storage-init' scripts/lxc-update.sh

echo "LXC storage configuration regression checks: OK"
