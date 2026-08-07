# Backup & Restore

Part 5B adds administrator-controlled backup and restore through the web UI.

## Storage location

Application backups created from the UI are stored inside the LXC:

```text
/var/backups/mailhub/
```

Each backup is a separate directory such as:

```text
mailhub-20260807T210000Z
```

A restore automatically creates an additional safety backup first:

```text
pre-restore-20260807T211500Z
```

## Backup contents

Each normal backup contains:

```text
database.dump
attachments.tgz
routed.tgz
env.backup
SHA256SUMS
created-at.txt
git-commit.txt
```

`env.backup` is required because encrypted email passwords and OAuth credentials
depend on the matching `APP_SECRET_KEY`.

## Restore safety

The web UI requires the administrator to type:

```text
RESTORE <backup-id>
```

exactly before a restore request is accepted.

The LXC agent validates the backup identifier and confines restores to
`/var/backups/mailhub`.

Before the selected backup is restored, the agent creates a new pre-restore
safety backup.

During restore:

1. backup checksums are verified;
2. backend, worker and frontend are stopped;
3. PostgreSQL is restored;
4. attachment and routed volumes are restored;
5. the backup application environment is restored;
6. current PostgreSQL credentials, Compose project name and exposed ports are
   preserved;
7. storage permissions are repaired;
8. the application stack is rebuilt and started.

## Web UI

Open:

```text
Administration → Backup & Restore
```

or:

```text
/admin/backups
```

The page shows backup date, total size, database size, attachment size, routed
file size and whether the backup was checksum-verified.

## Important

The backup files are local to the LXC. For disaster recovery from LXC/host
failure, copy `/var/backups/mailhub` to storage outside the LXC or include it in
your Proxmox backup strategy.
