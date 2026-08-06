#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] || { echo "Run as root on Proxmox."; exit 1; }
command -v pct >/dev/null || { echo "pct not found."; exit 1; }
CTID="${CTID:-$(pvesh get /cluster/nextid)}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
BRIDGE="${BRIDGE:-vmbr0}"
DISK="${DISK:-20}"
MEMORY="${MEMORY:-4096}"
CORES="${CORES:-2}"
pveam update >/dev/null
template="$(pveam available --section system | awk '/debian-12-standard/ {print $2}' | sort -V | tail -1)"
pveam list "$TEMPLATE_STORAGE" | grep -q "/$template$" || pveam download "$TEMPLATE_STORAGE" "$template"
pct create "$CTID" "$TEMPLATE_STORAGE:vztmpl/$template" \
  --hostname mail-attachment-hub --unprivileged 1 --features nesting=1,keyctl=1 \
  --cores "$CORES" --memory "$MEMORY" --swap 512 \
  --rootfs "$STORAGE:$DISK" --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" \
  --onboot 1 --start 1
for _ in {1..30}; do
  pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1 && break
  sleep 2
done
pct exec "$CTID" -- bash -lc '
  apt-get update
  apt-get install -y curl ca-certificates
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/install.sh)"
'
ip="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
echo "Installed in LXC $CTID: http://$ip:3000"
