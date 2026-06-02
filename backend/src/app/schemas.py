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
from pydantic.alias_generators import to_camel

from app.models.todo import TodoPriority, TodoStatus
from app.models.user import UserStatus


class AliasSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ResponseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# =============================
# API Schemas
# =============================


class Message(AliasSchema):
    message: str


# =============================
# User Schemas
# =============================


class UserListFilters(AliasSchema):
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


class UserCreate(InputSchema):
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
            msg = (
                "O nome de usuário não pode começar ou terminar com o caractere"
                " underscore (_)."
            )
            raise ValueError(msg)

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value):
            msg = "A senha deve conter pelo menos uma letra maiúscula."
            raise ValueError(msg)

        if not any(c.islower() for c in value):
            msg = "A senha deve conter pelo menos uma letra minúscula."
            raise ValueError(msg)

        if not any(c.isdigit() for c in value):
            msg = "A senha deve conter pelo menos um número."
            raise ValueError(msg)

        if not any(not c.isalnum() for c in value):
            msg = "A senha deve conter pelo menos um caractere especial."
            raise ValueError(msg)

        return value

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.password != self.confirm_password:
            msg = "As senhas informadas não são iguais."
            raise ValueError(msg)

        return self


class UserUpdate(InputSchema):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
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
            msg = "A senha deve conter pelo menos uma letra maiúscula."
            raise ValueError(msg)

        if not any(c.islower() for c in value):
            msg = "A senha deve conter pelo menos uma letra minúscula."
            raise ValueError(msg)

        if not any(c.isdigit() for c in value):
            msg = "A senha deve conter pelo menos um número."
            raise ValueError(msg)

        if not any(not c.isalnum() for c in value):
            msg = "A senha deve conter pelo menos um caractere especial."
            raise ValueError(msg)

        return value


class UserPublic(ResponseSchema):
    uuid_: uuid.UUID
    username: str
    email: EmailStr


class UserPrivate(ResponseSchema):
    uuid_: uuid.UUID
    username: str
    email: EmailStr
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime


class UserSchema(ResponseSchema):
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


class UserRequestPassword(InputSchema):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.password != self.confirm_password:
            msg = "As senhas informadas não são iguais."
            raise ValueError(msg)

        return self


class UserList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class RefreshTokenSchema(ResponseSchema):
    id: int
    user_uuid: uuid.UUID
    refresh_token: str
    is_revoked: bool
    expires_at: datetime
    created_at: datetime


class RefreshTokensListFilter(AliasSchema):
    id: int | None = None
    user_uuid: uuid.UUID | None = None
    is_revoked: bool | None = None

    expires_after: datetime | None = None
    expires_before: datetime | None = None

    created_after: datetime | None = None
    created_before: datetime | None = None

    offset: int = 0
    limit: int = 10

    order_by: Literal["id", "user_uuid", "is_revoked", "expires_at", "created_at"] = (
        "created_at"
    )
    order_desc: bool = True


class RefreshTokensList(AliasSchema):
    result: list[RefreshTokenSchema]
    total: int
    offset: int
    limit: int


# =============================
# Todos Schemas
# =============================


class TodoListFilters(AliasSchema):
    status: TodoStatus | None = None
    priority: TodoPriority | None = None

    created_after: datetime | None = None
    created_before: datetime | None = None

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    order_by: Literal[
        "created_at",
        "updated_at",
        "due_date",
        "priority",
        "status",
    ] = "created_at"

    order_desc: bool = True


class TodoCreate(InputSchema):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    priority: TodoPriority = TodoPriority.NONE
    due_date: datetime | None = None


class TodoUpdate(InputSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: TodoStatus | None = None
    priority: TodoPriority | None = None
    due_date: datetime | None = None


class TodoResponse(ResponseSchema):
    uuid_: uuid.UUID
    name: str
    description: str
    status: TodoStatus
    priority: TodoPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime


class TodoSchema(ResponseSchema):
    id: int
    uuid_: uuid.UUID
    name: str
    description: str
    status: TodoStatus
    priority: TodoPriority
    due_date: datetime | None
    user_uuid: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TodoList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    result: list[TodoSchema]
    total: int
    offset: int
    limit: int
