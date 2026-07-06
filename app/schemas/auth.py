"""Pydantic schemas for auth endpoints.

CamelModel serializes JSON with camelCase keys (e.g. accessToken) while
keeping snake_case field names in Python code.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,  # Accept both camelCase and snake_case on input
        ser_json_by_alias=True,  # Emit camelCase in JSON responses
    )


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(CamelModel):
    refresh_token: str = Field(min_length=1)


class TokenPairResponse(CamelModel):
    access_token: str
    refresh_token: str
    expires_in: int


class UserPayload(CamelModel):
    id: str
    email: str
    roles: List[str]


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8)
    roles: Optional[List[str]] = None
