from pydantic import EmailStr
from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    email: EmailStr
    senha: str


class RefreshRequest(SQLModel):
    refresh_token: str


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"