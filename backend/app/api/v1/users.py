from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("", status_code=201, response_model=UserResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user."""
    result = await db.execute(
        text(
            "INSERT INTO users (name, email, phone) "
            "VALUES (:name, :email, :phone) "
            "RETURNING id, name, email, kyc_status"
        ),
        {"name": body.name, "email": body.email, "phone": body.phone},
    )
    row = result.first()
    await db.commit()
    return {"id": row[0], "name": row[1], "email": row[2], "kyc_status": row[3]}
