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
        console.print("[green]Create Superuser[/]")
        console.print("[green]=[/]" * 100)

        data = {
            "username": Prompt.ask("[cyan]Username[/]"),
            "email": Prompt.ask("[cyan]E-mail[/]"),
            "password": Prompt.ask(
                "[cyan]Password[/]",
                password=True,
            ),
            "confirm_password": Prompt.ask(
                "[cyan]Confirm password[/]",
                password=True,
            ),
        }

        try:
            user = UserCreate.model_validate(data)
            break

        except ValidationError as err:
            console.print("\n[red]Validation error:[/]\n")

            for error in err.errors():
                console.print(f"[red]- {error['msg']}[/]")

    console.print()
    console.print("Creating superuser...")

    try:
        asyncio.run(_create_superuser(data=user))
    except UserAlreadyExistsError:
        console.print("\n[red]Integrity error:[/]\n")

        console.print(
            "[red]- Um erro de integridade do banco de dados ocorreu, verifique"
            " se o usuario ja nao existe na base de dados[/]"
        )
    else:
        console.print()
        console.print("Superuser created")


def server() -> None:
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
