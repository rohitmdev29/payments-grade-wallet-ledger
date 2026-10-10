from fastapi import Header, HTTPException
import uuid


async def require_idempotency_key(
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> str:
    """Validate the Idempotency-Key header is a UUID."""
    try:
        uuid.UUID(idempotency_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Idempotency-Key")
    return idempotency_key
