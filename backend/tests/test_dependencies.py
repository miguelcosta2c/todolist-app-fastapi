from contextlib import suppress

import pytest
from pytest_mock import MockerFixture

from app.core.dependencies import get_db


@pytest.mark.asyncio
async def test_get_db_success(mocker: MockerFixture):
    mock_session = mocker.AsyncMock()

    mock_factory = mocker.patch("app.core.dependencies.AsyncSessionLocal")
    mock_factory.return_value.__aenter__.return_value = mock_session

    db_gen = get_db()
    session = await anext(db_gen)

    assert session == mock_session

    with suppress(StopAsyncIteration):
        await anext(db_gen)

    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_exception_rollback(mocker: MockerFixture):
    mock_session = mocker.AsyncMock()
    mock_factory = mocker.patch("app.core.dependencies.AsyncSessionLocal")
    mock_factory.return_value.__aenter__.return_value = mock_session

    db_gen = get_db()
    await anext(db_gen)

    with pytest.raises(RuntimeError, match="Erro de Banco"):
        await db_gen.athrow(RuntimeError("Erro de Banco"))

    mock_session.rollback.assert_called_once()

    mock_session.close.assert_called_once()
