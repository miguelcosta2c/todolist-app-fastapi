import logging
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rich.logging import RichHandler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import admin_router, auth_router, todo_router, user_router
from app.core.limiter import limiter
from app.core.settings import settings

# Logging

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)

logger = logging.getLogger("app")

# App

app = FastAPI()

# Rate limiting

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Permite apenas os domínios da lista
    allow_credentials=True,  # Permite cookies e headers de autenticação
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os headers
)

# Health check


class Health(BaseModel):
    status: Literal["ok"]


@app.get("/health")
async def health() -> Health:
    return {"status": "ok"}


# Routers

app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=todo_router)
app.include_router(router=admin_router)
