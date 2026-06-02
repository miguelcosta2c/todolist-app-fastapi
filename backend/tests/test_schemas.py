import pytest
from pydantic import ValidationError

from app.schemas import UserCreate, UserUpdate


class TestUserCreateValidateUsername:
    async def test_starts_with_underscore(self) -> None:
        with pytest.raises(ValidationError, match="não pode começar ou terminar"):
            UserCreate(
                username="_miguel",
                email="test@test.com",
                password="Senha123@",
                confirm_password="Senha123@",
            )

    async def test_ends_with_underscore(self) -> None:
        with pytest.raises(ValidationError, match="não pode começar ou terminar"):
            UserCreate(
                username="miguel_",
                email="test@test.com",
                password="Senha123@",
                confirm_password="Senha123@",
            )


class TestUserCreateValidatePassword:
    async def test_missing_uppercase(self) -> None:
        with pytest.raises(ValidationError, match="maiúscula"):
            UserCreate(
                username="miguel",
                email="test@test.com",
                password="senha123@",
                confirm_password="senha123@",
            )

    async def test_missing_lowercase(self) -> None:
        with pytest.raises(ValidationError, match="minúscula"):
            UserCreate(
                username="miguel",
                email="test@test.com",
                password="SENHA123@",
                confirm_password="SENHA123@",
            )

    async def test_missing_digit(self) -> None:
        with pytest.raises(ValidationError, match="número"):
            UserCreate(
                username="miguel",
                email="test@test.com",
                password="Senha@@@!",
                confirm_password="Senha@@@!",
            )

    async def test_missing_special_char(self) -> None:
        with pytest.raises(ValidationError, match="caractere especial"):
            UserCreate(
                username="miguel",
                email="test@test.com",
                password="Senha1234",
                confirm_password="Senha1234",
            )


class TestUserUpdateValidateNewPassword:
    async def test_missing_uppercase(self) -> None:
        with pytest.raises(ValidationError, match="maiúscula"):
            UserUpdate(
                new_password="senha123@",
            )

    async def test_missing_lowercase(self) -> None:
        with pytest.raises(ValidationError, match="minúscula"):
            UserUpdate(
                new_password="SENHA123@",
            )

    async def test_missing_digit(self) -> None:
        with pytest.raises(ValidationError, match="número"):
            UserUpdate(
                new_password="Senha@@@!",
            )

    async def test_missing_special_char(self) -> None:
        with pytest.raises(ValidationError, match="caractere especial"):
            UserUpdate(
                new_password="Senha1234",
            )

    async def test_none_is_valid(self) -> None:
        user_update = UserUpdate()
        assert user_update.new_password is None

    async def test_none_explicitly(self) -> None:
        user_update = UserUpdate(new_password=None)
        assert user_update.new_password is None
