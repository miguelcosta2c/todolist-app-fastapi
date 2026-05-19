from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.core.settings import TIMEZONE
from app.models import User
from tests.conftest import MockDBTimeCallable

user_informations = {
    "username": "John Doe",
    "email": "johndoe@email.com",
    "password_hash": hash_password("123456789"),
}


def test_user_model():
    user = User(**user_informations)

    assert user.username == user_informations["username"]
    assert user.email == user_informations["email"]
    assert user.password_hash == user_informations["password_hash"]


@pytest.mark.asyncio
async def test_user_model_in_database(session: AsyncSession):
    user = User(**user_informations)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    result = await session.scalar(
        select(User).where(
            (User.username == user_informations["username"])
            & (User.email == user_informations["email"])
            & (User.password_hash == user_informations["password_hash"])
        )
    )

    assert result is not None


@pytest.mark.asyncio
async def test_user_model_created_and_updated_at(
    session: AsyncSession, mock_db_time: MockDBTimeCallable
):
    time = datetime(2026, 1, 1, tzinfo=TIMEZONE)
    with mock_db_time(model=User, time=time):
        user = User(**user_informations)

        session.add(user)
        await session.commit()
        await session.refresh(user)

    assert user.created_at == datetime(2026, 1, 1)  # noqa: DTZ001
    assert user.updated_at == datetime(2026, 1, 1)  # noqa: DTZ001
