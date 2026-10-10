# Payments-Grade Wallet Ledger

A double-entry ledger backend for a digital wallet.

## Quick Start

    cp .env.example .env
    docker compose up

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL 15+
- SQLAlchemy Core (text() — no ORM)
- asyncpg
- Docker Compose
- Pytest
- GitHub Actions

## Milestones

1. Schema — double-entry, constraints, triggers
2. Concurrency — row locks, deadlock prevention, stampede test
3. Idempotency — client keys, UNIQUE constraint, SHA-256
4. Reconciliation — 5 checks, job lock, EXPLAIN ANALYZE
5. Fraud + LLM — rules in DB, LLM parses only

## License

MIT
