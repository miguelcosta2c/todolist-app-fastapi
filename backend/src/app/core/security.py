import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import TIMEZONE, settings
from app.models.token import UserToken

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_uuid: uuid.UUID) -> str:
    expire = datetime.now(tz=TIMEZONE) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_uuid), "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(user_uuid: uuid.UUID, session: AsyncSession) -> str:
    now = datetime.now(tz=TIMEZONE)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_uuid), "exp": expire, "type": "refresh"}

    refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    refresh_token_db = UserToken(
        user_uuid=user_uuid,
        refresh_token=refresh_token,
        expires_at=expire,
        created_at=now,
    )

    session.add(refresh_token_db)
    await session.commit()

    return refresh_token


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(str(token), SECRET_KEY, algorithms=[ALGORITHM])
