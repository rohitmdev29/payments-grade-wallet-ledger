from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.reconciliation_service import run_reconciliation

router = APIRouter()


@router.post("/reconciliation/run")
async def manual_reconciliation(db: AsyncSession = Depends(get_db)):
    """Manually trigger a reconciliation run."""
    return await run_reconciliation(db)
