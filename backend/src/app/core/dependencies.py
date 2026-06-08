import logging
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
from app.schemas import RefreshTokensListFilter, TodoListFilters, UserListFilters
from app.services.user import UserDBService

logger = logging.getLogger(__name__)

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
        logger.warning("Token de acesso expirado: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token de acesso informado expirou.",
        ) from err
    except JWTError as err:
        logger.warning("Token de acesso inválido: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token de acesso informado é inválido.",
        ) from err

    if payload.get("type") != "access":
        logger.warning("Tipo de token inválido para acesso: %s", payload.get("type"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token informado não é válido para esta operação.",
        )

    user_uuid = payload.get("sub")

    if not user_uuid:
        logger.warning("Token de acesso não contém o identificador do usuário")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token de acesso informado é inválido.",
        )

    user = await UserDBService(db).get_user_by_uuid(user_uuid)

    if user is None:
        logger.warning("Usuário não encontrado para o UUID: %s", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O usuário associado a este token não foi encontrado.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:

    if not current_user.is_superuser:
        logger.warning(
            "Acesso negado ao usuário %s: permissão de superusuário necessária",
            current_user.uuid_,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para realizar esta ação.",
        )

    return current_user


CurrentSuperUser = Annotated[User, Depends(get_current_superuser)]

# ==================================================================
# Filter dependencies
# ==================================================================

UsersFilter = Annotated[UserListFilters, Depends()]
TokensFilter = Annotated[RefreshTokensListFilter, Depends()]
TodosFilter = Annotated[TodoListFilters, Depends()]
