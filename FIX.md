# Installer fix

The Proxmox installer previously returned exit status 2 when the automatically selected CT ID was unused. `choose_ctid()` now uses an explicit `if` and returns zero for an available ID.

Use only `proxmox/install.sh` as the canonical Proxmox installer.
