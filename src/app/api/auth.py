from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from app.core.dependencies import RefreshToken, SessionDB
from app.core.security import create_access_token, create_refresh_token
from app.core.settings import settings
from app.schemas.auth import TokenResponse, UserCreate, UserPublic
from app.services.api import api_validate_refresh_token
from app.services.auth import (
    authenticate_user,
    create_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


IS_SECURE = settings.IS_SECURE


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic
)
async def register(data: UserCreate, session: SessionDB) -> Any:
    user = await create_user(session, data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    return user


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDB,
    response: Response,
) -> Any:
    user = await authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user.uuid_)
    refresh_token = await create_refresh_token(user.uuid_, db)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Protege contra XSS
        secure=IS_SECURE,  # Apenas via HTTPS
        samesite="lax",  # Protege contra CSRF
        max_age=60 * 60 * 24 * 7,
    )

    return {"access_token": token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    user_refresh_token: RefreshToken, db: SessionDB, response: Response
) -> dict[str, Any]:
    # Validando o refresh token
    refresh_token = await api_validate_refresh_token(user_refresh_token, response, db)

    # Criando novo access e refresh token
    user_uuid = refresh_token.user_uuid

    new_access_token = create_access_token(user_uuid)
    new_refresh_token = await create_refresh_token(user_uuid, db)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,  # Protege contra XSS
        secure=IS_SECURE,  # Apenas via HTTPS
        samesite="lax",  # Protege contra CSRF
        max_age=60 * 60 * 24 * 7,
    )

    # Retorna o novo access token no corpo da resposta
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/revoke_token")
async def logout(
    user_refresh_token: RefreshToken, db: SessionDB, response: Response
) -> Any:
    refresh_token = await api_validate_refresh_token(user_refresh_token, response, db)

    try:
        refresh_token.is_revoked = True
        await db.commit()
    except Exception as err:
        await db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao comitar"
        ) from err

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=IS_SECURE,
        samesite="lax",
    )

    return {"message": "Logout realizado com sucesso"}
