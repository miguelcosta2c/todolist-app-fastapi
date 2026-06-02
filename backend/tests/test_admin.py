import uuid
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
    "username": "regular_user",
    "email": "regular@test.com",
    "password": "User123@",
    "confirm_password": "User123@",
}

ADMIN_DATA = {
    "username": "superadmin",
    "email": "admin@test.com",
    "password": "Admin123@",
    "confirm_password": "Admin123@",
}


async def _create_user(
    session: AsyncSession, data: dict[str, Any], is_superuser: bool = False
) -> None:
    await UserDBService(session).create_user(
        UserCreate(**data), is_superuser=is_superuser
    )


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


# =============================
# GET /users/{user_uuid}
# =============================


async def test_get_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.get(
        f"/users/{user.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == USER_DATA["email"]


async def test_get_user_by_uuid_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.get(
        f"/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# PATCH /users/{user_uuid}
# =============================


async def test_patch_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.patch(
        f"/users/{user.uuid_}",
        json={"username": "novo_nome"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "novo_nome"


# =============================
# DELETE /users/{user_uuid}
# =============================


async def test_delete_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.delete(
        f"/users/{user.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


# =============================
# GET /tokens/
# =============================


async def test_list_tokens_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    admin_token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    # Login as regular user to create a refresh token in DB
    await _login(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        "/tokens/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "result" in body
    assert body["total"] >= 1


# =============================
# DELETE /tokens/{token_id}
# =============================


async def test_delete_token_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    admin_token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    # Login as regular user to create a refresh token
    await _login(client, USER_DATA["email"], USER_DATA["password"])

    # List tokens to get the ID
    list_resp = await client.get(
        "/tokens/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token_id = list_resp.json()["result"][0]["id"]

    response = await client.delete(
        f"/tokens/{token_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_delete_token_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.delete(
        "/tokens/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
