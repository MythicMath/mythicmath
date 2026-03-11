import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://mythic:mythic@db:5432/mythicmath",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
