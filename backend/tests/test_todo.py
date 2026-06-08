import uuid
from datetime import datetime
from typing import Any

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import TIMEZONE
from app.models.todo import TodoPriority, TodoStatus
from app.schemas import TodoCreate, TodoListFilters, UserCreate
from app.services.todo import TodoDBService
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


async def get_access_token(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


# =============================
# GET /todos/
# =============================


async def test_list_todos_empty(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []
    assert body["total"] == 0


async def test_list_todos_with_items(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    await TodoDBService(session).create_todo(
        TodoCreate(name="Minha tarefa"), user.uuid_
    )

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["total"] == 1
    assert body["result"][0]["name"] == "Minha tarefa"


async def test_list_todos_filter_by_status(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    todo1 = await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa em progresso"), user.uuid_,
    )
    await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa concluida"), user.uuid_,
    )
    await TodoDBService(session).update_todo(
        todo1, {"status": TodoStatus.IN_PROGRESS}
    )

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": "IN_PROGRESS"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["result"][0]["name"] == "Tarefa em progresso"


async def test_list_todos_filter_by_priority(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa importante", priority=TodoPriority.HIGH),
        user.uuid_,
    )
    await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa normal"),
        user.uuid_,
    )

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
        params={"priority": "HIGH"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["result"]) == 1
    assert body["result"][0]["name"] == "Tarefa importante"


async def test_list_todos_filter_by_created_after(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa antiga"), user.uuid_
    )

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
        params={"created_after": "2099-01-01T00:00:00Z"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []


async def test_list_todos_filter_by_created_before(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa futura"), user.uuid_
    )

    response = await client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
        params={"created_before": "2020-01-01T00:00:00Z"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["result"] == []


# =============================
# POST /todos/
# =============================


async def test_create_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.post(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Nova tarefa"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["name"] == "Nova tarefa"
    assert body["description"] == ""
    assert body["status"] == "TODO"
    assert body["priority"] == "NONE"
    assert "uuid_" in body


async def test_create_todo_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/todos/",
        json={"name": "Tarefa sem token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================
# GET /todos/{todo_uuid}
# =============================


async def test_get_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa especifica"), user.uuid_
    )

    response = await client.get(
        f"/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Tarefa especifica"


async def test_get_todo_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.get(
        f"/todos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# PATCH /todos/{todo_uuid}
# =============================


async def test_patch_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa original"), user.uuid_
    )

    response = await client.patch(
        f"/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Tarefa atualizada"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Tarefa atualizada"


async def test_patch_todo_no_changes(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa original"), user.uuid_
    )

    response = await client.patch(
        f"/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Tarefa original"},
    )

    assert response.status_code == status.HTTP_200_OK


async def test_patch_todo_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.patch(
        f"/todos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Nao importa"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# DELETE /todos/{todo_uuid}
# =============================


async def test_delete_todo_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None

    todo = await TodoDBService(session).create_todo(
        TodoCreate(name="Tarefa para deletar"), user.uuid_
    )

    response = await client.delete(
        f"/todos/{todo.uuid_}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's really gone
    found = await TodoDBService(session).get_todo_by_uuid(todo.uuid_, user.uuid_)
    assert found is None


async def test_delete_todo_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    await create_user(session)
    token = await get_access_token(client, USER_DATA["email"], USER_DATA["password"])

    response = await client.delete(
        f"/todos/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================
# count_todos filter branches
# =============================


async def test_count_todos_default(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await TodoDBService(session).create_todo(TodoCreate(name="Tarefa A"), user.uuid_)

    total = await TodoDBService(session).count_todos(TodoListFilters())
    assert total == 1


async def test_count_todos_filter_by_search(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await TodoDBService(session).create_todo(TodoCreate(name="Comprar pao"), user.uuid_)
    await TodoDBService(session).create_todo(TodoCreate(name="Estudar Python"), user.uuid_)

    total = await TodoDBService(session).count_todos(
        TodoListFilters(search="pao")
    )
    assert total == 1


async def test_count_todos_filter_by_user_uuid(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")
    user1 = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    user2 = await UserDBService(session).get_user_by(email="outro@email.com")
    assert user1 is not None and user2 is not None
    await TodoDBService(session).create_todo(TodoCreate(name="Tarefa 1"), user1.uuid_)
    await TodoDBService(session).create_todo(TodoCreate(name="Tarefa 2"), user2.uuid_)

    total = await TodoDBService(session).count_todos(
        TodoListFilters(user_uuid=user1.uuid_)
    )
    assert total == 1


# =============================
# get_all_todos filter branches
# =============================


async def test_get_all_todos_filter_by_search(session: AsyncSession) -> None:
    await create_user(session)
    user = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    assert user is not None
    await TodoDBService(session).create_todo(TodoCreate(name="Comprar pao"), user.uuid_)
    await TodoDBService(session).create_todo(TodoCreate(name="Estudar Python"), user.uuid_)

    todos = await TodoDBService(session).get_all_todos(
        TodoListFilters(search="pao")
    )
    assert len(todos) == 1


async def test_get_all_todos_filter_by_user_uuid(session: AsyncSession) -> None:
    await create_user(session)
    await create_user(session, username="outro", email="outro@email.com")
    user1 = await UserDBService(session).get_user_by(email=USER_DATA["email"])
    user2 = await UserDBService(session).get_user_by(email="outro@email.com")
    assert user1 is not None and user2 is not None
    await TodoDBService(session).create_todo(TodoCreate(name="Tarefa 1"), user1.uuid_)
    await TodoDBService(session).create_todo(TodoCreate(name="Tarefa 2"), user2.uuid_)

    todos = await TodoDBService(session).get_all_todos(
        TodoListFilters(user_uuid=user1.uuid_)
    )
    assert len(todos) == 1
