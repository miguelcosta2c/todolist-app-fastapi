from fastapi import status
from httpx import AsyncClient

johndoe = {
    "username": "johndoe",
    "email": "johndoe@email.com",
    "password": "12345678",
}


async def test_root_api(client: AsyncClient):
    response = await client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"msg": "Hello, world!"}


async def test_register_user_api(client: AsyncClient):
    payload = {**johndoe}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "johndoe"  # Isso força a leitura da linha 25


async def test_register_user_api_when_user_already_exists(client: AsyncClient):
    payload = {**johndoe}

    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "User already exists"}


async def test_authenticate_user(client: AsyncClient):
    # Creating user
    payload = {**johndoe}
    await client.post("/auth/register", json=payload)

    data = {"username": payload["email"], "password": payload["password"]}

    response = await client.post("/auth/token", data=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"  # noqa: S105


async def test_login_invalid_credentials(client: AsyncClient):
    login_data = {"username": "wronguser", "password": "wrongpassword"}
    response = await client.post("/auth/token", data=login_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid credentials"
