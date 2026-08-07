#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$APP_DIR"

grep -Fq 'backup_create)' scripts/update-agent.sh
grep -Fq 'backup_restore)' scripts/update-agent.sh
grep -Fq 'backup_list)' scripts/update-agent.sh
grep -Fq 'pre-restore-' scripts/update-agent.sh
grep -Fq '/var/backups/mailhub' scripts/update-agent.sh
grep -Fq 'maintenance-status.json' scripts/install-update-agent.sh
grep -Fq 'backups.json' scripts/install-update-agent.sh
grep -Fq 'scripts/backup.sh' proxmox/install.sh
grep -Fq 'scripts/restore.sh' proxmox/install.sh
grep -Fq 'sha256sum -c SHA256SUMS' scripts/restore.sh
grep -Fq 'CURRENT_POSTGRES_PASSWORD' scripts/restore.sh
grep -Fq 'APP_SECRET_KEY' scripts/restore.sh

echo "Backup/restore platform regression checks: OK"
