from typing import Any

from fastapi import APIRouter

from app.core.dependencies import CurrentSuperUser, CurrentUser, SessionDB
from app.schemas import UserPrivate, UserSchema, UserUpdate
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


@router.patch("/me/patch", response_model=UserPrivate)
async def patch_me(db: SessionDB, current_user: CurrentUser, data: UserUpdate) -> Any:
    return await UserDBService(db).update_user(current_user, data)
