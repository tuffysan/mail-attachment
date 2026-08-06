#!/usr/bin/env bash
set -Eeuo pipefail
REPO="${REPO:-tuffysan/mail-attachment}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/mail-attachment-hub}"
[[ $EUID -eq 0 ]] || { echo "Run as root."; exit 1; }
command -v docker >/dev/null || {
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
}
apt-get update
apt-get install -y git make curl openssl
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" fetch origin "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
else
  rm -rf "$INSTALL_DIR"
  git clone --branch "$BRANCH" "https://github.com/$REPO.git" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
[[ -f .env ]] || make init
make up
scripts/doctor.sh
ip="$(hostname -I | awk '{print $1}')"
echo "Mail Attachment Hub: http://$ip:3000"
echo "Credentials: $INSTALL_DIR/.env"
