import json
from datetime import datetime
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import TIMEZONE
from app.models.user import UserStatus
from app.schemas import UserCreate, UserListFilters
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

SUPERUSER_DATA = {
    "username": "admin",
    "email": "admin@email.com",
    "password": "Admin123@",
    "confirm_password": "Admin123@",
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

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["email"] == USER_DATA["email"]
    assert body["username"] == USER_DATA["username"]


async def test_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_me_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/users/me",
        headers={"Authorization": "Bearer token_invalido"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
            "password": USER_DATA["password"],
            "new_password": USER_DATA["password"],
        },
    )

    assert response.status_code == status.HTTP_200_OK
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
            "password": "SenhaErrada@123",
            "new_password": "NovaSenha@123",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_patch_me_unauthorized(client: AsyncClient) -> None:
    response = await client.patch(
        "/users/me",
        json={
            "username": "novo",
            "password": "senha123",
            "new_password": "nova_senha",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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

    assert response.status_code == status.HTTP_204_NO_CONTENT


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

    assert response.status_code == status.HTTP_400_BAD_REQUEST


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

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_delete_me_unauthorized(client: AsyncClient) -> None:
    response = await client.request(
        "DELETE",
        "/users/me",
        content=json.dumps({"password": "senha123", "confirm_password": "senha123"}),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["result"], list)


async def test_list_users_as_regular_user(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_list_users_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/admin/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================
# UserDBService
# =============================


async def test_get_user_by_invalid_field(session: AsyncSession) -> None:
    with pytest.raises(ValueError, match="O campo informado é inválido"):
        await UserDBService(session).get_user_by(campo_invalido="valor")


async def test_get_all_users(session: AsyncSession) -> None:
    users_numero_experado = 2
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")

    filters = UserListFilters(offset=0, limit=10)

    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == users_numero_experado


async def test_get_all_users_with_pagination(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")

    filters = UserListFilters(offset=0, limit=1)

    users = await UserDBService(session).get_all_users(filters)
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


# =============================
# get_all_users filter branches
# =============================


async def test_get_all_users_filter_by_username(
    session: AsyncSession,
) -> None:
    await create_user(session, username="joao", email="joao@test.com")
    await create_user(session, username="jose", email="jose@test.com")
    await create_user(session, username="maria", email="maria@test.com")

    filters = UserListFilters(offset=0, limit=10, username="joa")
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1
    assert users[0].username == "joao"


async def test_get_all_users_filter_by_email(
    session: AsyncSession,
) -> None:
    await create_user(session, email="joao@test.com")
    await create_user(
        session, username="jose", email="jose@outro.com"
    )

    filters = UserListFilters(offset=0, limit=10, email="test")
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1
    assert users[0].email == "joao@test.com"


async def test_get_all_users_filter_by_status(
    session: AsyncSession,
) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)

    await create_user(session, username="outro", email="outro@email.com")

    filters = UserListFilters(
        offset=0, limit=10, status=UserStatus.DELETED, include_deleted=True
    )
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1
    assert users[0].status == UserStatus.DELETED


async def test_get_all_users_filter_by_is_superuser(
    session: AsyncSession,
) -> None:
    await create_user(session)
    data = {**USER_DATA, "username": "admin", "email": "admin@test.com"}
    await UserDBService(session).create_user(
        UserCreate(**data), is_superuser=True
    )

    filters = UserListFilters(offset=0, limit=10, is_superuser=True)
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1
    assert users[0].is_superuser is True


async def test_get_all_users_filter_by_created_after(
    session: AsyncSession,
) -> None:
    await create_user(session)
    filters = UserListFilters(
        offset=0,
        limit=10,
        created_after=datetime.now(TIMEZONE),
    )
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 0


async def test_get_all_users_filter_by_created_before(
    session: AsyncSession,
) -> None:
    await create_user(session)
    filters = UserListFilters(
        offset=0,
        limit=10,
        created_before=datetime.now(TIMEZONE),
    )
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1


async def test_get_all_users_include_deleted(
    session: AsyncSession,
) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)

    filters = UserListFilters(offset=0, limit=10, include_deleted=True)
    users = await UserDBService(session).get_all_users(filters)
    assert len(users) == 1


async def test_get_user_by_uuid_only_active_false(
    session: AsyncSession,
) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)

    # only_active=True (default) should NOT find deleted user
    found = await UserDBService(session).get_user_by_uuid(user.uuid_)
    assert found is None

    # only_active=False should find deleted user
    found = await UserDBService(session).get_user_by_uuid(
        user.uuid_, only_active=False
    )
    assert found is not None
    assert found.uuid_ == user.uuid_


# =============================
# count_users filter branches
# =============================


async def test_count_users_default(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10)
    )
    assert total == 2


async def test_count_users_include_deleted(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10, include_deleted=True)
    )
    assert total == 1

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10, include_deleted=False)
    )
    assert total == 0


async def test_count_users_filter_by_username(session: AsyncSession) -> None:
    await create_user(session, username="joao", email="joao@test.com")
    await create_user(session, username="jose", email="jose@test.com")

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10, username="joa")
    )
    assert total == 1


async def test_count_users_filter_by_email(session: AsyncSession) -> None:
    await create_user(session, email="joao@test.com")
    await create_user(session, username="jose", email="jose@outro.com")

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10, email="test")
    )
    assert total == 1


async def test_count_users_filter_by_status(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await UserDBService(session).delete_user(user)
    await create_user(session, username="outro", email="outro@email.com")

    total = await UserDBService(session).count_users(
        UserListFilters(
            offset=0, limit=10, status=UserStatus.DELETED, include_deleted=True
        )
    )
    assert total == 1


async def test_count_users_filter_by_is_superuser(session: AsyncSession) -> None:
    await create_user(session)
    await UserDBService(session).create_user(
        UserCreate(**{**USER_DATA, "username": "admin", "email": "admin@test.com"}),
        is_superuser=True,
    )

    total = await UserDBService(session).count_users(
        UserListFilters(offset=0, limit=10, is_superuser=True)
    )
    assert total == 1


async def test_count_users_filter_by_created_after(session: AsyncSession) -> None:
    await create_user(session)

    total = await UserDBService(session).count_users(
        UserListFilters(
            offset=0, limit=10, created_after=datetime.now(TIMEZONE),
        )
    )
    assert total == 0


async def test_count_users_filter_by_created_before(session: AsyncSession) -> None:
    await create_user(session)

    total = await UserDBService(session).count_users(
        UserListFilters(
            offset=0, limit=10, created_before=datetime.now(TIMEZONE),
        )
    )
    assert total == 1
