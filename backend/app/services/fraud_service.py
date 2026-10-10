"""
Fraud rules.

Rules run inside the transfer transaction before commit.
Thresholds are stored in the risk_rules table, NOT in code.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_fraud_rules(
    db: AsyncSession,
    from_account_id: int,
    amount: int,
) -> list[dict]:
    """Return a list of fired rules (possibly empty)."""
    fired: list[dict] = []

    # Rule 1: large amount
    result = await db.execute(
        text(
            "SELECT name, action FROM risk_rules "
            "WHERE name = 'large_amount' AND :amt >= threshold"
        ),
        {"amt": amount},
    )
    for row in result.fetchall():
        fired.append({"rule": row[0], "action": row[1]})

    # Rule 2: velocity — too many debits in the last hour
    result = await db.execute(
        text(
            "SELECT COUNT(*) FROM ledger_entries "
            "WHERE account_id = :aid "
            "  AND direction = 'DEBIT' "
            "  AND created_at > now() - interval '1 hour'"
        ),
        {"aid": from_account_id},
    )
    if result.scalar_one() >= 10:
        fired.append({"rule": "high_velocity", "action": "HOLD"})

    return fired
