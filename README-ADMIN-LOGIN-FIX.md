# Admin Login Output Fix

This patch fixes the Proxmox installation result so the generated admin
credentials are always printed at the end of a successful installation.

## What changed

`proxmox/install.sh` now:

1. validates `/root/mailhub-credentials.env` immediately after creating it;
2. refuses to finish successfully if `ADMIN_EMAIL` or `ADMIN_PASSWORD` is empty;
3. prints an `ADMIN LOGIN` block inside the LXC installation log before
   `COMPLETE`;
4. reads credentials directly from `/root/mailhub-credentials.env` on the
   Proxmox host;
5. always prints the admin credentials as a dedicated final block, independent
   of `/root/mailhub-install-info.txt`.

Expected final output:

```text
============================================================
 Mail Attachment Hub installerades korrekt
============================================================
LXC-ID:          134
IP-adress:       192.168.0.x
Webbgränssnitt:  http://192.168.0.x:3000
API:             http://192.168.0.x:8080

============================================================
 ADMIN LOGIN
============================================================
Admin email:     admin@example.com
Admin password:  <generated password>
============================================================
```

If credentials cannot be read, the installer now reports an installation error
instead of silently finishing without a password.

## Apply

Copy the files over your repository, commit and push.

```powershell
git add proxmox/install.sh `
        scripts/mailhub-cli.sh `
        scripts/write-install-info.sh

git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/mailhub-cli.sh
git update-index --chmod=+x scripts/write-install-info.sh

git commit -m "fix(installer): always print admin login credentials"
git push origin main
```
