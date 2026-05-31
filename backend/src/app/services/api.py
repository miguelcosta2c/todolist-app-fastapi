import uuid
from datetime import datetime

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.settings import TIMEZONE, settings
from app.exc import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from app.models import User, UserToken
from app.schemas import UserCreate, UserRequestPassword, UserUpdate
from app.services import auth
from app.services.user import UserDBService

# ================================
# Api Utils
# ================================


async def validate_refresh_token(
    db: AsyncSession, refresh_token: str | None, response: Response
) -> UserToken:
    """
    Faz a mesma coisa que "app.auth.services.validate_refresh_token", porem gera os
    erros para a api.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao esta logado.",
        )

    try:
        db_refresh_token = await auth.db_validate_refresh_token(refresh_token, db)
    except InvalidTokenError as err:
        # Deletando o token invalido
        delete_cookie_refresh_token(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=err.mensagem
        ) from err

    return db_refresh_token


async def generate_tokens(
    db: AsyncSession, user_uuid: uuid.UUID, response: Response
) -> dict[str, str]:
    access_token = create_access_token(user_uuid)
    refresh_token = await create_refresh_token(user_uuid, db)

    create_cookie_refresh_token(response, refresh_token)

    return {"access_token": access_token, "token_type": "bearer"}


def create_cookie_refresh_token(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Protege contra XSS
        secure=settings.IS_SECURE,  # Apenas via HTTPS
        samesite="lax",  # Protege contra CSRF
        max_age=60 * 60 * 24 * 7,
    )


def delete_cookie_refresh_token(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.IS_SECURE,
        samesite="lax",
    )


# ================================
# Api Auth Services
# ================================


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    try:
        user = await UserDBService(db).create_user(data)
    except UserAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        ) from err
    return user


async def login_user(
    db: AsyncSession, username: str, password: str, response: Response
) -> dict[str, str]:
    try:
        user = await auth.authenticate_user(
            db,
            username,
            password,
        )
    except InvalidCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from err

    user.last_login_at = datetime.now(TIMEZONE)
    await db.commit()

    return await generate_tokens(db, user.uuid_, response)


async def generate_new_tokens_user(
    db: AsyncSession, user_refresh_token: str | None, response: Response
) -> dict[str, str]:
    refresh_token = await validate_refresh_token(db, user_refresh_token, response)
    await auth.revoke_refresh_token_in_db(db, refresh_token.refresh_token)
    return await generate_tokens(db, refresh_token.user_uuid, response)


async def logout_user(
    db: AsyncSession, user_refresh_token: str | None, response: Response
) -> dict[str, str]:
    refresh_token = await validate_refresh_token(db, user_refresh_token, response)
    await auth.revoke_refresh_token_in_db(db, refresh_token.refresh_token)
    delete_cookie_refresh_token(response)
    return {"message": "Logout realizado com sucesso"}


# ================================
# Api User Services
# ================================


async def patch_current_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not verify_password(update_data.pop("password"), user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha incorreta"
        )

    return await UserDBService(db).update_user(user, update_data)


async def delete_current_user(
    db: AsyncSession, user: User, data: UserRequestPassword
) -> None:
    try:
        await UserDBService(db).delete_user_with_password(user, data)
    except InvalidCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Senha invalida"
        ) from err
