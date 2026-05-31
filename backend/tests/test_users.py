import json
from typing import Any

import pytest
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
    "password": "senha123",
    "confirm_password": "senha123",
}

SUPERUSER_DATA = {
    "username": "admin",
    "email": "admin@email.com",
    "password": "admin123",
    "confirm_password": "admin123",
}


async def create_user(session: AsyncSession, **overrides: Any) -> None:
    data = {**USER_DATA, **overrides}
    await UserDBService(session).create_user(UserCreate(**data))


async def create_superuser(session: AsyncSession) -> None:
    await UserDBService(session).create_user(
        UserCreate(**SUPERUSER_DATA), is_superuser=True
    )


async def login(client: AsyncClient, email: str, password: str) -> None:
    await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )


async def get_access_token(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


# =============================
# GET /users/me
# =============================


async def test_me_success(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == USER_DATA["email"]
    assert body["username"] == USER_DATA["username"]


async def test_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_me_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/users/me",
        headers={"Authorization": "Bearer token_invalido"},
    )
    assert response.status_code == 401


# =============================
# PATCH /users/me
# =============================


async def test_patch_me_username(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "novo_username",
            "email": None,
            "password": USER_DATA["password"],
            "new_password": USER_DATA["password"],
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "novo_username"


async def test_patch_me_wrong_password(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "novo_username",
            "email": None,
            "password": "senha_errada",
            "new_password": "nova_senha",
        },
    )

    assert response.status_code == 401


async def test_patch_me_unauthorized(client: AsyncClient) -> None:
    response = await client.patch(
        "/users/me",
        json={
            "username": "novo",
            "email": None,
            "password": "senha123",
            "new_password": "nova_senha",
        },
    )
    assert response.status_code == 401


# =============================
# DELETE /users/me
# =============================


async def test_delete_me_success(client: AsyncClient, session: AsyncSession) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.request(
        "DELETE",
        "/users/me",
        content=json.dumps(
            {
                "password": USER_DATA["password"],
                "confirm_password": USER_DATA["password"],
            }
        ),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 204


async def test_delete_me_wrong_password(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.request(
        "DELETE",
        "/users/me",
        content=json.dumps(
            {
                "password": "senha_errada",
                "confirm_password": "senha_errada",
            }
        ),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400


async def test_delete_me_passwords_do_not_match(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.request(
        "DELETE",
        "/users/me",
        content=json.dumps(
            {
                "password": "senha123",
                "confirm_password": "diferente",
            }
        ),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 422


async def test_delete_me_unauthorized(client: AsyncClient) -> None:
    response = await client.request(
        "DELETE",
        "/users/me",
        content=json.dumps({"password": "senha123", "confirm_password": "senha123"}),
    )
    assert response.status_code == 401


# =============================
# GET /users/ (superuser only)
# =============================


async def test_list_users_as_superuser(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    await create_superuser(session)
    token = await get_access_token(
        client, SUPERUSER_DATA["email"], SUPERUSER_DATA["password"]
    )

    response = await client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_users_as_regular_user(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


async def test_list_users_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/users/")
    assert response.status_code == 401


# =============================
# UserDBService
# =============================


async def test_get_user_by_invalid_field(session: AsyncSession) -> None:
    with pytest.raises(ValueError, match="Campo inválido"):
        await UserDBService(session).get_user_by(campo_invalido="valor")


async def test_get_all_users(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")

    users = await UserDBService(session).get_all_users(offset=0, limit=10)
    assert len(users) == 2


async def test_get_all_users_with_pagination(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")

    users = await UserDBService(session).get_all_users(offset=0, limit=1)
    assert len(users) == 1


async def test_update_user_no_changes(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    # Atualiza com os mesmos dados — não deve fazer commit
    updated = await UserDBService(session).update_user(
        user, {"username": USER_DATA["username"]}
    )
    assert updated.username == USER_DATA["username"]


async def test_get_user_by_uuid(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    found = await UserDBService(session).get_user_by_uuid(user.uuid_)
    assert found is not None
    assert found.uuid_ == user.uuid_
