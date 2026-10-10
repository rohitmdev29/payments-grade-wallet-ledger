from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transfer import TransferCreate, TransferResponse
from app.services.transfer_service import execute_transfer
from app.services.idempotency_service import (
    check_or_create_idempotency,
    save_response,
    mark_failed,                            # ← NEW: import added
)
from app.api.deps import require_idempotency_key

router = APIRouter()

# For now assume the authenticated user is id=1.
DEFAULT_USER_ID = 1


@router.post("", status_code=201, response_model=TransferResponse)
async def create_transfer(
    body: TransferCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(require_idempotency_key),
):
    """
    Create a transfer.

    Idempotency:
      - same key + same body      -> replay saved response
      - same key + different body -> 422
      - key stuck in STARTED      -> 409
      - key FAILED                -> allowed to retry
    """
    # Step 1: Idempotency check
    # If this key was already used, either:
    #   - Return the saved response (if COMPLETED)
    #   - Raise IdempotencyConflict (if different body)
    #   - Raise RequestInProgress (if still STARTED)
    #   - Allow retry (if FAILED — the previous attempt errored)
    existing = await check_or_create_idempotency(
        db,
        user_id=DEFAULT_USER_ID,
        key=idempotency_key,
        request_body=body.model_dump(),
    )
    if existing is not None:
        return existing

    # Step 2: Run the transfer
    # Wrapped in try/except so that if the transfer fails, we can mark
    # the idempotency key as FAILED. Without this, a failed transfer
    # would leave the key stuck in 'STARTED' status forever, and every
    # future retry with the same key would return 409 REQUEST_IN_PROGRESS.
    try:                                    # ← NEW: try block
        transfer_id = await execute_transfer(
            db,
            from_account_id=body.from_account_id,
            to_account_id=body.to_account_id,
            amount=body.amount,
            transfer_type=body.type,
        )
    except Exception:                       # ← NEW: except block
        # Mark the key as FAILED so the client can safely retry.
        await mark_failed(db, DEFAULT_USER_ID, idempotency_key)
        raise                               # ← Re-raise so the client
                                            #   sees the real error.

    response = {"transfer_id": transfer_id, "status": "COMPLETED"}

    # Step 3: Save response for replay
    await save_response(db, DEFAULT_USER_ID, idempotency_key, 201, response)
    return response