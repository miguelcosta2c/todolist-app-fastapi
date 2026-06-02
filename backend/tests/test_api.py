import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.exc import InvalidCredentialsError, InvalidTokenError
from app.models import User, UserToken
from app.models.user import UserStatus
from app.schemas import UserCreate
from app.services.auth import (
    authenticate_user,
    db_validate_refresh_token,
    get_refresh_token_in_db,
    revoke_refresh_token_in_db,
)
from app.services.user import UserDBService

# =============================
# Helpers
# =============================

USER_DATA = {
    "username": "miguel",
    "email": "miguel@email.com",
    "password": "Senha123@",
    "confirm_password": "Senha123@",
}


async def create_user(session: AsyncSession, **overrides: Any) -> None:
    data = {**USER_DATA, **overrides}
    await UserDBService(session).create_user(UserCreate(**data))


# =============================
# POST /auth/register
# =============================


async def test_register_success(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=USER_DATA)

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["username"] == USER_DATA["username"]
    assert body["email"] == USER_DATA["email"]
    assert "uuid_" in body
    assert "password" not in body


async def test_register_duplicate_email(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)

    response = await client.post(
        "/auth/register",
        json={**USER_DATA, "username": "outro"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_register_duplicate_username(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)

    response = await client.post(
        "/auth/register",
        json={**USER_DATA, "email": "outro@email.com"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_register_passwords_do_not_match(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={**USER_DATA, "confirm_password": "diferente"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# =============================
# POST /auth/token
# =============================


async def test_login_success(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)

    response = await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"  # noqa: S105
    assert "refresh_token" in response.cookies


async def test_login_wrong_password(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)

    response = await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": "errada"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_nonexistent_user(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": "naoexiste@email.com", "password": "qualquer"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_deleted_user(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)

    response = await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================
# POST /auth/refresh
# =============================


async def test_refresh_success(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)

    login = await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )
    assert login.status_code == status.HTTP_200_OK

    response = await client.post("/auth/refresh")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body


async def test_refresh_without_cookie(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_revokes_old_token(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)

    login = await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )
    assert login.status_code == status.HTTP_200_OK
    original_token = login.cookies["refresh_token"]

    # Primeiro refresh funciona
    first_refresh = await client.post("/auth/refresh")
    assert first_refresh.status_code == status.HTTP_200_OK

    # Token original foi revogado — não pode ser usado novamente
    client.cookies.set("refresh_token", original_token)
    revoked_response = await client.post("/auth/refresh")
    assert revoked_response.status_code == status.HTTP_401_UNAUTHORIZED

    client.cookies.clear()


# =============================
# POST /auth/revoke_token
# =============================


async def test_logout_success(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)

    await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )

    response = await client.post("/auth/revoke_token")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Logout realizado com sucesso"
    assert "refresh_token" not in response.cookies


async def test_logout_without_cookie(client: AsyncClient) -> None:
    response = await client.post("/auth/revoke_token")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_twice(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)

    await client.post(
        "/auth/token",
        data={"username": USER_DATA["email"], "password": USER_DATA["password"]},
    )
    await client.post("/auth/revoke_token")

    # Segundo logout com token já revogado
    response = await client.post("/auth/revoke_token")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(**kwargs: object) -> MagicMock:
    user = MagicMock(spec=User)
    user.status = UserStatus.ACTIVE
    user.password_hash = "hashed"  # noqa: S105
    for k, v in kwargs.items():
        setattr(user, k, v)
    return user


def make_db_token(**kwargs: object) -> MagicMock:
    token = MagicMock(spec=UserToken)
    token.is_revoked = False
    token.user_uuid = uuid.uuid4()
    for k, v in kwargs.items():
        setattr(token, k, v)
    return token


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------


class TestAuthenticateUser:
    async def test_returns_user_on_valid_credentials(self) -> None:
        db: AsyncMock = AsyncMock()
        user: MagicMock = make_user()
        db.scalar.return_value = user

        with patch("app.services.auth.verify_password", return_value=True):
            result: User = await authenticate_user(db, "a@b.com", "secret")

        assert result is user

    async def test_raises_when_user_not_found(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await authenticate_user(db, "no@one.com", "secret")

    async def test_raises_on_wrong_password(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = make_user()

        with (
            patch("app.services.auth.verify_password", return_value=False),
            pytest.raises(InvalidCredentialsError),
        ):
            await authenticate_user(db, "a@b.com", "wrong")


# ---------------------------------------------------------------------------
# get_refresh_token_in_db
# ---------------------------------------------------------------------------


class TestGetRefreshTokenInDb:
    async def test_returns_token_when_found(self) -> None:
        db: AsyncMock = AsyncMock()
        fake_token: MagicMock = make_db_token()
        db.scalar.return_value = fake_token

        result: UserToken | None = await get_refresh_token_in_db(db, "tok")

        assert result is fake_token

    async def test_returns_none_when_not_found(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = None

        result: UserToken | None = await get_refresh_token_in_db(db, "tok")

        assert result is None


# ---------------------------------------------------------------------------
# revoke_refresh_token_in_db
# ---------------------------------------------------------------------------


class TestRevokeRefreshTokenInDb:
    async def test_revokes_existing_token(self) -> None:
        db: AsyncMock = AsyncMock()
        token: MagicMock = make_db_token(is_revoked=False)

        with patch(
            "app.services.auth.get_refresh_token_in_db", AsyncMock(return_value=token)
        ):
            await revoke_refresh_token_in_db(db, "tok")

        assert token.is_revoked is True
        db.commit.assert_called_once()

    async def test_raises_when_token_not_in_db(self) -> None:
        # line 47-48
        db: AsyncMock = AsyncMock()

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=None),
            ),
            pytest.raises(InvalidTokenError),
        ):
            await revoke_refresh_token_in_db(db, "missing")


# ---------------------------------------------------------------------------
# db_validate_refresh_token
# ---------------------------------------------------------------------------


class TestDbValidateRefreshToken:
    async def test_returns_token_on_valid_refresh_token(self) -> None:
        user_uuid: uuid.UUID = uuid.uuid4()
        token: MagicMock = make_db_token(is_revoked=False, user_uuid=user_uuid)
        db: AsyncMock = AsyncMock()
        payload: dict[str, str] = {"type": "refresh", "sub": str(user_uuid)}

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", return_value=payload),
        ):
            result: UserToken = await db_validate_refresh_token("tok", db)

        assert result is token

    async def test_raises_when_token_not_in_db(self) -> None:
        # line 77-78
        db: AsyncMock = AsyncMock()

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=None),
            ),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("missing", db)

    async def test_revokes_and_raises_on_expired_token(self) -> None:
        # lines 84-91
        token: MagicMock = make_db_token()
        db: AsyncMock = AsyncMock()

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch(
                "app.services.auth.decode_token", side_effect=ExpiredSignatureError()
            ),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("expired", db)

        assert token.is_revoked is True
        db.commit.assert_called_once()

    async def test_revokes_and_raises_on_invalid_jwt(self) -> None:
        # lines 84-91 via JWTError
        token: MagicMock = make_db_token()
        db: AsyncMock = AsyncMock()

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", side_effect=JWTError()),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("invalid_jwt", db)

        assert token.is_revoked is True

    async def test_raises_when_token_type_is_not_refresh(self) -> None:
        # lines 96-97
        token: MagicMock = make_db_token()
        db: AsyncMock = AsyncMock()
        payload: dict[str, str] = {"type": "access", "sub": str(uuid.uuid4())}

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", return_value=payload),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("tok", db)

    async def test_raises_when_sub_is_missing(self) -> None:
        # lines 102-103
        token: MagicMock = make_db_token()
        db: AsyncMock = AsyncMock()
        payload: dict[str, str] = {"type": "refresh"}  # no "sub"

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", return_value=payload),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("tok", db)

    async def test_raises_when_token_is_revoked(self) -> None:
        user_uuid: uuid.UUID = uuid.uuid4()
        token: MagicMock = make_db_token(is_revoked=True, user_uuid=user_uuid)
        db: AsyncMock = AsyncMock()
        payload: dict[str, str] = {"type": "refresh", "sub": str(user_uuid)}

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", return_value=payload),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("tok", db)

    async def test_raises_when_uuid_does_not_match(self) -> None:
        # lines 113-114
        token: MagicMock = make_db_token(is_revoked=False, user_uuid=uuid.uuid4())
        db: AsyncMock = AsyncMock()
        # sub aponta para um UUID diferente do token no banco
        payload: dict[str, str] = {"type": "refresh", "sub": str(uuid.uuid4())}

        with (
            patch(
                "app.services.auth.get_refresh_token_in_db",
                AsyncMock(return_value=token),
            ),
            patch("app.services.auth.decode_token", return_value=payload),
            pytest.raises(InvalidTokenError),
        ):
            await db_validate_refresh_token("tok", db)


# =============================
# GET /health
# =============================


async def test_health_success(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


# =============================
# get_db rollback on error
# =============================


async def test_get_db_rollback_on_error() -> None:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    with patch("app.core.dependencies.AsyncSessionLocal") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        gen = get_db()
        await gen.__anext__()

        with pytest.raises(RuntimeError):
            await gen.athrow(RuntimeError("db error"))

        mock_session.rollback.assert_awaited_once()


# =============================
# get_current_user exceptions
# =============================


class TestGetCurrentUserExceptions:
    async def test_expired_token(self, client: AsyncClient) -> None:
        with patch(
            "app.core.dependencies.decode_token",
            side_effect=ExpiredSignatureError(),
        ):
            response = await client.get(
                "/users/me",
                headers={"Authorization": "Bearer expired"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expirado" in response.json()["detail"]

    async def test_wrong_token_type(self, client: AsyncClient) -> None:
        with patch(
            "app.core.dependencies.decode_token",
            return_value={"type": "refresh", "sub": str(uuid.uuid4())},
        ):
            response = await client.get(
                "/users/me",
                headers={"Authorization": "Bearer token_tipo_errado"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token inválido para esta operação" in response.json()["detail"]

    async def test_missing_sub(self, client: AsyncClient) -> None:
        with patch(
            "app.core.dependencies.decode_token",
            return_value={"type": "access"},
        ):
            response = await client.get(
                "/users/me",
                headers={"Authorization": "Bearer sem_sub"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token inválido" in response.json()["detail"]

    async def test_user_not_found(self, client: AsyncClient) -> None:
        some_uuid = uuid.uuid4()
        with (
            patch(
                "app.core.dependencies.decode_token",
                return_value={"type": "access", "sub": str(some_uuid)},
            ),
            patch(
                "app.core.dependencies.UserDBService.get_user_by_uuid",
                AsyncMock(return_value=None),
            ),
        ):
            response = await client.get(
                "/users/me",
                headers={"Authorization": "Bearer token_sem_usuario"},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "não encontrado" in response.json()["detail"]
