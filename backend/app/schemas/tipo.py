from app.models.tipo import TipoBase


class TipoCreate(TipoBase):
    """Cadastro de tipo (POST). Herda 'nome' com as regras de tamanho."""


class TipoResponse(TipoBase):
    id: int


class TipoUso(TipoResponse):
    """Tipo com a quantidade de itens que o usam."""
    quantidade_itens: int