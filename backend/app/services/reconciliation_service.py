"""
Reconciliation service.

Runs five SQL checks in a single REPEATABLE READ transaction.
The job REPORTS problems but NEVER fixes them — silent mutation hides
root causes.

The job lock (SELECT ... FOR UPDATE NOWAIT on job_locks) is acquired
inside the same transaction as the checks. This avoids SQLAlchemy's
"session already in transaction" error.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.errors import RequestInProgress


CHECKS = {
    "check_1_global_balance": """
        SELECT NULL::BIGINT,
               SUM(CASE WHEN direction = 'DEBIT'  THEN amount ELSE 0 END)::TEXT,
               SUM(CASE WHEN direction = 'CREDIT' THEN amount ELSE 0 END)::TEXT
        FROM ledger_entries
        HAVING SUM(CASE WHEN direction = 'DEBIT'  THEN amount ELSE 0 END)
            <> SUM(CASE WHEN direction = 'CREDIT' THEN amount ELSE 0 END)
    """,
    "check_2_transfer_balance": """
        SELECT transfer_id,
               SUM(CASE WHEN direction = 'DEBIT'  THEN amount ELSE 0 END)::TEXT,
               SUM(CASE WHEN direction = 'CREDIT' THEN amount ELSE 0 END)::TEXT
        FROM ledger_entries
        GROUP BY transfer_id
        HAVING SUM(CASE WHEN direction = 'DEBIT'  THEN amount ELSE 0 END)
            <> SUM(CASE WHEN direction = 'CREDIT' THEN amount ELSE 0 END)
    """,
    "check_3_stored_balance": """
        SELECT a.id,
               a.balance::TEXT,
               COALESCE(SUM(
                   CASE WHEN le.direction = 'CREDIT' THEN le.amount
                        ELSE -le.amount END
               ), 0)::TEXT
        FROM accounts a
        LEFT JOIN ledger_entries le ON le.account_id = a.id
        GROUP BY a.id, a.balance
        HAVING a.balance <> COALESCE(SUM(
            CASE WHEN le.direction = 'CREDIT' THEN le.amount
                 ELSE -le.amount END
        ), 0)
    """,
    "check_4_no_overdraft": """
        SELECT id, '0'::TEXT, balance::TEXT
        FROM accounts
        WHERE type = 'USER' AND balance < 0
    """,
    "check_5_orphans": """
        SELECT t.id, 'has entries', 'no entries'
        FROM transfers t
        LEFT JOIN ledger_entries le ON le.transfer_id = t.id
        WHERE le.id IS NULL
        UNION ALL
        SELECT le.id, 'has transfer', 'no transfer'
        FROM ledger_entries le
        LEFT JOIN transfers t ON t.id = le.transfer_id
        WHERE t.id IS NULL
    """,
}


async def run_reconciliation(
    db: AsyncSession,
    acquire_lock: bool = True,
) -> dict:
    """
    Run all five checks inside one REPEATABLE READ transaction.

    If acquire_lock is True, first try to take the job_locks row with
    FOR UPDATE NOWAIT — if another run already holds it, raise
    RequestInProgress.

    Tests should call with acquire_lock=False to bypass the lock.
    """
    async with db.begin():
        # REPEATABLE READ must be set as the first statement in the transaction.
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))

        if acquire_lock:
            # Take the job lock. NOWAIT means fail immediately if another
            # reconciliation run is already in progress.
            try:
                await db.execute(
                    text(
                        "SELECT * FROM job_locks "
                        "WHERE job_name = 'reconciliation' "
                        "FOR UPDATE NOWAIT"
                    )
                )
            except Exception:
                raise RequestInProgress()

        result = await db.execute(
            text("INSERT INTO reconciliation_runs (status) "
                 "VALUES ('RUNNING') RETURNING id")
        )
        run_id = result.scalar_one()

        problems: list[dict] = []
        for check_name, sql in CHECKS.items():
            result = await db.execute(text(sql))
            for row in result.fetchall():
                problems.append({
                    "check_name": check_name,
                    "entity_id": row[0],
                    "expected": row[1],
                    "actual": row[2],
                })

        for p in problems:
            await db.execute(
                text(
                    "INSERT INTO reconciliation_problems "
                    "(run_id, check_name, entity_id, expected, actual) "
                    "VALUES (:run_id, :check, :eid, :exp, :act)"
                ),
                {
                    "run_id": run_id,
                    "check": p["check_name"],
                    "eid": p["entity_id"],
                    "exp": p["expected"],
                    "act": p["actual"],
                },
            )

        status = "OK" if not problems else "MISMATCH"
        await db.execute(
            text(
                "UPDATE reconciliation_runs "
                "SET ended_at = now(), status = :status, problem_count = :count "
                "WHERE id = :id"
            ),
            {"status": status, "count": len(problems), "id": run_id},
        )

    return {"run_id": run_id, "status": status, "problem_count": len(problems)}