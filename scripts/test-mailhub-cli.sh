#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"

for command_name in \
  credentials \
  status \
  doctor \
  logs \
  restart \
  update \
  update-status \
  repair
do
  grep -q "${command_name}" scripts/mailhub-cli.sh
done

grep -q 'mailhub doctor' scripts/write-install-info.sh
grep -q 'mailhub credentials' scripts/write-install-info.sh
grep -q 'mailhub-cli.sh' proxmox/install.sh
grep -q 'write-install-info.sh' proxmox/install.sh
grep -q 'mailhub doctor' proxmox/install.sh
grep -q '/root/mailhub-install-info.txt' proxmox/install.sh

echo "MailHub CLI/install-result regression checks: OK"
