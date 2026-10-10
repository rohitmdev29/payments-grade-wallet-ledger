"""Idempotency tests."""
import uuid
import pytest


@pytest.mark.asyncio
async def test_same_request_5_times(client):
    key = str(uuid.uuid4())
    body = {"type": "PEER", "from_account_id": 1, "to_account_id": 2, "amount": 1000}
    responses = []
    for _ in range(5):
        r = await client.post(
            "/api/v1/transfers",
            json=body,
            headers={"Idempotency-Key": key},
        )
        responses.append(r.json())
    assert all(r == responses[0] for r in responses)


@pytest.mark.asyncio
async def test_same_key_different_body(client):
    key = str(uuid.uuid4())
    r1 = await client.post(
        "/api/v1/transfers",
        json={"type": "PEER", "from_account_id": 1, "to_account_id": 2, "amount": 1000},
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 201

    r2 = await client.post(
        "/api/v1/transfers",
        json={"type": "PEER", "from_account_id": 1, "to_account_id": 2, "amount": 9999},
        headers={"Idempotency-Key": key},
    )
    assert r2.status_code == 422
