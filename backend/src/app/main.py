import logging
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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

app = FastAPI(
    title="TODO LIST APP",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

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

# Other Middlewares

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)


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
