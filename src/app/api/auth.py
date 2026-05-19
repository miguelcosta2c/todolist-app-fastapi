from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from app.core.dependencies import RefreshToken, SessionDB
from app.core.settings import settings
from app.exc import InvalidCredentialsError
from app.schemas.api import Message
from app.schemas.auth import TokenResponse, UserCreate, UserPublic
from app.services.api import (
    api_validate_refresh_token,
    delete_cookie_refresh_token,
    generate_tokens,
)
from app.services.auth import (
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


IS_SECURE = settings.IS_SECURE


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic
)
async def register(data: UserCreate, session: SessionDB) -> Any:
    try:
        user = await create_user(session, data)
    except UserAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        ) from err
    return user


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDB,
    response: Response,
) -> Any:
    try:
        user = await authenticate_user(
            db,
            form_data.username,
            form_data.password,
        )
    except InvalidCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from err

    return await generate_tokens(user.uuid_, db, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    user_refresh_token: RefreshToken, db: SessionDB, response: Response
) -> dict[str, Any]:
    # Validando o refresh token
    refresh_token = await api_validate_refresh_token(user_refresh_token, response, db)
    # Retornando novo access e refresh token
    return await generate_tokens(refresh_token.user_uuid, db, response)


@router.post("/revoke_token", response_model=Message)
async def logout(
    user_refresh_token: RefreshToken, db: SessionDB, response: Response
) -> Any:
    # Validando o refresh token
    refresh_token = await api_validate_refresh_token(user_refresh_token, response, db)

    # Revogando o refresh token
    refresh_token.is_revoked = True
    await db.commit()

    # Deletando o refresh token do cookie
    delete_cookie_refresh_token(response)

    return {"message": "Logout realizado com sucesso"}
