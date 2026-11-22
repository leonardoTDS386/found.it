from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item

class TipoBase(SQLModel):
    nome: str = Field(min_length=2, max_length= 40, description="Nome do tipo de objeto")


class Tipo(TipoBase, table= True):
    """Tabela Tipos"""
    __tablename__ = "tipos"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(min_length=2, max_length=40, unique= True, index= True)

    itens: list["Item"] = Relationship(back_populates="tipo")