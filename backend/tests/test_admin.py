import uuid
from typing import Any

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import TodoPriority, TodoStatus
from app.schemas import TodoCreate, UserCreate
from app.services.todo import TodoDBService
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
# GET /admin/users/{user_uuid}
# =============================


async def test_get_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.get(
        f"/admin/users/{user.uuid_}",
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
        f"/admin/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# PATCH /admin/users/{user_uuid}
# =============================


async def test_patch_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.patch(
        f"/admin/users/{user.uuid_}",
        json={"username": "novo_nome"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "novo_nome"


# =============================
# DELETE /admin/users/{user_uuid}
# =============================


async def test_delete_user_by_uuid_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    response = await client.delete(
        f"/admin/users/{user.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


# =============================
# GET /admin/tokens/
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
        "/admin/tokens/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "result" in body
    assert body["total"] >= 1


# =============================
# DELETE /admin/tokens/{token_id}
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
        "/admin/tokens/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token_id = list_resp.json()["result"][0]["id"]

    response = await client.delete(
        f"/admin/tokens/{token_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_delete_token_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.delete(
        "/admin/tokens/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# GET /admin/todos
# =============================


async def test_admin_list_todos_empty(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []
    assert body["total"] == 0


async def test_admin_list_todos_with_items(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    await TodoDBService(session).create_todo(
        TodoCreate(name="Todo do usuario regular"), user.uuid_
    )

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["result"][0]["name"] == "Todo do usuario regular"


async def test_admin_list_todos_filter_by_status(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Em progresso"), user.uuid_
    )
    await TodoDBService(session).create_todo(
        TodoCreate(name="Concluida"), user.uuid_
    )
    await TodoDBService(session).update_todo(
        todo, {"status": TodoStatus.IN_PROGRESS}
    )

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "IN_PROGRESS"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["result"][0]["name"] == "Em progresso"


async def test_admin_list_todos_filter_by_priority(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    await TodoDBService(session).create_todo(
        TodoCreate(name="Importante", priority=TodoPriority.HIGH), user.uuid_
    )
    await TodoDBService(session).create_todo(
        TodoCreate(name="Normal"), user.uuid_
    )

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
        params={"priority": "HIGH"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["result"][0]["name"] == "Importante"


async def test_admin_list_todos_filter_by_created_after(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    await TodoDBService(session).create_todo(
        TodoCreate(name="Antiga"), user.uuid_
    )

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
        params={"createdAfter": "2099-01-01T00:00:00Z"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []


async def test_admin_list_todos_filter_by_created_before(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    await TodoDBService(session).create_todo(
        TodoCreate(name="Futura"), user.uuid_
    )

    response = await client.get(
        "/admin/todos",
        headers={"Authorization": f"Bearer {token}"},
        params={"createdBefore": "2020-01-01T00:00:00Z"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []


# =============================
# GET /admin/todos/{todo_uuid}
# =============================


async def test_admin_get_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])
    admin = await UserDBService(session).get_user_by(email=ADMIN_DATA["email"])
    assert admin is not None

    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Todo admin"), admin.uuid_
    )

    response = await client.get(
        f"/admin/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Todo admin"


async def test_admin_get_todo_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.get(
        f"/admin/todos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# DELETE /admin/todos/{todo_uuid}
# =============================


async def test_admin_delete_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    await _create_user(session, USER_DATA)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Todo para deletar"), user.uuid_
    )

    response = await client.delete(
        f"/admin/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    found = await TodoDBService(session).get_todo_by_uuid_admin(todo.uuid_)
    assert found is None


async def test_admin_delete_todo_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await _create_user(session, ADMIN_DATA, is_superuser=True)
    token = await _login(client, ADMIN_DATA["email"], ADMIN_DATA["password"])

    response = await client.delete(
        f"/admin/todos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
