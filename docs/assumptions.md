# Assumptions

This document lists all assumptions made while building the Payments-Grade Wallet Ledger project. Any reviewer should read these to understand the boundaries of what was built.

For the full requirements, see [requirements.md](requirements.md).

---

## 1. Money & Currency

- All amounts are stored in **paise** (integers), never rupees or floats.
- Currency is **INR only**. No multi-currency support.
- `1 Rupee = 100 paise`.
- Maximum amount per transfer is bounded by `BIGINT` range (9,223,372,036,854,775,807 paise ≈ ₹92 quadrillion).
- No rounding rules are needed since all amounts are integers.

---

## 2. Accounts

### User Accounts

- A user account belongs to exactly one wallet.
- A wallet belongs to exactly one user.
- A user can have **many wallets** (e.g., main + savings).
- User accounts **cannot go negative** — enforced via `CHECK` constraint.

### System Accounts

- System accounts belong to the platform, not to any user.
- There are exactly **3 system accounts**:
  - `CASH_IN` — represents money coming from outside (top-ups)
  - `CASH_OUT` — represents money going outside (withdrawals)
  - `FEE_REVENUE` — represents platform's revenue
- System accounts **can go negative** — they represent platform liability.
- System accounts are created at migration time (3 rows seeded).
- System accounts use `wallet_id = NULL`.

### External World

- The "external world" (banks, NPCI, other platforms) is **not modeled**.
- `CASH_IN` and `CASH_OUT` are placeholders for external money movement.
- No real bank integration exists.
- `CASH_IN = -₹10,00,000` means "platform has taken ₹10 lakh from outside" — not that the platform physically has that cash.

---

## 3. Transfers

- Every money movement is a transfer.
- Transfer types: `TOP_UP`, `PEER`, `WITHDRAWAL`, `FEE`, `REVERSAL`.
- Transfer statuses: `PENDING`, `COMPLETED`, `HELD`, `FAILED`, `REVERSED`.
- Every transfer writes **at least 2 ledger entries** (double-entry).
- A transfer's debits must equal its credits — enforced at the application layer and verified nightly.
- Transfers are **immutable** once completed. Mistakes are fixed with reversal transfers.
- Self-transfers (same account to same account) are **rejected**.
- Amount must be **positive** (`> 0`).

---

## 4. Ledger

- Ledger entries are **append-only** — never updated, never deleted.
- Enforced via **PostgreSQL triggers** that raise an exception on `UPDATE` or `DELETE`.
- Ledger entry amounts are always **positive**; the direction (`DEBIT` or `CREDIT`) is stored separately.
- Every entry references exactly one account and one transfer.
- No ledger entry exists without a transfer (no orphans).
- No transfer exists without ledger entries (verified nightly).

---

## 5. Idempotency

- The **client** generates the idempotency key (a UUID v4).
- The key is sent as an `Idempotency-Key` HTTP header.
- The server computes a **SHA-256 hash** of the request body.
- A `UNIQUE(user_id, key)` constraint prevents duplicate inserts.
- Same key + same hash → replay saved response.
- Same key + different hash → `422 IDEMPOTENCY_CONFLICT`.
- Keys are **scoped per user** (same key from different users is allowed).
- Assumption: client retries use the **same key**.
- Assumption: keys older than 24 hours can be deleted (optional cleanup).

---

## 6. Concurrency

- Transfers run at **READ COMMITTED** isolation (PostgreSQL default).
- Row locks via `SELECT ... FOR UPDATE` are sufficient for correctness.
- **Deadlock prevention:** Account IDs are sorted in Python, then locked in ascending order via **two separate queries**.
- **Assumption:** `ORDER BY` in SQL does **not** guarantee lock order — this was verified.
- Serializable isolation is **not used** (throughput cost not justified).
- Stampede test assumes PostgreSQL's default lock timeout (1 second for deadlock detection).

---

## 7. Reconciliation

- Runs **nightly** (via cron or framework scheduler).
- Uses `REPEATABLE READ` to get a consistent snapshot.
- **Only one run at a time** — enforced via `job_locks` table with `FOR UPDATE NOWAIT`.
- **Reports problems but never auto-fixes them.** This is deliberate.
- Five checks are run:
  1. Global debit = credit
  2. Per-transfer balance
  3. Stored balance = computed balance
  4. No overdrafts
  5. No orphans
- Assumption: a "problem" is any row returned by the check query.
- Assumption: reconciliation runs when traffic is low (midnight).
- Assumption: full table scans are acceptable for a nightly job with 1M rows.

---

## 8. Fraud Detection

- Thresholds are stored in the `risk_rules` table, **not in code**.
- Rules run **inside the transfer transaction, before commit**.
- A held transfer's money **does not move** until an admin releases it.
- Assumption: admin release flow is a simple status update (no complex workflow).
- Assumption: "velocity" rules use the last 1 hour by default.

---

## 9. LLM

- LLM is used **only for two purposes**:
  1. Explaining fraud flags (nightly job)
  2. Parsing statement questions into JSON (real-time)
- **The rules make every decision; the LLM only explains and answers.**
- **The LLM never writes SQL.** Our code always runs its own parameterized queries.
- LLM output is treated as **untrusted data**, always validated before use.
- Supported LLM providers: OpenAI (real) and a mock (for tests).
- **Tests run without network or API key** — using the mock provider.
- Assumption: LLM returns valid JSON when instructed.
- Assumption: user notes are **data, not instructions** (prompt injection handled).
- Assumption: supported question types are limited to **4 kinds**:
  1. Total sent to a person in a date range
  2. Total received in a date range
  3. Largest transfer in a date range
  4. Number of transfers in a date range

---

## 10. API

- Every `POST` requires an `Idempotency-Key` header.
- Missing or invalid key → `400`.
- Amounts are always integers in paise.
- Pagination uses `ORDER BY created_at DESC, id DESC`.
- Cursor-based pagination is a **bonus**, not required.
- Error responses use a **single shape** everywhere:
  ```json
  {"code": "...", "message": "...", "request_id": "..."}
