from datetime import date, time
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.tipo import Tipo
    from app.models.usuario import Usuario
    from app.models.solicitacao import SolicitacaoDevolucao


class StatusItem(str, Enum):
    perdido = "perdido"
    achado = "achado"
    entregue = "entregue"


class TipoRegistro(str, Enum):
    perdido = "perdido" # Registrado por usuario
    achado = "achado" # Registrado por admin


class ItemBase(SQLModel):
    nome: str = Field(min_length=2, max_length=120, description="Nome do Objeto")
    descricao: str = Field(min_length=1, max_length=1000)
    local: str = Field(min_length=1, max_length=200)
    data: date = Field(description="Data em que foi perdido ou achado")
    horario: time = Field(description="Horário aproximado")


class Item(ItemBase, table=True):
    """Tabela 'itens' (achados, perdidos, entregues)"""
    __tablename__ = "itens"

    id: int | None = Field(default=None, primary_key = True)
    status: StatusItem = Field(default=StatusItem.perdido)
    tipo_registro: TipoRegistro
    data_registro: date = Field(default_factory=date.today)
    data_devolucao: date | None = None
    retirado_por_nome: str | None = Field(default=None, max_length=120)
    retirado_por_email: str | None = Field(default=None, max_length=120)

    # Chaves estrangeiras
    tipo_id: int = Field(foreign_key="tipos.id")
    registrado_por_id: int = Field(foreign_key="usuarios.id")

    tipo: "Tipo" = Relationship(back_populates="itens")
    usuario: "Usuario" = Relationship(back_populates="itens")
    solicitacoes: list["SolicitacaoDevolucao"] = Relationship(back_populates="item", cascade_delete=True)