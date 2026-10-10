"""
Nightly fraud explainer.

For each flagged transfer today, send the rule + last 10 transfers to
an LLM. Save the explanation + label to risk_flags.
"""
import asyncio
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.config import settings
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider


def _get_llm():
    if settings.llm_provider == "openai":
        return OpenAIProvider()
    return MockLLMProvider()


async def main():
    llm = _get_llm()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT t.id, le.account_id "
                "FROM transfers t "
                "JOIN ledger_entries le ON le.transfer_id = t.id "
                "WHERE t.status = 'HELD' "
                "  AND t.created_at > now() - interval '1 day'"
            )
        )
        for transfer_id, account_id in result.fetchall():
            recent_result = await db.execute(
                text(
                    "SELECT amount, direction, created_at "
                    "FROM ledger_entries "
                    "WHERE account_id = :aid "
                    "ORDER BY created_at DESC LIMIT 10"
                ),
                {"aid": account_id},
            )
            recent = [
                {"amount": r[0], "direction": r[1], "created_at": str(r[2])}
                for r in recent_result.fetchall()
            ]
            explained = await llm.explain_flag("large_amount", recent)
            await db.execute(
                text(
                    "INSERT INTO risk_flags "
                    "(transfer_id, rule_name, label, explanation) "
                    "VALUES (:tid, 'large_amount', :label, :exp)"
                ),
                {
                    "tid": transfer_id,
                    "label": explained["label"],
                    "exp": explained["explanation"],
                },
            )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
