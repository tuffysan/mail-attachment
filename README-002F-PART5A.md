# Commit 002F – Part 5A
## Automated Test Suite + GitHub Actions CI

Apply on top of `mail-attachment-hub-commit-002F-final.zip`.

### New CI gates

GitHub Actions is split into four clear gates:

1. **Backend / Python**
   - Python 3.12
   - install backend test dependencies
   - compile source/tests
   - pytest

2. **Frontend / TypeScript**
   - Node.js 22
   - `npm ci` when a lockfile exists, otherwise `npm install`
   - production `npm run build`

3. **Installer / Release Gate**
   - shell syntax
   - `make check`
   - `scripts/release-self-test.sh`
   - critical release file checks
   - release manifest parsing

4. **Docker Integration**
   - runs only after the three fast gates pass
   - Compose startup
   - API smoke
   - migration smoke and migration cycle
   - auth
   - frontend
   - email account API
   - worker/mail engine
   - rule engine
   - storage platform

A final GitHub job named **CI Success** only succeeds when all gates are green.

### Existing CI bug fixed

The previous `tests/clean-tree-check.sh` was still written for an early
"Step 006" prototype and rejected the current production Proxmox installer.

Part 5A replaces it with a 002F-aware repository check.

The Makefile also executes repository test scripts through `bash`, avoiding
false `Permission denied` errors when ZIP extraction or Windows loses executable
bits.

### Pull Request Guard

A lightweight PR workflow checks that generated credentials/secrets are not
committed and that required CI helper scripts are executable.

### Dependabot

Weekly dependency checks are enabled for:

- GitHub Actions
- backend Python dependencies
- frontend npm dependencies

### Local verification performed

```text
new CI shell scripts: bash -n             PASS
make check                                PASS
tsc -p frontend/tsconfig.json --noEmit    PASS
focused 002F backend tests                PASS (from final 002F validation)
release-self-test                         PASS (from final 002F validation)
```

The full Docker integration gate must run on GitHub or another Docker-capable
host.

### Apply

```powershell
git add .github `
        scripts/ci `
        tests/clean-tree-check.sh `
        Makefile `
        docs/CI.md

git update-index --chmod=+x scripts/ci/backend-unit.sh
git update-index --chmod=+x scripts/ci/frontend-build.sh
git update-index --chmod=+x scripts/ci/release-gate.sh
git update-index --chmod=+x scripts/ci/docker-integration.sh
git update-index --chmod=+x tests/clean-tree-check.sh

git commit -m "ci: add automated release gates"
git push origin main
```

Then protect `main` in GitHub and require the status check:

```text
CI Success
```
