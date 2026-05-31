from collections.abc import AsyncGenerator, Generator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Any, Protocol

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import Mapper
from testcontainers.postgres import PostgresContainer

from app.core.dependencies import get_db
from app.core.settings import TIMEZONE
from app.db import Base
from app.main import app


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer("postgres:17-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer) -> AsyncEngine:
    url = postgres_container.get_connection_url(driver="asyncpg")
    return create_async_engine(url, echo=False)


@pytest.fixture(scope="session")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture(scope="session", autouse=True)
async def setup_db(engine: AsyncEngine) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db(engine: AsyncEngine) -> AsyncGenerator[None]:
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


@contextmanager
def _mock_db_time(
    *, model: type[Base], time: datetime = datetime(2024, 1, 1, tzinfo=TIMEZONE)
) -> Generator[datetime]:
    def fake_time_hook[T: Any](
        mapper: Mapper[T], connection: Connection, target: T
    ) -> None:
        if hasattr(target, "created_at"):
            target.created_at = time
        if hasattr(target, "updated_at"):
            target.updated_at = time

    event.listen(model, "before_insert", fake_time_hook)
    try:
        yield time
    finally:
        event.remove(model, "before_insert", fake_time_hook)


class MockDBTimeCallable(Protocol):
    def __call__(
        self,
        *,
        model: type[Base],
        time: datetime = datetime(2024, 1, 1, tzinfo=TIMEZONE),
    ) -> AbstractContextManager[datetime]: ...


@pytest.fixture
def mock_db_time() -> MockDBTimeCallable:
    return _mock_db_time


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _get_test_db() -> AsyncGenerator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
