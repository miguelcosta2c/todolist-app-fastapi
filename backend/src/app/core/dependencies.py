from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    APIKeyCookie,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db import AsyncSessionLocal
from app.models import User
from app.schemas import RefreshTokensListFilter, UserListFilters
from app.services.user import UserDBService

# ==================================================================
# Session Dependency
# ==================================================================


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise


SessionDB = Annotated[AsyncSession, Depends(get_db)]

# ==================================================================
# Auth dependencies
# ==================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
refresh_cookie_scheme = APIKeyCookie(name="refresh_token", auto_error=False)

LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]

Token = Annotated[str, Depends(oauth2_scheme)]
RefreshToken = Annotated[str | None, Depends(refresh_cookie_scheme)]


async def get_current_user(token: Token, db: SessionDB) -> User:
    try:
        payload: dict[str, Any] = decode_token(token)
    except ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expirado.",
        ) from err
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        ) from err

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para esta operação.",
        )

    user_uuid = payload.get("sub")

    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    user = await UserDBService(db).get_user_by_uuid(user_uuid)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para fazer esta acao",
        )

    return current_user


CurrentSuperUser = Annotated[User, Depends(get_current_superuser)]

# ==================================================================
# Filter dependencies
# ==================================================================

UsersFilter = Annotated[UserListFilters, Depends()]
TokensFilter = Annotated[RefreshTokensListFilter, Depends()]
