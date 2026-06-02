import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.settings import TIMEZONE, settings
from app.exc import InvalidCredentialsError, InvalidTokenError, UserAlreadyExistsError
from app.models import Todo, User, UserToken
from app.schemas import (
    RefreshTokensListFilter,
    TodoCreate,
    TodoListFilters,
    TodoUpdate,
    UserCreate,
    UserListFilters,
    UserRequestPassword,
    UserUpdate,
)
from app.services import auth, token
from app.services.todo import TodoDBService
from app.services.user import UserDBService

logger = logging.getLogger(__name__)

# ================================
# Api Utils
# ================================


async def validate_refresh_token(
    db: AsyncSession, refresh_token: str | None, response: Response
) -> UserToken:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O usuário não está autenticado.",
        )

    try:
        db_refresh_token = await auth.db_validate_refresh_token(refresh_token, db)
    except InvalidTokenError as err:
        delete_cookie_refresh_token(response)
        logger.warning("Refresh token inválido: %s", err.mensagem)
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
        httponly=True,
        secure=settings.IS_SECURE,
        samesite="lax",
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
        logger.warning("Tentativa de cadastro com e-mail já existente: %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O usuário informado já existe na base de dados.",
        ) from err
    logger.info("Usuário cadastrado com sucesso: %s", user.uuid_)
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
        logger.warning(
            "Tentativa de login com credenciais inválidas para: %s", username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="As credenciais fornecidas são inválidas.",
        ) from err

    user.last_login_at = datetime.now(TIMEZONE)
    await db.commit()

    logger.info("Login realizado com sucesso: %s", user.uuid_)
    return await generate_tokens(db, user.uuid_, response)


async def generate_new_tokens_user(
    db: AsyncSession, user_refresh_token: str | None, response: Response
) -> dict[str, str]:
    refresh_token = await validate_refresh_token(db, user_refresh_token, response)
    await auth.revoke_refresh_token_in_db(db, refresh_token.refresh_token)
    logger.info("Tokens renovados para o usuário: %s", refresh_token.user_uuid)
    return await generate_tokens(db, refresh_token.user_uuid, response)


async def logout_user(
    db: AsyncSession, user_refresh_token: str | None, response: Response
) -> dict[str, str]:
    refresh_token = await validate_refresh_token(db, user_refresh_token, response)
    await auth.revoke_refresh_token_in_db(db, refresh_token.refresh_token)
    delete_cookie_refresh_token(response)
    logger.info("Logout realizado para o usuário: %s", refresh_token.user_uuid)
    return {"message": "Logout realizado com sucesso."}


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
        logger.warning("Usuário não encontrado para o UUID: %s", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O usuário solicitado não foi encontrado.",
        )
    return user


async def patch_user_by_uuid(
    db: AsyncSession, user_uuid: uuid.UUID, data: UserUpdate
) -> User:
    user_service = UserDBService(db)
    user = await _get_user_by_uuid(user_service, user_uuid)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    updated_user = await user_service.update_user(user, update_data)
    logger.info("Administrador atualizou o usuário: %s", user_uuid)
    return updated_user


async def delete_user_by_uuid(db: AsyncSession, user_uuid: uuid.UUID) -> None:
    user_service = UserDBService(db)
    user = await _get_user_by_uuid(user_service, user_uuid)
    await user_service.delete_user(user)
    logger.info("Administrador excluiu o usuário: %s", user_uuid)


async def patch_current_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not verify_password(update_data.pop("password"), user.password_hash):
        logger.warning(
            "Tentativa de atualização de perfil com senha incorreta: %s", user.uuid_
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A senha fornecida está incorreta.",
        )

    updated_user = await UserDBService(db).update_user(user, update_data)
    logger.info("Perfil atualizado pelo usuário: %s", user.uuid_)
    return updated_user


