"""
Stampede test.

Puts 500 rupees in one user wallet and fires 50 concurrent 20-rupee
transfers out of it.

Passes only if:
  - exactly 25 transfers succeed (50 * 20 = 1000, but only 500 available)
  - the wallet ends at 0 and is never negative
  - total debits equal total credits

Run 5 times in a row. A race that fails once is still a bug.

NOTE: Accounts 1/2/3 are system accounts. Use accounts 4 and 5 which
are USER accounts — those enforce the non-negative balance rule.
"""
import asyncio
import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.services.transfer_service import execute_transfer


CONCURRENCY = 50
AMOUNT = 2000          # 20 rupees each
START_BALANCE = 50000  # 500 rupees total
EXPECTED_SUCCESSES = 25  # 50 * 20 = 1000; only 500 available -> 25 succeed
RUNS = 5


@pytest.mark.asyncio
async def test_stampede():
    for run in range(RUNS):
        async with AsyncSessionLocal() as db:
            await db.execute(text(
                "TRUNCATE ledger_entries, transfers RESTART IDENTITY CASCADE"
            ))
            await db.execute(text("UPDATE accounts SET balance = :b WHERE id = 4"),
                             {"b": START_BALANCE})
            await db.execute(text("UPDATE accounts SET balance = 0 WHERE id = 5"))
            await db.commit()

        async def one_transfer():
            async with AsyncSessionLocal() as db:
                try:
                    await execute_transfer(db, 4, 5, AMOUNT)
                    return True
                except Exception:
                    return False

        results = await asyncio.gather(*[one_transfer() for _ in range(CONCURRENCY)])
        successes = sum(results)

        async with AsyncSessionLocal() as db:
            balance = (await db.execute(
                text("SELECT balance FROM accounts WHERE id = 4")
            )).scalar_one()
            debits = (await db.execute(
                text("SELECT COALESCE(SUM(amount),0) FROM ledger_entries "
                     "WHERE direction='DEBIT'")
            )).scalar_one()
            credits = (await db.execute(
                text("SELECT COALESCE(SUM(amount),0) FROM ledger_entries "
                     "WHERE direction='CREDIT'")
            )).scalar_one()

        assert successes == EXPECTED_SUCCESSES, \
            f"Run {run}: expected {EXPECTED_SUCCESSES}, got {successes}"
        assert balance == 0, f"Run {run}: balance {balance} != 0"
        assert debits == credits, f"Run {run}: debits {debits} != credits {credits}"
