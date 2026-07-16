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


class SessionView(BaseModel):
    account: AccountView
    csrf_token: str
    expires_at: datetime
