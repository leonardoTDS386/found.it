from datetime import date

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from app.models.usuario import Perfil, UsuarioBase


class UsuarioCreate(SQLModel):
    """Dados recebidos no cadastro (POST)."""
    nome: str = Field(min_length=3, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    cpf: str | None = Field(default=None, max_length=14)
    telefone: str | None = Field(default=None, max_length=20)
    endereco: str | None = Field(default=None, max_length=255)

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, valor: str) -> str:
        if not any(c.isalpha() for c in valor) or not any(c.isdigit() for c in valor):
            raise ValueError("A senha deve ter letras e números.")
        return valor


class UsuarioResponse(UsuarioBase):
    """O que a API devolve."""
    id: int
    perfil: Perfil
    criado_em: date