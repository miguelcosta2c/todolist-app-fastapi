import asyncio

import uvicorn
from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Prompt

from app.core.settings import settings
from app.db import AsyncSessionLocal
from app.exc import UserAlreadyExistsError
from app.schemas import UserCreate
from app.services.user import UserDBService

console = Console()


async def _create_superuser(data: UserCreate) -> None:
    async with AsyncSessionLocal() as session:
        await UserDBService(session).create_user(data=data, is_superuser=True)


def create_superuser() -> None:
    while True:
        console.print("[green]=[/]" * 100)
        console.print("[green]Criação de Superusuário[/]")
        console.print("[green]=[/]" * 100)

        data = {
            "username": Prompt.ask("[cyan]Nome de usuário[/]"),
            "email": Prompt.ask("[cyan]E-mail[/]"),
            "password": Prompt.ask(
                "[cyan]Senha[/]",
                password=True,
            ),
            "confirm_password": Prompt.ask(
                "[cyan]Confirmar senha[/]",
                password=True,
            ),
        }

        try:
            user = UserCreate.model_validate(data)
            break

        except ValidationError as err:
            console.print("\n[red]Erro de validação:[/]\n")

            for error in err.errors():
                console.print(f"[red]- {error['msg']}[/]")

    console.print()
    console.print("Criando superusuário...")

    try:
        asyncio.run(_create_superuser(data=user))
    except UserAlreadyExistsError:
        console.print("\n[red]Erro de integridade:[/]\n")

        console.print(
            "[red]- Ocorreu um erro de integridade no banco de dados."
            " Verifique se o usuário já não existe na base de dados.[/]"
        )
    else:
        console.print()
        console.print("Superusuário criado com sucesso.")


def server() -> None:
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
