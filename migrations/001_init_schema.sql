-- Payments-Grade Wallet Ledger — Initial Schema
-- Milestone 1: Double-entry schema with DB-level constraints.

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id           BIGSERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    phone        TEXT NOT NULL UNIQUE,
    kyc_status   TEXT NOT NULL DEFAULT 'PENDING'
                 CHECK (kyc_status IN ('PENDING','VERIFIED','REJECTED')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- WALLETS
-- ============================================================
CREATE TABLE wallets (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users(id),
    name         TEXT NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- ACCOUNTS
-- Holds both user wallets and system accounts.
-- Only user wallets must stay non-negative.
-- ============================================================
CREATE TABLE accounts (
    id           BIGSERIAL PRIMARY KEY,
    wallet_id    BIGINT REFERENCES wallets(id),
    type         TEXT NOT NULL
                 CHECK (type IN ('USER','CASH_IN','CASH_OUT','FEE_REVENUE')),
    balance      BIGINT NOT NULL DEFAULT 0,
    currency     TEXT NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT account_wallet_consistency CHECK (
        (type = 'USER' AND wallet_id IS NOT NULL) OR
        (type <> 'USER' AND wallet_id IS NULL)
    ),
    CONSTRAINT balance_non_negative CHECK (type <> 'USER' OR balance >= 0)
);

-- ============================================================
-- TRANSFERS
-- ============================================================
CREATE TABLE transfers (
    id            BIGSERIAL PRIMARY KEY,
    type          TEXT NOT NULL
                  CHECK (type IN ('TOP_UP','PEER','WITHDRAWAL','FEE','REVERSAL')),
    status        TEXT NOT NULL DEFAULT 'PENDING'
                  CHECK (status IN ('PENDING','COMPLETED','HELD','FAILED','REVERSED')),
    amount        BIGINT NOT NULL CHECK (amount > 0),
    note          TEXT,
    reversal_of   BIGINT REFERENCES transfers(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- LEDGER ENTRIES
-- Append-only: never updated, never deleted.
-- ============================================================
CREATE TABLE ledger_entries (
    id           BIGSERIAL PRIMARY KEY,
    transfer_id  BIGINT NOT NULL REFERENCES transfers(id),
    account_id   BIGINT NOT NULL REFERENCES accounts(id),
    direction    TEXT NOT NULL CHECK (direction IN ('DEBIT','CREDIT')),
    amount       BIGINT NOT NULL CHECK (amount > 0),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_ledger_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'ledger_entries is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ledger_entries_no_update
BEFORE UPDATE ON ledger_entries
FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();

CREATE TRIGGER ledger_entries_no_delete
BEFORE DELETE ON ledger_entries
FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();

-- ============================================================
-- IDEMPOTENCY KEYS
-- ============================================================
CREATE TABLE idempotency_keys (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT NOT NULL REFERENCES users(id),
    key            UUID NOT NULL,
    request_hash   TEXT NOT NULL,
    response_code  INT,
    response_body  JSONB,
    status         TEXT NOT NULL DEFAULT 'STARTED'
                   CHECK (status IN ('STARTED','COMPLETED','FAILED')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT idempotency_user_key_unique UNIQUE (user_id, key)
);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id           BIGSERIAL PRIMARY KEY,
    transfer_id  BIGINT NOT NULL REFERENCES transfers(id),
    old_status   TEXT,
    new_status   TEXT NOT NULL,
    changed_by   TEXT NOT NULL,
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- RISK RULES + FLAGS
-- ============================================================
CREATE TABLE risk_rules (
    id           BIGSERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    threshold    BIGINT NOT NULL,
    action       TEXT NOT NULL CHECK (action IN ('HOLD','FLAG')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE risk_flags (
    id           BIGSERIAL PRIMARY KEY,
    transfer_id  BIGINT NOT NULL REFERENCES transfers(id),
    rule_name    TEXT NOT NULL,
    label        TEXT NOT NULL CHECK (label IN ('likely_ok','review','likely_fraud')),
    explanation  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- RECONCILIATION
-- ============================================================
CREATE TABLE job_locks (
    job_name     TEXT PRIMARY KEY,
    locked_at    TIMESTAMPTZ
);

CREATE TABLE reconciliation_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at      TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'RUNNING'
                  CHECK (status IN ('RUNNING','OK','MISMATCH','FAILED')),
    problem_count INT NOT NULL DEFAULT 0
);

CREATE TABLE reconciliation_problems (
    id           BIGSERIAL PRIMARY KEY,
    run_id       BIGINT NOT NULL REFERENCES reconciliation_runs(id),
    check_name   TEXT NOT NULL,
    entity_id    BIGINT,
    expected     TEXT,
    actual       TEXT
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_ledger_account_created
    ON ledger_entries (account_id, created_at DESC, id DESC);

CREATE INDEX idx_transfers_created
    ON transfers (created_at DESC, id DESC);

CREATE INDEX idx_ledger_transfer
    ON ledger_entries (transfer_id);

CREATE INDEX idx_idempotency_user_key
    ON idempotency_keys (user_id, key);

CREATE INDEX idx_ledger_account_amount
    ON ledger_entries (account_id, amount);