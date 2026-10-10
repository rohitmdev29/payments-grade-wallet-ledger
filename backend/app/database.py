from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.config import settings

# Use NullPool: every session opens a fresh connection and closes it
# on release. This avoids "Future attached to a different loop" errors
# when tests run across multiple event loops.
#
# For production, this could be swapped for a pooled engine, but for
# this project the correctness guarantee of fresh connections is more
# important than the small performance cost.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
