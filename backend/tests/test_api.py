from typing import Any

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import UserCreate
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
