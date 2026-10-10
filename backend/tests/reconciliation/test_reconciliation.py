"""
Reconciliation detects corruptions.

Seeds a clean transfer, then corrupts one ledger entry directly in the
database and verifies the reconciliation job reports the mismatch.

Since the ledger_entries table has a trigger that blocks UPDATE and
DELETE, we temporarily disable the trigger to simulate the corruption.
"""
import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.services.reconciliation_service import run_reconciliation


@pytest.mark.asyncio
async def test_reconciliation_detects_corruptions():
    # ---- Setup: clean transfer with balanced entries ----
    async with AsyncSessionLocal() as db:
        await db.execute(text(
            "TRUNCATE reconciliation_problems, reconciliation_runs, "
            "ledger_entries, transfers RESTART IDENTITY CASCADE"
        ))
        await db.execute(text("UPDATE accounts SET balance = 100000 WHERE id = 4"))
        await db.execute(text("UPDATE accounts SET balance = 50000 WHERE id = 5"))
        await db.commit()

        await db.execute(text(
            "INSERT INTO transfers (type, status, amount) "
            "VALUES ('PEER', 'COMPLETED', 500)"
        ))
        await db.execute(text(
            "INSERT INTO ledger_entries "
            "(transfer_id, account_id, direction, amount) "
            "VALUES (1, 4, 'DEBIT', 500), (1, 5, 'CREDIT', 500)"
        ))
        await db.commit()

    # ---- Corrupt one entry (requires temporarily disabling the trigger) ----
    async with AsyncSessionLocal() as db:
        await db.execute(text(
            "ALTER TABLE ledger_entries DISABLE TRIGGER ledger_entries_no_update"
        ))
        await db.execute(text("UPDATE ledger_entries SET amount = 999 WHERE id = 1"))
        await db.execute(text(
            "ALTER TABLE ledger_entries ENABLE TRIGGER ledger_entries_no_update"
        ))
        await db.commit()

    # ---- Run reconciliation ----
    async with AsyncSessionLocal() as db:
        result = await run_reconciliation(db, acquire_lock=False)

    assert result["status"] == "MISMATCH"
    assert result["problem_count"] >= 1
