from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    decode_token,
    hash_password,
    verify_password,
)
from app.models.token import UserToken
from app.models.user import User
from app.schemas.auth import UserCreate


async def create_user(db: AsyncSession, data: UserCreate) -> User | None:
    """
    Cria um usuário.
    Se o usuário (email ou username) já existir, retorna None.
    Caso contrário, cria e retorna o novo User.

    Campos = username, email, password
    """
    query = select(User).where(
        (User.email == data.email) | (User.username == data.username)
    )
    existing_user = await db.scalar(query)

    if existing_user is not None:
        return None

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await db.scalar(select(User).where(User.email == email))

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def get_refresh_token_in_db(
    refresh_token: str, db: AsyncSession
) -> UserToken | None:
    return await db.scalar(
        select(UserToken).where(UserToken.refresh_token == refresh_token)
    )


class InvalidTokenError(Exception):
    def __init__(self, msg: str) -> None:
        self.mensagem = msg
        super().__init__(self.mensagem)


async def validate_refresh_token(
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

        try:
            db_refresh_token.is_revoked = True
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        msg = "Token expirado ou invalido, faca login novamente"
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
            msg = "Token revogado"
            raise InvalidTokenError(msg)

        return db_refresh_token
