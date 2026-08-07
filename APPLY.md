# Apply LXC update support

Copy the files over the repository, then commit:

```powershell
git add scripts docs/LXC_UPDATES.md
git commit -m "feat(installer): add LXC update and rollback commands"
git push origin main
```

For an existing LXC:

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main
chmod +x scripts/install-lxc-cli.sh
./scripts/install-lxc-cli.sh
mailhub update
```
