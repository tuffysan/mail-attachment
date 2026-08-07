# LXC updates

A running Proxmox LXC installation can update itself from GitHub without being recreated.

## Update

Inside the LXC:

```bash
mailhub update
```

The command fetches `origin/main`, creates a pre-update backup, rebuilds the Docker images,
starts the updated stack, and checks both backend and frontend.

## Rollback

After an update, the previous Git commit is shown. Roll back with:

```bash
mailhub rollback <previous-commit>
```

## Version

```bash
mailhub version
```

## Existing LXC installation

After these files have been pushed to GitHub, run once:

```bash
cd /opt/mail-attachment-hub
git pull --ff-only origin main
chmod +x scripts/install-lxc-cli.sh
./scripts/install-lxc-cli.sh
```

After that:

```bash
mailhub update
```
