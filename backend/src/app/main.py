import logging
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from rich.logging import RichHandler

from app.api import admin_router, auth_router, todo_router, user_router
from app.core.settings import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)

logger = logging.getLogger("app")

app = FastAPI()


class Health(BaseModel):
    status: Literal["ok"]


@app.get("/health")
def health() -> Health:
    return {"status": "ok"}


app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=todo_router)
app.include_router(router=admin_router)
