-- Seed the three platform system accounts.
-- These belong to the platform, not to any user.
INSERT INTO accounts (wallet_id, type, balance) VALUES
    (NULL, 'CASH_IN', 0),
    (NULL, 'CASH_OUT', 0),
    (NULL, 'FEE_REVENUE', 0);

-- Seed the reconciliation job lock row.
INSERT INTO job_locks (job_name) VALUES ('reconciliation');