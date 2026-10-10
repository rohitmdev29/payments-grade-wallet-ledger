"""
Seed script: 1,000 users, 2,000 wallets, 100,000 transfers.
Run inside the API container:
    docker compose exec api python scripts/seed.py
"""
import asyncio
import random
from sqlalchemy import text

from app.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("Seeding users...")
        await db.execute(text("""
            INSERT INTO users (name, email, phone, kyc_status)
            SELECT 'User ' || i,
                   'user' || i || '@example.com',
                   '+91999' || LPAD(i::text, 7, '0'),
                   'VERIFIED'
            FROM generate_series(1, 1000) i
        """))
        await db.commit()

        print("Seeding wallets and accounts...")
        await db.execute(text(
            "INSERT INTO wallets (user_id, name) SELECT id, 'Main Wallet' FROM users"
        ))
        await db.execute(text(
            "INSERT INTO wallets (user_id, name) SELECT id, 'Savings Wallet' FROM users"
        ))
        await db.execute(text(
            "INSERT INTO accounts (wallet_id, type, balance) "
            "SELECT id, 'USER', 100000 FROM wallets"
        ))
        await db.commit()

        print("Seeding transfers...")
        for _ in range(100000):
            await db.execute(
                text("INSERT INTO transfers (type, status, amount) "
                     "VALUES ('TOP_UP', 'COMPLETED', :a)"),
                {"a": random.randint(100, 1000)},
            )
        await db.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