async def delete_current_user(
    db: AsyncSession, user: User, data: UserRequestPassword
) -> None:
    try:
        await UserDBService(db).delete_user_with_password(user, data)
    except InvalidCredentialsError as err:
        logger.warning(
            "Tentativa de exclusão de conta com senha incorreta: %s", user.uuid_
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha fornecida é inválida.",
        ) from err
    logger.info("Conta excluída pelo usuário: %s", user.uuid_)


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
        logger.warning("Token não encontrado para exclusão: %s", token_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O token solicitado não foi encontrado.",
        )
    await token.delete_token_by_id(db, token_id)
    await db.commit()
    logger.info("Administrador excluiu o token: %s", token_id)


# ================================
# Api Todo Services
# ================================


async def list_user_todos(
    db: AsyncSession, user_uuid: uuid.UUID, filters: TodoListFilters
) -> dict[str, Any]:
    todos = await TodoDBService(db).get_todos_by_user(user_uuid, filters)
    total = await db.scalar(
        select(func.count(Todo.id)).where(Todo.user_uuid == user_uuid)
    )
    total = 0 if total is None else total
    return {
        "result": todos,
        "total": total,
        "offset": filters.offset,
        "limit": filters.limit,
    }


async def create_user_todo(
    db: AsyncSession, user_uuid: uuid.UUID, data: TodoCreate
) -> Todo:
    todo = await TodoDBService(db).create_todo(data, user_uuid)
    logger.info("Tarefa criada pelo usuário %s: %s", user_uuid, todo.uuid_)
    return todo


async def _get_user_todo(
    db: AsyncSession, user_uuid: uuid.UUID, todo_uuid: uuid.UUID
) -> Todo:
    todo = await TodoDBService(db).get_todo_by_uuid(todo_uuid, user_uuid)
    if todo is None:
        logger.warning(
            "Tarefa não encontrada para o usuário %s: %s", user_uuid, todo_uuid
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A tarefa solicitada não foi encontrada.",
        )
    return todo


async def get_user_todo(
    db: AsyncSession, user_uuid: uuid.UUID, todo_uuid: uuid.UUID
) -> Todo:
    return await _get_user_todo(db, user_uuid, todo_uuid)


async def patch_user_todo(
    db: AsyncSession,
    user_uuid: uuid.UUID,
    todo_uuid: uuid.UUID,
    data: TodoUpdate,
) -> Todo:
    todo = await _get_user_todo(db, user_uuid, todo_uuid)
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    updated_todo = await TodoDBService(db).update_todo(todo, update_data)
    logger.info("Tarefa atualizada pelo usuário %s: %s", user_uuid, todo_uuid)
    return updated_todo


async def delete_user_todo(
    db: AsyncSession, user_uuid: uuid.UUID, todo_uuid: uuid.UUID
) -> None:
    todo = await _get_user_todo(db, user_uuid, todo_uuid)
    await TodoDBService(db).delete_todo(todo)
    logger.info("Tarefa excluída pelo usuário %s: %s", user_uuid, todo_uuid)


# ================================
# Admin Todo
# ================================


async def list_all_todos(db: AsyncSession, filters: TodoListFilters) -> dict[str, Any]:
    todos = await TodoDBService(db).get_all_todos(filters)
    total = await db.scalar(select(func.count(Todo.id)))
    total = 0 if total is None else total
    return {
        "result": todos,
        "total": total,
        "offset": filters.offset,
        "limit": filters.limit,
    }


async def _get_todo_by_uuid_admin(db: AsyncSession, todo_uuid: uuid.UUID) -> Todo:
    todo = await TodoDBService(db).get_todo_by_uuid_admin(todo_uuid)
    if todo is None:
        logger.warning("Administrador: tarefa não encontrada: %s", todo_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A tarefa solicitada não foi encontrada.",
        )
    return todo


async def admin_get_todo_by_uuid(db: AsyncSession, todo_uuid: uuid.UUID) -> Todo:
    return await _get_todo_by_uuid_admin(db, todo_uuid)


async def admin_delete_todo_by_uuid(db: AsyncSession, todo_uuid: uuid.UUID) -> None:
    todo = await _get_todo_by_uuid_admin(db, todo_uuid)
    await TodoDBService(db).delete_todo(todo)
    logger.info("Administrador excluiu a tarefa: %s", todo_uuid)
