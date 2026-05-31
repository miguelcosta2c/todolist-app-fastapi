from typing import Any

from fastapi import APIRouter, status

from app.core.dependencies import CurrentSuperUser, CurrentUser, SessionDB
from app.schemas import UserPrivate, UserRequestPassword, UserSchema, UserUpdate
from app.services import api
from app.services.user import UserDBService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserSchema])
async def list_users(
    db: SessionDB, only_superuser: CurrentSuperUser, offset: int = 0, limit: int = 10
) -> Any:
    """
    Superuser only
    """
    return await UserDBService(db).get_all_users(offset, limit)


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
