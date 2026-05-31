from typing import Any

from fastapi import FastAPI

from app.api import auth_router, user_router

app = FastAPI()


@app.get("/health")
def health() -> Any:
    return {"status": "ok"}


app.include_router(router=auth_router)
app.include_router(router=user_router)
