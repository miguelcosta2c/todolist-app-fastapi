import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

# =============================
# User Schemas
# =============================


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    uuid_: uuid.UUID
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# =============================
# Token Schemas
# =============================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
