import uuid
from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.dependencies import (
    SessionDB,
    TokensFilter,
    TodosFilter,
    UsersFilter,
    get_current_superuser,
)
from app.schemas import (
    RefreshTokensList,
    TodoList,
    TodoResponse,
    UserList,
    UserSchema,
    UserUpdate,
)
from app.services import api

router = APIRouter(
    prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_superuser)]
)


# ==============================================
# DB User Routes
# ==============================================


@router.get("/users", response_model=UserList)
async def list_users(db: SessionDB, filters: UsersFilter) -> Any:
    return await api.list_all_users(db, filters)


@router.get("/users/{user_uuid}", response_model=UserSchema)
async def get_user(db: SessionDB, user_uuid: uuid.UUID) -> Any:
    return await api.get_user_by_uuid(db, user_uuid)


@router.patch("/users/{user_uuid}", response_model=UserSchema)
async def patch_user(
    db: SessionDB,
    user_uuid: uuid.UUID,
    data: UserUpdate,
) -> Any:
    return await api.patch_user_by_uuid(db, user_uuid, data)


@router.delete("/users/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: SessionDB, user_uuid: uuid.UUID) -> None:
    await api.delete_user_by_uuid(db, user_uuid)


# ==============================================
# DB Token Routes
# ==============================================


@router.get("/tokens/", response_model=RefreshTokensList)
async def list_tokens(db: SessionDB, filters: TokensFilter) -> Any:
    return await api.list_all_refresh_tokens(db, filters)


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(db: SessionDB, token_id: int) -> None:
    await api.delete_token_by_id(db, token_id)


# ==============================================
# DB Todo Routes
# ==============================================


@router.get("/todos", response_model=TodoList)
async def list_todos(db: SessionDB, filters: TodosFilter) -> Any:
    return await api.list_all_todos(db, filters)


@router.get("/todos/{todo_uuid}", response_model=TodoResponse)
async def get_todo(db: SessionDB, todo_uuid: uuid.UUID) -> Any:
    return await api.admin_get_todo_by_uuid(db, todo_uuid)


@router.delete("/todos/{todo_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: SessionDB, todo_uuid: uuid.UUID) -> None:
    await api.admin_delete_todo_by_uuid(db, todo_uuid)
