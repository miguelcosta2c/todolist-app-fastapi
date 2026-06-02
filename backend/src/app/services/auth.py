import logging
import uuid

from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    decode_token,
    verify_password,
)
from app.exc import InvalidCredentialsError, InvalidTokenError
from app.models import User, UserToken
from app.models.user import UserStatus

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(
        select(User).where(
            User.email == email,
            User.status == UserStatus.ACTIVE,
        )
    )

    if not user:
        logger.debug("Tentativa de autenticação com e-mail inexistente: %s", email)
        raise InvalidCredentialsError

    if not verify_password(password, user.password_hash):
        logger.debug("Tentativa de autenticação com senha incorreta para: %s", email)
        raise InvalidCredentialsError

    return user


async def get_refresh_token_in_db(
    db: AsyncSession, refresh_token: str
) -> UserToken | None:
    return await db.scalar(
        select(UserToken).where(UserToken.refresh_token == refresh_token)
    )


async def revoke_refresh_token_in_db(db: AsyncSession, refresh_token: str) -> None:
    token = await get_refresh_token_in_db(db, refresh_token)

    if token is None:
        msg = "O refresh token informado não foi encontrado na base de dados."
        raise InvalidTokenError(msg)

    token.is_revoked = True

    await db.commit()


async def db_validate_refresh_token(
    refresh_token: str,
    db: AsyncSession,
) -> UserToken:
    db_refresh_token = await get_refresh_token_in_db(refresh_token=refresh_token, db=db)

    if db_refresh_token is None:
        msg = "O refresh token informado não foi encontrado na base de dados."
        raise InvalidTokenError(msg)

    try:
        payload = decode_token(refresh_token)

    except (ExpiredSignatureError, JWTError) as err:
        db_refresh_token.is_revoked = True
        await db.commit()

        msg = "O refresh token informado expirou ou é inválido."
        raise InvalidTokenError(msg) from err

    else:
        if payload.get("type") != "refresh":
            msg = "O token informado não é do tipo refresh."
            raise InvalidTokenError(msg)

        refresh_token_user_uuid = payload.get("sub")

        if not refresh_token_user_uuid:
            msg = "O refresh token informado é inválido."
            raise InvalidTokenError(msg)

        refresh_token_user_uuid = uuid.UUID(refresh_token_user_uuid)

        if db_refresh_token.is_revoked:
            msg = "O refresh token informado já foi revogado."
            raise InvalidTokenError(msg)

        if db_refresh_token.user_uuid != refresh_token_user_uuid:
            msg = "O refresh token informado é inválido."
            raise InvalidTokenError(msg)

        return db_refresh_token
