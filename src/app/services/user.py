from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
)
from app.exc import UserAlreadyExistsError
from app.models import User
from app.schemas import UserCreate, UserUpdate


class UserDBService:
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

    async def update_user(self, user: User, data: UserUpdate) -> User:
        """
        Atualiza parcialmente um usuário.
        Apenas os campos enviados serão alterados.
        """

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        updated = False
        for field, value in update_data.items():
            if getattr(user, field) != value:
                updated = True
                setattr(user, field, value)

        if updated:
            await self.session.commit()
            await self.session.refresh(user)

        return user
