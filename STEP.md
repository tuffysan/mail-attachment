# Mail Attachment Hub v1.0.0

Steps 011 and 012 are merged into this production release.

Included:
- complete email ingestion, rule and storage platforms
- administration statistics and audit logs
- API key foundation
- backup and restore
- diagnostics and update scripts
- production Caddy/HTTPS profile
- Docker one-line installer
- Proxmox LXC one-line installer
- release automation and upgrade-safe migrations
- operational and troubleshooting documentation

Validation:
```bash
make init
make check
make test
make up
make migration-smoke
make auth-smoke
make frontend-smoke
make email-account-smoke
make mail-engine-smoke
make rule-engine-smoke
make storage-platform-smoke
make doctor
```
