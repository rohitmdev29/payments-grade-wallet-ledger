"""
Nightly reconciliation worker.

Calls run_reconciliation(), which handles the job lock internally
via SELECT ... FOR UPDATE NOWAIT.
"""
import asyncio

from app.database import AsyncSessionLocal
from app.services.reconciliation_service import run_reconciliation
from app.utils.errors import RequestInProgress


async def main():
    async with AsyncSessionLocal() as db:
        try:
            result = await run_reconciliation(db, acquire_lock=True)
            print(f"Reconciliation finished: {result}")
        except RequestInProgress:
            print("Another reconciliation run is in progress. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())