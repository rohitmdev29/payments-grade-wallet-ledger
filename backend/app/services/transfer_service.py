"""
Transfer service — the core money path.

Every transfer is atomic: it either fully happens or leaves no trace.
Correctness relies on three things:
  1. Row-level locks (SELECT ... FOR UPDATE)
  2. Lock ordering (ascending account_id) to prevent deadlocks
  3. Double-entry: SUM(debits) = SUM(credits)

Balance rule:
  - USER accounts must stay non-negative.
  - System accounts (CASH_IN, CASH_OUT, FEE_REVENUE) may go negative,
    because they represent platform liability, not real user money.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.errors import (
    InsufficientFunds,
    AccountNotFound,
    InvalidAmount,
    SelfTransfer,
)


async def execute_transfer(
    db: AsyncSession,
    from_account_id: int,
    to_account_id: int,
    amount: int,
    transfer_type: str = "PEER",
) -> int:
    """
    Execute a transfer between two accounts.

    Runs inside a single transaction. If any step fails, everything rolls back.
    """
    # --- Validate inputs ---
    if amount <= 0:
        raise InvalidAmount()
    if from_account_id == to_account_id:
        raise SelfTransfer()

    # --- Deadlock prevention ---
    # Lock rows in ascending account_id order. If two transfers lock rows
    # in opposite orders, each waits for the other forever.
    #
    # NOTE: `ORDER BY id FOR UPDATE` does NOT guarantee lock order in
    # PostgreSQL — locks are acquired in scan order. The safe pattern is
    # to sort in Python and issue two separate queries.
    first, second = sorted([from_account_id, to_account_id])

    async with db.begin():
        # --- Lock both accounts ---
        await db.execute(
            text("SELECT id, balance FROM accounts WHERE id = :id FOR UPDATE"),
            {"id": first},
        )
        await db.execute(
            text("SELECT id, balance FROM accounts WHERE id = :id FOR UPDATE"),
            {"id": second},
        )

        # --- Read sender's balance AND type while holding the lock ---
        result = await db.execute(
            text("SELECT balance, type FROM accounts WHERE id = :id"),
            {"id": from_account_id},
        )
        row = result.first()
        if row is None:
            raise AccountNotFound(from_account_id)

        balance = row[0]
        account_type = row[1]

        # --- Only user wallets must stay non-negative ---
        # System accounts (CASH_IN, CASH_OUT, FEE_REVENUE) represent
        # platform liability and are allowed to go negative.
        if account_type == "USER" and balance < amount:
            raise InsufficientFunds(from_account_id, balance, amount)

        # --- Insert transfer ---
        result = await db.execute(
            text(
                "INSERT INTO transfers (type, status, amount) "
                "VALUES (:type, 'COMPLETED', :amount) RETURNING id"
            ),
            {"type": transfer_type, "amount": amount},
        )
        transfer_id = result.scalar_one()

        # --- Insert balanced ledger entries (double-entry) ---
        await db.execute(
            text(
                "INSERT INTO ledger_entries "
                "(transfer_id, account_id, direction, amount) "
                "VALUES "
                "(:tid, :from_id, 'DEBIT', :amt), "
                "(:tid, :to_id,   'CREDIT', :amt)"
            ),
            {
                "tid": transfer_id,
                "from_id": from_account_id,
                "to_id": to_account_id,
                "amt": amount,
            },
        )

        # --- Update stored balances ---
        await db.execute(
            text("UPDATE accounts SET balance = balance - :amt WHERE id = :id"),
            {"amt": amount, "id": from_account_id},
        )
        await db.execute(
            text("UPDATE accounts SET balance = balance + :amt WHERE id = :id"),
            {"amt": amount, "id": to_account_id},
        )

        # --- Audit log ---
        await db.execute(
            text(
                "INSERT INTO audit_log (transfer_id, new_status, changed_by) "
                "VALUES (:tid, 'COMPLETED', 'system')"
            ),
            {"tid": transfer_id},
        )

        return transfer_id
    # COMMIT happens here (or ROLLBACK on exception)