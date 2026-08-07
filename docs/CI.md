# Continuous Integration

Commit 002F Part 5A splits CI into four gates.

## Backend / Python

Runs on Python 3.12 and executes:

```bash
./scripts/ci/backend-unit.sh
```

This performs Python compilation, Ruff and the backend pytest suite.

## Frontend / TypeScript

Runs on Node.js 22:

```bash
./scripts/ci/frontend-build.sh
```

The script uses `npm ci` when a lockfile exists, otherwise `npm install`, then
runs the production frontend build.

## Installer / Release Gate

Runs:

```bash
./scripts/ci/release-gate.sh
```

It validates shell syntax, existing static repository checks, release
invariants, critical files and the 002F release manifest.

## Docker Integration

Only starts after the three fast gates pass. It starts the real Compose stack
and executes the existing API, migration, authentication, frontend, email,
worker, rule and storage smoke tests.

## Recommended GitHub branch protection

Protect `main` and require the status check:

```text
CI Success
```

Also enable:

- Require a pull request before merging.
- Require branches to be up to date before merging.
- Do not allow bypassing the required CI check for normal development.

This means the LXC update agent can safely follow `main`: code cannot normally
reach `main` unless all CI gates are green.
