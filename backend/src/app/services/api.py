import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.settings import TIMEZONE, settings
from app.exc import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from app.models import User, UserToken
from app.schemas import (
    RefreshTokensListFilter,
    UserCreate,
    UserListFilters,
    UserRequestPassword,
    UserUpdate,
)
from app.services import auth, token
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


async def list_all_users(db: AsyncSession, filters: UserListFilters) -> dict[str, Any]:
    users = await UserDBService(db).get_all_users(filters)
    total = await db.scalar(select(func.count(User.id)))
    total = 0 if total is None else total
    return {
        "result": users,
        "total": total,
        "offset": filters.offset,
        "limit": filters.limit,
    }


async def get_user_by_uuid(db: AsyncSession, user_uuid: uuid.UUID) -> User:
    return await _get_user_by_uuid(UserDBService(db), user_uuid)


async def _get_user_by_uuid(
    user_service: type[UserDBService], user_uuid: uuid.UUID
) -> User:
    user = await user_service.get_user_by_uuid(user_uuid, only_active=False)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O usuario com o id informado nao existe",
        )
    return user


async def patch_user_by_uuid(
    db: AsyncSession, user_uuid: uuid.UUID, data: UserUpdate
) -> User:
    user_service = UserDBService(db)
    user = await _get_user_by_uuid(user_service, user_uuid)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    return await user_service.update_user(user, update_data)


async def delete_user_by_uuid(db: AsyncSession, user_uuid: uuid.UUID) -> None:
    user_service = UserDBService(db)
    user = await _get_user_by_uuid(user_service, user_uuid)
    await user_service.delete_user(user)


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


# ================================
# Api Token Services
# ================================


async def list_all_refresh_tokens(
    db: AsyncSession, filters: RefreshTokensListFilter
) -> dict[str, Any]:
    tokens = await token.list_all_user_tokens(db, filters)
    total = await db.scalar(select(func.count(UserToken.id)))
    total = 0 if total is None else total
    return {
        "result": tokens,
        "total": total,
        "offset": filters.offset,
        "limit": filters.limit,
    }


async def delete_token_by_id(db: AsyncSession, token_id: int) -> None:
    db_token = await token.get_token_by_id(db, token_id)
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token nao encontrado"
        )
    await token.delete_token_by_id(db, token_id)
    await db.commit()
