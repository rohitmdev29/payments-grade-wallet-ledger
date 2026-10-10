"""
Statement Q&A.

Four-step flow:
  1. LLM parses the question into JSON.
  2. We validate the JSON.
  3. We run OUR OWN parameterized query, scoped to caller's accounts.
  4. Return the number + transfer IDs.

The LLM NEVER writes SQL.
"""
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import LLMProvider
from app.llm.mock_provider import MockLLMProvider


SUPPORTED = [
    "Total sent to a person in a date range",
    "Total received in a date range",
    "Largest transfer in a date range",
    "Number of transfers in a date range",
]


def _parse_date(s: str):
    """Convert 'YYYY-MM-DD' string to Python date object for asyncpg."""
    return datetime.strptime(s, "%Y-%m-%d").date()


async def answer_statement_question(
    db: AsyncSession,
    user_id: int,
    question: str,
    llm: LLMProvider | None = None,
) -> dict:
    llm = llm or MockLLMProvider()

    # Step 1: LLM parses
    parsed = await llm.parse_statement_question(question)

    # Step 2: Validate
    qtype = parsed.get("type")
    if qtype not in (1, 2, 3, 4):
        return {
            "error": "I can only answer these four kinds of question.",
            "supported": SUPPORTED,
        }

    # Step 3: Our own parameterized query, scoped to caller.
    # Dates are passed as Python date objects so asyncpg accepts them.
    base = """
        SELECT t.id, le.amount
        FROM transfers t
        JOIN ledger_entries le ON le.transfer_id = t.id
        JOIN accounts a ON a.id = le.account_id
        WHERE a.wallet_id IN (
            SELECT id FROM wallets WHERE user_id = :uid
        )
          AND t.created_at BETWEEN :from_ts AND :to_ts
    """

    params = {
        "uid": user_id,
        "from_ts": _parse_date(parsed["from"]),
        "to_ts": _parse_date(parsed["to"]),
    }

    if qtype == 1:
        sql = base + " AND le.direction = 'DEBIT'"
    elif qtype == 2:
        sql = base + " AND le.direction = 'CREDIT'"
    elif qtype == 3:
        sql = base + " ORDER BY le.amount DESC LIMIT 1"
    else:
        sql = """
            SELECT COUNT(*), NULL
            FROM transfers t
            JOIN ledger_entries le ON le.transfer_id = t.id
            JOIN accounts a ON a.id = le.account_id
            WHERE a.wallet_id IN (
                SELECT id FROM wallets WHERE user_id = :uid
            )
              AND t.created_at BETWEEN :from_ts AND :to_ts
        """

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    # Step 4: Return the answer
    if qtype == 4:
        return {"count": rows[0][0], "transfer_ids": []}

    total = sum(r[1] for r in rows)
    return {"total_paise": total, "transfer_ids": [r[0] for r in rows]}
