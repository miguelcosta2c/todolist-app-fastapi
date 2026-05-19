from typing import Any

from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.schemas.auth import UserPrivate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserPrivate)
async def user(current_user: CurrentUser) -> Any:
    return current_user
