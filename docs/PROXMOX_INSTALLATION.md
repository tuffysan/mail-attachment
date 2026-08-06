# Proxmox LXC installation

## One-line installation

Run as `root` on the Proxmox VE host:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

The installer:

1. validates Proxmox tools and storage;
2. downloads the latest Debian 12 standard template;
3. creates an unprivileged LXC with nesting and keyctl;
4. installs Docker Engine and Docker Compose;
5. clones `tuffysan/mail-attachment`;
6. generates database, encryption and administrator secrets;
7. builds and starts the complete stack;
8. waits for `/health/ready`;
9. installs the `mailhub` administration command;
10. prints the URL and generated administrator password.

## Default resources

- 2 CPU cores
- 4096 MB RAM
- 512 MB swap
- 24 GB disk
- DHCP on `vmbr0`
- storage `local-lvm`
- template storage `local`

## Custom installation

```bash
CTID=134     STORAGE=local-lvm     TEMPLATE_STORAGE=local     BRIDGE=vmbr0     DISK_GB=40     MEMORY_MB=6144     CORES=4     ADMIN_EMAIL=admin@example.com     TZ=Europe/Stockholm     bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

Static IP example:

```bash
IPV4=192.168.1.50/24     GATEWAY=192.168.1.1     DNS_SERVER=192.168.1.1     bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```

## Administration

Enter the container:

```bash
pct enter <CTID>
```

Available commands:

```bash
mailhub status
mailhub logs
mailhub restart
mailhub update
mailhub backup
mailhub restore <backup-directory>
mailhub doctor
mailhub credentials
```

## Credentials

Generated credentials are stored only inside the container:

```text
/root/mailhub-credentials.txt
```

The application's full environment is stored in:

```text
/opt/mail-attachment-hub/.env
```

Both files should be protected and included in secure backups.

## Important

Docker in LXC requires nesting. The script also applies LXC settings commonly
needed for Docker in an unprivileged container. Review these settings against
your own security requirements before exposing the service publicly.

Test backup and restore before production use.
