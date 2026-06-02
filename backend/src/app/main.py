from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.api import admin_router, auth_router, user_router

app = FastAPI()


class Health(BaseModel):
    status: Literal["ok"]


@app.get("/health")
def health() -> Health:
    return {"status": "ok"}


app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=admin_router)
