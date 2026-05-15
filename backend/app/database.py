from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# pool_pre_ping: Neon free-tier compute suspends after ~5 min idle, killing any
#   open connections. Without pre-ping, the next query hands out a dead conn
#   and throws asyncpg InterfaceError: connection is closed.
# pool_recycle: rotate connections every 5 min so we don't even reach the
#   suspend boundary on a busy worker.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
