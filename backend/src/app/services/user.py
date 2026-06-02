import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from sqlalchemy import desc, select
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
from app.schemas import UserCreate, UserListFilters, UserRequestPassword
from app.services import token

ORDER_FIELDS = {
    "id": User.id,
    "updated_at": User.updated_at,
    "deleted_at": User.deleted_at,
    "username": User.username,
    "email": User.email,
    "created_at": User.created_at,
}


class UserDBService:
    UserFields = Literal["uuid_", "username", "email", "status"]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_users(self, filters: UserListFilters) -> Sequence[User]:
        """
        Retorna todos os usuários cadastrados no banco de dados.

        Returns:
            Lista de usuários persistidos no banco.
            Retorna uma lista vazia caso nenhum usuário exista.
        """

        stmt = select(User)

        if not filters.include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))

        if filters.username:
            stmt = stmt.where(User.username.ilike(f"%{filters.username}%"))

        if filters.email:
            stmt = stmt.where(User.email.ilike(f"%{filters.email}%"))

        if filters.status:
            stmt = stmt.where(User.status == filters.status)

        if filters.is_superuser is not None:
            stmt = stmt.where(User.is_superuser == filters.is_superuser)

        if filters.created_after:
            stmt = stmt.where(User.created_at >= filters.created_after)

        if filters.created_before:
            stmt = stmt.where(User.created_at <= filters.created_before)

        column = ORDER_FIELDS.get(filters.order_by, User.created_at)

        stmt = (
            stmt.order_by(desc(column) if filters.order_desc else column)
            .offset(filters.offset)
            .limit(filters.limit)
        )

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_user_by_uuid(
        self, user_uuid: uuid.UUID, *, only_active: bool = True
    ) -> User | None:
        query = select(User).where(User.uuid_ == user_uuid)

        if only_active:
            query = query.where(User.status == UserStatus.ACTIVE)

        return await self.session.scalar(query)

    async def get_user_by(self, **kwargs: str) -> User | None:
        for field in kwargs:
            if field not in self.UserFields.__args__:
                msg = f"O campo informado é inválido: {field}."
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
        await token.delete_refresh_tokens_from_user(self.session, user)

        user.deleted_at = datetime.now(tz=TIMEZONE)
        user.status = UserStatus.DELETED

        await self.session.commit()

    async def delete_user_with_password(
        self, user: User, data: UserRequestPassword
    ) -> None:
        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError
        await self.delete_user(user)
