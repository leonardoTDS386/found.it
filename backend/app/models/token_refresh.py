from pydantic import NaiveDatetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class TokenRefresh(SQLModel, table=True):
    """Tabela token refresh, guarda o hash do token"""
    __tablename__ = "tokens_refresh"

    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(unique=True, index=True)
    expira_em: NaiveDatetime
    revogado: bool = Field(default=False)

    usuario_id: int = Field(foreign_key="usuarios.id", ondelete="CASCADE")
    usuario: "Usuario" = Relationship(back_populates="tokens")