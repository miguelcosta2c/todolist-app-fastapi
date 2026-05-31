from datetime import UTC
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    HOST: str = Field(init=False)
    PORT: int = Field(init=False)
    DATABASE_URL: str = Field(init=False)
    ALEMBIC_DATABASE_URL: str = Field(init=False)
    SECRET_KEY: str = Field(init=False)
    ALGORITHM: str = Field(init=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(init=False)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(init=False)
    ENVIRONMENT: Literal["development", "production"] = Field(init=False)

    @property
    def DEBUG(self) -> bool:  # noqa: N802
        return self.ENVIRONMENT == "development"

    @property
    def IS_SECURE(self) -> bool:  # noqa: N802
        return not self.DEBUG


TIMEZONE = UTC

settings = _Settings()
