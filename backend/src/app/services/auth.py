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


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(
        select(User).where(
            User.email == email,
            User.status == UserStatus.ACTIVE,
        )
    )

    if not user:
        # Usuario nao existe
        raise InvalidCredentialsError

    if not verify_password(password, user.password_hash):
        # Senha incorreta
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
        msg = "Espera-se que o refresh token esteja no banco de dados"
        raise InvalidTokenError(msg)

    token.is_revoked = True

    await db.commit()


async def db_validate_refresh_token(
    refresh_token: str,
    db: AsyncSession,
) -> UserToken:
    """
    Faz verificações para confirmar se o "refresh token" é valido.

    Esta função verifica se ele existe no banco
    verifica se ele é invalido ou está expirado
    verifica se o tipo do token é o tipo certo
    e se o token já está revogado.

    retorna a instância do refresh token no banco de dados.
    """
    # ============================
    # Verificando o token bruto
    # ============================

    db_refresh_token = await get_refresh_token_in_db(refresh_token=refresh_token, db=db)

    # Verificando se o token esta no banco de dados
    if db_refresh_token is None:
        msg = "Espera-se que o refresh token esteja no banco de dados"
        raise InvalidTokenError(msg)

    # Vendo se o token enviado ja e invalido ou ja foi expirado
    try:
        payload = decode_token(refresh_token)

    except (ExpiredSignatureError, JWTError) as err:
        # Verificando se o token esta expirado ou e invalido

        db_refresh_token.is_revoked = True
        await db.commit()

        msg = "Token expirado ou invalido"
        raise InvalidTokenError(msg) from err

    else:
        # Vendo se o tipo do token enviado e valido
        if payload.get("type") != "refresh":
            msg = 'Espera-se que o token seja do tipo "refresh"'
            raise InvalidTokenError(msg)

        refresh_token_user_uuid = payload.get("sub")

        if not refresh_token_user_uuid:
            msg = "Token invalido"
            raise InvalidTokenError(msg)

        # Vendo se o token ja esta revogado
        if db_refresh_token.is_revoked:
            msg = "Token revogado"
            raise InvalidTokenError(msg)

        if db_refresh_token.user_uuid != refresh_token_user_uuid:
            msg = "Token invalido"
            raise InvalidTokenError(msg)

        return db_refresh_token
