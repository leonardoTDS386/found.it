from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field , Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.usuario import Usuario


class SolicitacaoDevolucao(SQLModel, table=True):
    """Pedido de um usuário para retirar um item achado"""
    __tablename__ = "solicitacoes_devolucao"
    # Cada usuário só pode ter um pedido por item
    __table_args__ = (UniqueConstraint("item_id", "usuario_id"),)

    id: int | None = Field(default=None, primary_key=True)
    criada_em: date = Field(default_factory=date.today)

    item_id: int = Field(foreign_key="itens.id", ondelete="CASCADE")
    usuario_id: int = Field(foreign_key="usuarios.id", ondelete="CASCADE")

    item: "Item" = Relationship(back_populates="solicitacoes")
    usuario: "Usuario" = Relationship()