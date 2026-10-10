from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.wallet import WalletCreate, WalletResponse, BalanceResponse
from app.utils.errors import AccountNotFound

router = APIRouter()


@router.post("", status_code=201, response_model=WalletResponse)
async def create_wallet(body: WalletCreate, db: AsyncSession = Depends(get_db)):
    """Create a wallet for a user. Also creates the underlying account."""
    async with db.begin():
        result = await db.execute(
            text(
                "INSERT INTO wallets (user_id, name) "
                "VALUES (:uid, :name) "
                "RETURNING id, user_id, name, currency"
            ),
            {"uid": body.user_id, "name": body.name},
        )
        wallet_id, user_id, name, currency = result.first()

        result = await db.execute(
            text(
                "INSERT INTO accounts (wallet_id, type, balance, currency) "
                "VALUES (:wid, 'USER', 0, :cur) RETURNING id"
            ),
            {"wid": wallet_id, "cur": currency},
        )
        account_id = result.scalar_one()

    return {
        "id": wallet_id,
        "user_id": user_id,
        "account_id": account_id,
        "name": name,
        "currency": currency,
    }


@router.get("/{wallet_id}/balance", response_model=BalanceResponse)
async def get_balance(wallet_id: int, db: AsyncSession = Depends(get_db)):
    """Return the balance for a wallet's underlying account."""
    result = await db.execute(
        text(
            "SELECT a.id, a.balance, a.currency "
            "FROM accounts a "
            "JOIN wallets w ON w.id = a.wallet_id "
            "WHERE w.id = :wid"
        ),
        {"wid": wallet_id},
    )
    row = result.first()
    if row is None:
        raise AccountNotFound(wallet_id)
    return {"account_id": row[0], "balance_paise": row[1], "currency": row[2]}
