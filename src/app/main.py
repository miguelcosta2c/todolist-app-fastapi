from fastapi import FastAPI

from app.api import auth_router

app = FastAPI()
app.include_router(router=auth_router)
