from typing import Any

from fastapi import APIRouter, Response, status

from app.core.dependencies import LoginForm, RefreshToken, SessionDB
from app.schemas import Message, TokenResponse, UserCreate, UserPublic
from app.services import api

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic
)
async def register(db: SessionDB, data: UserCreate) -> Any:
    return await api.register_user(db, data)


@router.post("/token", response_model=TokenResponse)
async def login(db: SessionDB, form_data: LoginForm, response: Response) -> Any:
    return await api.login_user(db, form_data.username, form_data.password, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    db: SessionDB,
    user_refresh_token: RefreshToken,
    response: Response,
) -> dict[str, Any]:
    return await api.generate_new_tokens_user(db, user_refresh_token, response)


@router.post("/revoke_token", response_model=Message)
async def logout(
    db: SessionDB,
    user_refresh_token: RefreshToken,
    response: Response,
) -> Any:
    return await api.logout_user(db, user_refresh_token, response)
