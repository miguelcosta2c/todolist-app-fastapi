import uuid

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.core.settings import settings
from app.models import UserToken
from app.services.auth import InvalidTokenError, validate_refresh_token


async def api_validate_refresh_token(
    refresh_token: str | None, response: Response, db: AsyncSession
) -> UserToken:
    """
    Faz a mesma coisa que "app.auth.services.validate_refresh_token", porem gera os
    erros para a api.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao esta logado.",
        )

    try:
        db_refresh_token = await validate_refresh_token(refresh_token, db)
    except InvalidTokenError as err:
        # Deletando o token invalido
        response.delete_cookie(
            "refresh_token", httponly=True, samesite="lax", secure=settings.IS_SECURE
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=err.mensagem
        ) from err

    return db_refresh_token


async def generate_tokens(
    user_uuid: uuid.UUID, db: AsyncSession, response: Response
) -> dict[str, str]:
    access_token = create_access_token(user_uuid)
    refresh_token = await create_refresh_token(user_uuid, db)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Protege contra XSS
        secure=settings.IS_SECURE,  # Apenas via HTTPS
        samesite="lax",  # Protege contra CSRF
        max_age=60 * 60 * 24 * 7,
    )

    return {"access_token": access_token, "token_type": "bearer"}


def delete_cookie_refresh_token(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.IS_SECURE,
        samesite="lax",
    )
