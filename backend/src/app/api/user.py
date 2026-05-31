import uuid
from typing import Any

from fastapi import APIRouter, status

from app.core.dependencies import CurrentSuperUser, CurrentUser, SessionDB, UsersFilter
from app.schemas import (
    UserList,
    UserPrivate,
    UserRequestPassword,
    UserSchema,
    UserUpdate,
)
from app.services import api

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserList)
async def list_users(
    db: SessionDB, only_superuser: CurrentSuperUser, filters: UsersFilter
) -> Any:
    """
    Superuser only
    """
    return await api.list_all_users(db, filters)


@router.get("/{user_uuid}", response_model=UserSchema)
async def get_user(
    db: SessionDB, only_superuser: CurrentSuperUser, user_uuid: uuid.UUID
) -> Any:
    return await api.get_user_by_uuid(db, user_uuid)


@router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: SessionDB, only_superuser: CurrentSuperUser, user_uuid: uuid.UUID
) -> None:
    await api.delete_user_by_uuid(db, user_uuid)


@router.get("/me", response_model=UserPrivate)
async def me(current_user: CurrentUser) -> Any:
    return current_user


@router.patch("/me", response_model=UserPrivate)
async def patch_me(db: SessionDB, current_user: CurrentUser, data: UserUpdate) -> Any:
    return await api.patch_current_user(db, current_user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: SessionDB, current_user: CurrentUser, data: UserRequestPassword
) -> None:
    await api.delete_current_user(db, current_user, data)
