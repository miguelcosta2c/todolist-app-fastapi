from typing import Any

from fastapi import APIRouter, Request, status

from app.core.dependencies import CurrentUser, SessionDB
from app.core.limiter import limiter
from app.core.settings import settings
from app.schemas import (
    UserPrivate,
    UserRequestPassword,
    UserUpdate,
)
from app.services import api

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/me", response_model=UserPrivate)
@limiter.limit(settings.RATE_LIMIT_USER)
async def me(request: Request, current_user: CurrentUser) -> Any:
    return current_user


@router.patch("/me", response_model=UserPrivate)
@limiter.limit(settings.RATE_LIMIT_USER)
async def patch_me(
    request: Request, db: SessionDB, current_user: CurrentUser, data: UserUpdate
) -> Any:
    return await api.patch_current_user(db, current_user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.RATE_LIMIT_USER)
async def delete_me(
    request: Request,
    db: SessionDB,
    current_user: CurrentUser,
    data: UserRequestPassword,
) -> None:
    await api.delete_current_user(db, current_user, data)
