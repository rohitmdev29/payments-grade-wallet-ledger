# Payments-Grade Wallet Ledger

> A double-entry ledger backend for a digital wallet — the kind that sits behind every UPI or payments app. **Money here must never appear from nowhere, disappear, or move twice.**

[![CI](https://github.com/rohitmdev29/payments-grade-wallet-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/rohitmdev29/payments-grade-wallet-ledger/actions)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [What It Does](#what-it-does)
- [Stack](#stack)
- [Quick Start](#quick-start)
- [API Examples](#api-examples)
- [Project Structure](#project-structure)
- [Milestones](#milestones)
- [Key Design Decisions](#key-design-decisions)
- [Testing](#testing)
- [Error Shape](#error-shape)
- [Documentation](#documentation)
- [What's Not in Scope](#whats-not-in-scope)
- [Demo Video](#demo-video)
- [License](#license)

---

## Overview

This is a **payments-grade wallet ledger** — a backend system that:

- Lets users open wallets, top them up, send money to each other, and withdraw.
- Records every rupee twice (as a debit and a matching credit) so books always balance.
- Stays correct when a hundred people spend from the same wallet at the same moment.
- Charges only once, even when a client retries a payment after a timeout.
- Checks its own books every night and reports anything that doesn't add up.
- Holds suspicious transfers for review and answers plain-English questions about a user's statement.

Built to demonstrate **correctness fundamentals**: double-entry accounting, concurrency control, idempotency, reconciliation, and LLM safety.

---

## What It Does

### Core Features

| Feature | Description |
|---|---|
| **Double-entry ledger** | Every transfer writes 2+ ledger lines that cancel out; `SUM(debits) = SUM(credits)` |
| **Append-only ledger** | Entries can be inserted but never updated or deleted — enforced via triggers |
| **Concurrent-safe transfers** | `SELECT ... FOR UPDATE` in ascending `account_id` order to prevent deadlocks |
| **Idempotent APIs** | `Idempotency-Key` header + `UNIQUE(user_id, key)` + SHA-256 request hashing |
| **Nightly reconciliation** | 5 SQL checks in a `REPEATABLE READ` transaction; reports but never auto-fixes |
| **Fraud rules** | Thresholds in DB; held transfers move no money until released |
| **Statement Q&A** | LLM parses questions to JSON, our code runs SQL — LLM never writes SQL |
| **Audit log** | Every status change tracked with who and when |
| **Cursor pagination** | `(created_at, id)` based; compared against `OFFSET` with `EXPLAIN ANALYZE` |

### System Accounts

The platform has 3 system accounts (no user owner):

- **CASH_IN** — represents money coming from outside (top-ups)
- **CASH_OUT** — represents money going outside (withdrawals)
- **FEE_REVENUE** — represents platform's revenue

These can go **negative** because they represent platform liability, not real user money.

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11+ | Type hints, async support |
| Framework | FastAPI | Async, automatic OpenAPI docs |
| Database | PostgreSQL 15+ | Row-level locks, isolation levels, triggers |
| DB Access | SQLAlchemy Core (`text()`) | Connection pooling **without** hiding SQL |
| Driver | asyncpg | Native async Postgres driver |
| Container | Docker + Docker Compose | One-command startup |
| Testing | Pytest + pytest-asyncio | Async test support |
| CI | GitHub Actions | Automated test runs |
| LLM | OpenAI / Mock | Provider abstraction for tests |

**What we deliberately did NOT use:**

- ❌ SQLAlchemy ORM — hides the money path (brief requires it to be visible)
- ❌ Redis — not required; balance reads are already indexed and fast
- ❌ Alembic — raw SQL migrations are clearer for this project
- ❌ Kafka / RabbitMQ — no async messaging needed
- ❌ MongoDB — PostgreSQL handles everything

---

## Quick Start

### Prerequisites

- Docker Desktop (or Docker + Docker Compose)
- That's it

### Run the Project

```bash
git clone https://github.com/rohitmdev29/payments-grade-wallet-ledger.git
cd payments-grade-wallet-ledger
cp .env.example .env
docker compose up
