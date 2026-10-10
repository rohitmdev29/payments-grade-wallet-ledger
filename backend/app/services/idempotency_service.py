"""
Idempotency service.

The client sends an Idempotency-Key header with every POST. The server
hashes the request body and inserts a row in idempotency_keys with a
UNIQUE(user_id, key) constraint. If two identical requests arrive at the
same instant, the database lets only one insert succeed.
"""
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.errors import IdempotencyConflict, RequestInProgress
from app.utils.hashing import hash_request_body


async def check_or_create_idempotency(
    db: AsyncSession,
    user_id: int,
    key: str,
    request_body: dict,
) -> dict | None:
    """
    Returns:
        - None          : new key (or FAILED key), caller should proceed
        - saved response: key already completed, replay

    Raises:
        - IdempotencyConflict : same key, different body
        - RequestInProgress   : same key still running
    """
    body_hash = hash_request_body(request_body)

    # Try to insert. UNIQUE(user_id, key) does the hard part.
    try:
        await db.execute(
            text(
                "INSERT INTO idempotency_keys "
                "(user_id, key, request_hash, status) "
                "VALUES (:uid, :key, :hash, 'STARTED')"
            ),
            {"uid": user_id, "key": key, "hash": body_hash},
        )
        await db.commit()
        return None
    except Exception:
        # Unique violation - key exists. Roll back and fetch.
        await db.rollback()

    result = await db.execute(
        text(
            "SELECT request_hash, response_code, response_body, status "
            "FROM idempotency_keys "
            "WHERE user_id = :uid AND key = :key"
        ),
        {"uid": user_id, "key": key},
    )
    row = result.first()
    if row is None:
        raise

    existing_hash, _response_code, response_body, status = row

    # Same key, different body -> reject with 422
    if existing_hash != body_hash:
        raise IdempotencyConflict()

    # Same key, same body, COMPLETED -> replay saved response
    if status == "COMPLETED":
        return response_body

    # Same key, same body, FAILED -> delete old row and allow retry
    if status == "FAILED":
        await db.execute(
            text(
                "DELETE FROM idempotency_keys "
                "WHERE user_id = :uid AND key = :key"
            ),
            {"uid": user_id, "key": key},
        )
        await db.commit()
        return None

    # Same key, same body, STARTED -> another request is still running
    raise RequestInProgress()


async def save_response(
    db: AsyncSession,
    user_id: int,
    key: str,
    response_code: int,
    response_body: dict,
) -> None:
    """Save the response for a completed idempotent request."""
    await db.execute(
        text(
            "UPDATE idempotency_keys "
            "SET response_code = :code, "
            "    response_body = :body, "
            "    status = 'COMPLETED' "
            "WHERE user_id = :uid AND key = :key"
        ),
        {
            "code": response_code,
            "body": json.dumps(response_body),
            "uid": user_id,
            "key": key,
        },
    )
    await db.commit()


async def mark_failed(
    db: AsyncSession,
    user_id: int,
    key: str,
) -> None:
    """
    Mark an idempotency key as FAILED.

    Called when a transfer throws an exception. This unsticks the key
    so the client can retry the same request without getting a 409.
    """
    await db.execute(
        text(
            "UPDATE idempotency_keys "
            "SET status = 'FAILED' "
            "WHERE user_id = :uid AND key = :key"
        ),
        {"uid": user_id, "key": key},
    )
    await db.commit()
