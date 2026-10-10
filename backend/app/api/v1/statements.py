from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.statement import (
    StatementResponse,
    StatementQuestion,
    StatementAnswer,          # OLD: still imported but unused now
)
from app.services.statement_qa_service import answer_statement_question

router = APIRouter()


@router.get("/wallets/{wallet_id}/statement", response_model=StatementResponse)
async def get_statement(
    wallet_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Paginated statement, newest first."""
    result = await db.execute(
        text(
            "SELECT le.id, le.transfer_id, le.direction, le.amount, le.created_at "
            "FROM ledger_entries le "
            "JOIN accounts a ON a.id = le.account_id "
            "WHERE a.wallet_id = :wid "
            "ORDER BY le.created_at DESC, le.id DESC "
            "LIMIT :limit"
        ),
        {"wid": wallet_id, "limit": limit},
    )
    entries = [
        {
            "id": r[0],
            "transfer_id": r[1],
            "direction": r[2],
            "amount_paise": r[3],
            "created_at": r[4].isoformat(),
        }
        for r in result.fetchall()
    ]
    return {"entries": entries, "next_cursor": None}


# ---- OLD VERSION (commented out) ----
# The old version used response_model=StatementAnswer, which forced FastAPI
# to drop any field not defined in the model (e.g., "error" and "supported").
# That caused null values to appear for unsupported questions.
#
# @router.post("/users/{user_id}/statement/ask", response_model=StatementAnswer)
# async def ask_statement(
#     user_id: int,
#     body: StatementQuestion,
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Plain-English statement Q&A.
#
#     The LLM parses the question into JSON. Our code runs the SQL.
#     The LLM never writes SQL.
#     """
#     return await answer_statement_question(db, user_id, body.question)


# ---- NEW VERSION ----
@router.post("/users/{user_id}/statement/ask")
async def ask_statement(
    user_id: int,
    body: StatementQuestion,
    db: AsyncSession = Depends(get_db),
):
    """
    Plain-English statement Q&A.

    The LLM parses the question into JSON. Our code runs the SQL.
    The LLM never writes SQL.

    Response shape depends on the question type:
      - Supported   : {"total_paise": <int>, "transfer_ids": [<int>]}
      - Count       : {"count": <int>, "transfer_ids": []}
      - Unsupported : {"error": "...", "supported": [...]}

    NOTE: response_model is intentionally omitted. The service returns
    different shapes for different outcomes, so a fixed Pydantic model
    would drop fields like "error" and "supported".
    """
    return await answer_statement_question(db, user_id, body.question)