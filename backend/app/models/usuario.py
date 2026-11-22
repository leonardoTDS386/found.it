from datetime import date 
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.token_refresh import TokenRefresh

class Perfil(str, Enum):
    usuario = "usuario"
    admin = "admin"


class UsuarioBase(SQLModel):
    nome: str = Field(min_length=3, max_length=150, description="Nome completo")
    email: str = Field(max_length=120, description= "E-mail usado no Login")
    cpf: str | None = Field(default=None, max_length=14)
    telefone: str | None = Field(default=None, max_length=20)
    endereco: str | None = Field(default=None, max_length=255)


class Usuario(UsuarioBase, table=True):
    """Tabela 'usuarios'(comum e admin)"""
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key= True)
    email: str = Field(max_length=120, unique= True, index=True)
    senha_hash: str
    perfil: Perfil = Field(default=Perfil.usuario)
    criado_em: date = Field(default_factory=date.today)

    itens: list["Item"] = Relationship(back_populates="usuario")
    tokens: list["TokenRefresh"] = Relationship(
        back_populates="usuario", cascade_delete=True
    )