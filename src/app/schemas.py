import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from app.models.user import UserStatus

# =============================
# API Schemas
# =============================


class Message(BaseModel):
    message: str


# =============================
# User Schemas
# =============================


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.password != self.confirm_password:
            msg = "Senhas nao sao iguais"
            raise ValueError(msg)

        return self


class UserUpdate(BaseModel):
    username: str | None
    email: str | None


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


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid_: uuid.UUID
    username: str
    email: EmailStr
    password_hash: str
    status: UserStatus
    is_superuser: bool
    last_login_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


# =============================
# Token Schemas
# =============================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
