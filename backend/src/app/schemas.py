import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.user import UserStatus

# =============================
# API Schemas
# =============================


class Message(BaseModel):
    message: str


# =============================
# User Schemas
# =============================


class UserListFilters(BaseModel):
    username: str | None = None
    email: str | None = None
    status: UserStatus | None = None
    is_superuser: bool | None = None

    created_after: datetime | None = None
    created_before: datetime | None = None

    include_deleted: bool = False

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    order_by: Literal[
        "id",
        "username",
        "created_at",
        "updated_at",
        "deleted_at",
    ] = "created_at"

    order_desc: bool = True


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    confirm_password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if value.startswith("_") or value.endswith("_"):
            msg = "Username não pode começar ou terminar com _"
            raise ValueError(msg)

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value):
            msg = "A senha deve conter pelo menos uma letra maiúscula"
            raise ValueError(msg)

        if not any(c.islower() for c in value):
            msg = "A senha deve conter pelo menos uma letra minúscula"
            raise ValueError(msg)

        if not any(c.isdigit() for c in value):
            msg = "A senha deve conter pelo menos um número"
            raise ValueError(msg)

        if not any(not c.isalnum() for c in value):
            msg = "A senha deve conter pelo menos um caractere especial"
            raise ValueError(msg)

        return value

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.password != self.confirm_password:
            msg = "Senhas não são iguais"
            raise ValueError(msg)

        return self


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    email: EmailStr | None = None
    password: str | None = None
    new_password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if not any(c.isupper() for c in value):
            msg = "A senha deve conter pelo menos uma letra maiúscula"
            raise ValueError(msg)

        if not any(c.islower() for c in value):
            msg = "A senha deve conter pelo menos uma letra minúscula"
            raise ValueError(msg)

        if not any(c.isdigit() for c in value):
            msg = "A senha deve conter pelo menos um número"
            raise ValueError(msg)

        if not any(not c.isalnum() for c in value):
            msg = "A senha deve conter pelo menos um caractere especial"
            raise ValueError(msg)

        return value


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
    status: UserStatus
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


class UserRequestPassword(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.password != self.confirm_password:
            msg = "Senhas nao sao iguais"
            raise ValueError(msg)

        return self


class UserList(BaseModel):
    result: list[UserSchema]
    total: int
    offset: int
    limit: int


# =============================
# Token Schemas
# =============================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
