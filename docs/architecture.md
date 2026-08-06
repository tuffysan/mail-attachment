# Architecture

## Current Sprint 0 architecture

- **FastAPI backend:** HTTP API, health probes and lifecycle management.
- **PostgreSQL 16:** durable relational database.
- **SQLAlchemy 2 async:** application database access and transaction sessions.
- **Alembic:** ordered, reviewable and reversible database schema migrations.
- **Redis 7:** future job queue and short-lived coordination data.
- **Docker Compose:** local and CI runtime orchestration.

The backend applies pending migrations before starting Uvicorn. Readiness checks use the shared SQLAlchemy engine and Redis client. Application code obtains one asynchronous SQLAlchemy session per request through a FastAPI dependency.

Future steps will introduce authentication, the frontend, email connectors, rule execution, storage adapters and background workers without replacing this database foundation.
