import uuid
from typing import Any

from fastapi import APIRouter, Request, status

from app.core.dependencies import CurrentUser, SessionDB, TodosFilter
from app.core.limiter import limiter
from app.core.settings import settings
from app.schemas import (
    TodoCreate,
    TodoList,
    TodoResponse,
    TodoUpdate,
)
from app.services import api

router = APIRouter(prefix="/todos", tags=["Todo"])


@router.get("/", response_model=TodoList)
@limiter.limit(settings.RATE_LIMIT_TODO)
async def list_my_todos(
    request: Request, db: SessionDB, current_user: CurrentUser, filters: TodosFilter
) -> Any:
    return await api.list_user_todos(db, current_user.uuid_, filters)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
@limiter.limit(settings.RATE_LIMIT_TODO)
async def create_my_todo(
    request: Request, db: SessionDB, current_user: CurrentUser, data: TodoCreate
) -> Any:
    return await api.create_user_todo(db, current_user.uuid_, data)


@router.get("/{todo_uuid}", response_model=TodoResponse)
@limiter.limit(settings.RATE_LIMIT_TODO)
async def get_my_todo(
    request: Request, db: SessionDB, current_user: CurrentUser, todo_uuid: uuid.UUID
) -> Any:
    return await api.get_user_todo(db, current_user.uuid_, todo_uuid)


@router.patch("/{todo_uuid}", response_model=TodoResponse)
@limiter.limit(settings.RATE_LIMIT_TODO)
async def patch_my_todo(
    request: Request,
    db: SessionDB,
    current_user: CurrentUser,
    todo_uuid: uuid.UUID,
    data: TodoUpdate,
) -> Any:
    return await api.patch_user_todo(db, current_user.uuid_, todo_uuid, data)


@router.delete("/{todo_uuid}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.RATE_LIMIT_TODO)
async def delete_my_todo(
    request: Request,
    db: SessionDB,
    current_user: CurrentUser,
    todo_uuid: uuid.UUID,
) -> None:
    await api.delete_user_todo(db, current_user.uuid_, todo_uuid)
