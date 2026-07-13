from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings


class DBDependency:
    def __init__(self) -> None:
        self._engine = create_async_engine(
            url=settings.db_settings.db_url, echo=settings.db_settings.db_echo
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autocommit=False,
        )

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            yield session


# Синхронный URL для Celery (заменяем postgresql+asyncpg на postgresql+psycopg2)
SYNC_DATABASE_URL = settings.db_settings.db_url.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_sync_session_factory():
    return SyncSessionLocal
