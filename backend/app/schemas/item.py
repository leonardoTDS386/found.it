"""DTOs de item: o que entra e o que sai da API."""

from datetime import date, time

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from app.models.item import ItemBase, StatusItem, TipoRegistro


def _data_nao_futura(valor: date | None) -> date | None:
    if valor is not None and valor > date.today():
        raise ValueError("A data não pode ser futura.")
    return valor


# ---------- Entrada ----------
class ItemCreate(ItemBase):
    """Cadastro (POST). Herda nome, descricao, local, data e horario."""
    tipo_id: int

    @field_validator("data")
    @classmethod
    def data_valida(cls, valor):
        return _data_nao_futura(valor)


class ItemUpdate(SQLModel):
    """Edição (PUT). Todos os campos são opcionais: só muda o que for enviado."""
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, min_length=1, max_length=1000)
    local: str | None = Field(default=None, min_length=1, max_length=200)
    data: date | None = None
    horario: time | None = None
    tipo_id: int | None = None

    @field_validator("data")
    @classmethod
    def data_valida(cls, valor):
        return _data_nao_futura(valor)


class EntregaRequest(SQLModel):
    """Dados de quem retirou o objeto."""
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr


# ---------- Saída ----------
class TipoResumo(SQLModel):
    id: int
    nome: str


class ItemPublico(ItemBase):
    """Campos que qualquer usuário logado pode ver (busca)."""
    id: int
    status: StatusItem
    tipo: TipoResumo


class ItemResponse(ItemPublico):
    """Visão do dono do item."""
    tipo_registro: TipoRegistro
    data_registro: date
    data_devolucao: date | None = None


class ItemAdminResponse(ItemResponse):
    """Visão do administrador: inclui quem registrou e quem retirou."""
    registrado_por_id: int
    retirado_por_nome: str | None = None
    retirado_por_email: str | None = None