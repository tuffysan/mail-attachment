# Architecture

## Sprint 0 baseline

Mail Attachment Hub will use independently deployable services:

- `api`: FastAPI application, added in Step 003
- `web`: React application, added in Step 005
- `worker`: background jobs, added in a later sprint
- `postgres`: durable relational data
- `redis`: queues, locks and short-lived state

Only PostgreSQL and Redis are introduced in Step 002. Both run on an internal Docker network. Development ports bind to loopback only.

Persistent data is stored in named Docker volumes. Application services will connect by Compose DNS names (`postgres` and `redis`) rather than host ports.
