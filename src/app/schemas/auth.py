import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

# =============================
# User Schemas
# =============================


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid_: uuid.UUID
    username: str
    email: EmailStr


class UserPrivate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uuid_: uuid.UUID
    username: str
    email: EmailStr
    last_login_at: datetime | None
    created_at: datetime


# =============================
# Token Schemas
# =============================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
