import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
)
from app.core.settings import TIMEZONE
from app.exc import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.models import User
from app.models.user import UserStatus
from app.schemas import UserCreate, UserRequestPassword
from app.services.auth import delete_refresh_tokens_from_user


class UserDBService:
    UserFields = Literal["uuid_", "username", "email", "status"]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_users(self, offset: int, limit: int) -> Sequence[User]:
        """
        Retorna todos os usuários cadastrados no banco de dados.

        Returns:
            Lista de usuários persistidos no banco.
            Retorna uma lista vazia caso nenhum usuário exista.
        """

        result = await self.session.scalars(select(User).offset(offset).limit(limit))
        return result.all()

    async def get_user_by_uuid(
        self, user_uuid: uuid.UUID, *, only_active: bool = True
    ) -> User | None:
        query = select(User).where(User.uuid_ == user_uuid)

        if only_active:
            query.where(User.status == UserStatus.ACTIVE)

        return await self.session.scalar(query)

    async def get_user_by(self, **kwargs: str) -> User | None:
        for field in kwargs:
            if field not in self.UserFields.__args__:
                msg = f"Campo inválido: {field}"
                raise ValueError(msg)

        return await self.session.scalar(
            select(User).where(
                *(getattr(User, field) == value for field, value in kwargs.items())
            )
        )

    async def create_user(
        self, data: UserCreate, *, is_superuser: bool = False
    ) -> User:
        """
        Cria e persiste um novo usuário no banco de dados.

        O método:
        - cria uma instância de `User`;
        - gera o hash da senha informada;
        - adiciona o usuário na sessão do SQLAlchemy;
        - realiza o commit da transação;
        - atualiza a instância com os dados persistidos no banco.

        Args:
            data: Dados necessários para criação do usuário.

        Returns:
            A instância do usuário criada e persistida.

        Raises:
            UserAlreadyExistsError:
                Lançado quando já existe um usuário com o mesmo
                email ou username.

            IntegrityError:
                Capturado internamente quando ocorre violação
                de restrição única no banco de dados.
        """

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            is_superuser=is_superuser,
        )

        self.session.add(user)

        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            raise UserAlreadyExistsError from err

        await self.session.refresh(user)

        return user

    async def update_user(self, user: User, data: dict[str, str]) -> User:
        """
        Atualiza parcialmente um usuário.
        Apenas os campos enviados serão alterados.
        """

        if "new_password" in data:
            data["password_hash"] = hash_password(data.pop("new_password"))

        updated = False
        for field, value in data.items():
            if getattr(user, field) != value:
                updated = True
                setattr(user, field, value)

        if updated:
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def delete_user(self, user: User) -> None:
        await delete_refresh_tokens_from_user(self.session, user)

        user.deleted_at = datetime.now(tz=TIMEZONE)
        user.status = UserStatus.DELETED

        await self.session.commit()

    async def delete_user_with_password(
        self, user: User, data: UserRequestPassword
    ) -> None:
        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError
        await self.delete_user(user)
