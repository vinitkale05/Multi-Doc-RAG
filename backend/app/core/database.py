import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

Base = declarative_base()

# Resilient database connection support:
# If postgresql is configured or aiosqlite is available, use create_async_engine.
# Otherwise, use standard sqlite3 engine with thread pooling.

_use_native_async = False
try:
    if "postgresql" in settings.DATABASE_URL:
        import asyncpg
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        engine = create_async_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20)
        AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        _use_native_async = True
    elif "aiosqlite" in settings.DATABASE_URL:
        import aiosqlite
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        engine = create_async_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        _use_native_async = True
except ImportError:
    _use_native_async = False

if not _use_native_async:
    # Standard SQLite fallback with WAL mode and concurrency timeout
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
    sync_engine = create_engine(
        sync_url,
        connect_args={"check_same_thread": False, "timeout": 30.0} if "sqlite" in sync_url else {}
    )

    if "sqlite" in sync_url:
        from sqlalchemy import event
        @event.listens_for(sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
            except Exception:
                pass

    SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)

    class AsyncSessionProxy:
        """Async-compatible wrapper around SQLAlchemy sync Session."""
        def __init__(self, session: Session):
            self._session = session

        def add(self, instance):
            self._session.add(instance)

        async def flush(self):
            await asyncio.to_thread(self._session.flush)

        async def commit(self):
            await asyncio.to_thread(self._session.commit)

        async def rollback(self):
            await asyncio.to_thread(self._session.rollback)

        async def close(self):
            await asyncio.to_thread(self._session.close)

        async def execute(self, statement, *args, **kwargs):
            return await asyncio.to_thread(self._session.execute, statement, *args, **kwargs)

        async def delete(self, instance):
            await asyncio.to_thread(self._session.delete, instance)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
            await self.close()

    class AsyncSessionLocalWrapper:
        def __call__(self):
            return AsyncSessionProxy(SyncSessionLocal())

    AsyncSessionLocal = AsyncSessionLocalWrapper()


async def get_db() -> AsyncGenerator:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


async def init_db() -> None:
    if _use_native_async:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        await asyncio.to_thread(Base.metadata.create_all, bind=sync_engine)
