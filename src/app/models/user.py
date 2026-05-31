import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, override

from sqlalchemy import DateTime, Dialect, String, func, types
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class UUIDType(types.TypeDecorator[uuid.UUID]):
    """UUID nativo no Postgres, VARCHAR(36) no SQLite (testes)."""

    impl = types.String(36)
    cache_ok = True

    @override
    def load_dialect_impl(self, dialect: Dialect) -> types.TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    @override
    def process_bind_param(
        self, value: uuid.UUID | None, dialect: Dialect
    ) -> str | uuid.UUID | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value)

    @override
    def process_result_value(
        self, value: str | uuid.UUID | None, dialect: Dialect
    ) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid_: Mapped[uuid.UUID] = mapped_column(UUIDType, unique=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, native_enum=False), default=UserStatus.ACTIVE
    )
    is_superuser: Mapped[bool] = mapped_column(default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
