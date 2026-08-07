# Operations Dashboard – Part 5C

Part 5C expands the administrator Operations Dashboard with runtime resource
information and operational history.

## New system metrics

The backend reports:

- CPU count
- 1, 5 and 15 minute load averages
- RAM total / available / used percentage
- disk total / free / used percentage
- uptime

No additional Python dependency is required. Linux `/proc`, `os.getloadavg()`
and `shutil.disk_usage()` are used.

## Backup summary

The Operations Dashboard reads the same maintenance control files introduced in
Part 5B and shows:

- number of backups
- latest backup identifier
- latest backup date
- latest backup size
- total backup size
- current backup/restore agent state

The detailed Backup & Restore page remains available under:

```text
/admin/backups
```

## Recent syncs

The dashboard now shows the latest synchronization runs together with:

- account name
- email address
- status
- messages created
- attachments created
- error details
- start time

## Degraded state

The Operations Dashboard now also becomes degraded when:

- RAM usage is 95% or higher
- disk usage is 95% or higher
- the backup/restore agent is in an error state

This is in addition to the existing health, routing, storage and worker checks.
