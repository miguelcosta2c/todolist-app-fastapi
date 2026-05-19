from collections.abc import AsyncGenerator, Generator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Any, Protocol

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Mapper
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.settings import TIMEZONE
from app.db import Base
from app.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def session():
    """
    Provides a clean, isolated SQLAlchemy AsyncSession for a test case.

    This fixture handles the full lifecycle of the test database:
    1. Creates all database tables defined in the metadata.
    2. Yields an active AsyncSession to the test.
    3. Drops all tables after the test completes to ensure isolation.

    Yields:
        AsyncSession: An active asynchronous session connected to the test database.

    Note:
        This fixture uses `run_sync` to perform DDL operations (create/drop),
        as SQLAlchemy's metadata operations are traditionally synchronous.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
    """
    Provides a context manager to mock timestamps for SQLAlchemy models.

    This fixture is essential for testing logic that relies on specific
    creation or update times, ensuring that database-level timestamps
    are deterministic.

    Returns:
        MockDBTimeCallable: A callable that returns a context manager
            targeting a specific SQLAlchemy model.

    Example:
        def test_created_at_logic(client, mock_db_time):
            fixed_now = datetime(2025, 1, 1, tzinfo=UTC)
            with mock_db_time(model=User, time=fixed_now):
                # Any User inserted here will have created_at = fixed_now
                repo.create_user(name="John Doe")
    """
    return _mock_db_time


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """
    Creates an asynchronous FastAPI AsyncClient with an overridden database dependency.

    This fixture allows functional tests to interact with the API asynchronously
    while ensuring all database operations are performed within the scope of
    the provided `session` fixture.

    Args:
        session (AsyncSession): The database session to be used for
            the duration of the test.

    Yields:
        AsyncClient: An instance of the httpx AsyncClient with
            dependency overrides applied, suitable for testing async endpoints.

    Cleanup:
        Clears the `app.dependency_overrides` dictionary after the
        test execution to ensure a clean state for other fixtures.
    """

    async def _get_test_db() -> AsyncGenerator[AsyncSession]:
        yield session

    # Inject the test session into the FastAPI dependency system
    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Remove overrides to avoid leaking state between tests
    app.dependency_overrides.clear()
