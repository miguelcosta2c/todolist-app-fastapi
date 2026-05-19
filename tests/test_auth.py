import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserCreate, UserPublic
from app.services import auth


class TestSchemas:
    def test_user_create_schema(self):
        user_create = UserCreate(
            username="Miguel",
            email="miguel@email.com",
            password="12345678",  # noqa: S106
        )

        assert user_create.username == "Miguel"
        assert user_create.email == "miguel@email.com"
        assert user_create.password == "12345678"  # noqa: S105

    def test_user_create_schema_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="Miguel",
                email="asdasdasdasd",
                password="12345678",  # noqa: S106
            )

    def test_user_public_schema(self):
        user_public = UserPublic(
            uuid_=uuid.uuid4(),
            username="Miguel",
            email="miguel@email.com",
        )

        assert user_public.username == "Miguel"
        assert user_public.email == "miguel@email.com"


class TestServices:
    @pytest.mark.asyncio
    async def test_create_user_service(self, session: AsyncSession):
        user_create = UserCreate(
            username="johndoe",
            email="johndoe@email.com",
            password="12345678",  # noqa: S106
        )
        user = await auth.create_user(session, user_create)
        assert user is not None

    @pytest.mark.asyncio
    async def test_create_user_service_when_user_already_exists(
        self, session: AsyncSession
    ):
        user_create = UserCreate(
            username="johndoe",
            email="johndoe@email.com",
            password="12345678",  # noqa: S106
        )
        await auth.create_user(session, user_create)
        user = await auth.create_user(session, user_create)

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_service(self, session: AsyncSession):
        user_create = UserCreate(
            username="johndoe",
            email="johndoe@email.com",
            password="12345678",  # noqa: S106
        )
        user = await auth.create_user(session, user_create)

        assert user is not None

        authenticated_user = await auth.authenticate_user(
            session, user.email, "12345678"
        )

        assert authenticated_user is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_service_user_doesnt_exist(
        self, session: AsyncSession
    ):
        authenticated_user = await auth.authenticate_user(
            session, "anyemail@email.com", "12345678"
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_service_with_wrong_password(
        self, session: AsyncSession
    ):
        user_create = UserCreate(
            username="johndoe",
            email="johndoe@email.com",
            password="12345678",  # noqa: S106
        )
        user = await auth.create_user(session, user_create)

        assert user is not None

        authenticated_user = await auth.authenticate_user(
            session, user.email, "wrongpassword"
        )

        assert authenticated_user is None
