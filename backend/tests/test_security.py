from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.settings import TIMEZONE


def test_hash_password():
    hard_password = "123456789"  # noqa: S105

    hashed_password = hash_password(hard_password)

    assert verify_password("123456789", hashed_password)


FROZEN_TIME = datetime(2026, 5, 13, 13, 0, 0, tzinfo=TIMEZONE)


@freeze_time(FROZEN_TIME)
def test_access_token(monkeypatch: pytest.MonkeyPatch):
    token_expire_minutes = 5
    monkeypatch.setattr(
        "app.core.security.ACCESS_TOKEN_EXPIRE_MINUTES", token_expire_minutes
    )

    user_id = 1
    token = create_access_token(user_id)

    expire_time = int((FROZEN_TIME + timedelta(minutes=5)).timestamp())
    assert decode_token(token) == {"sub": str(user_id), "exp": expire_time}


def test_decode_token_error():
    token_invalido = decode_token("token_invalido")
    assert token_invalido is None
