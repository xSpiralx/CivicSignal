import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SignInRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AccountView(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    roles: list[str]
    permissions: list[str]
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class SessionView(BaseModel):
    account: AccountView
    csrf_token: str
    expires_at: datetime
    session_id: uuid.UUID
    created_at: datetime


class AccountCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=14, max_length=256)
    roles: list[str] = Field(min_length=1, max_length=5)


class AccountUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    roles: list[str] | None = Field(default=None, min_length=1, max_length=5)


class PasswordReplace(BaseModel):
    password: str = Field(min_length=14, max_length=256)


class SafeSessionView(BaseModel):
    id: uuid.UUID
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    current: bool
