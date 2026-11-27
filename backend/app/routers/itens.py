"""CRUD de itens (usuário e administrador)."""

import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from app.database import get_session
from app.dependencies import usuario_atual
from app.models import Item, Perfil, SolicitacaoDevolucao, StatusItem, Tipo, TipoRegistro, Usuario
from app.schemas.item import ItemCreate, ItemPublico, ItemResponse, ItemUpdate


router = APIRouter(prefix="/api/itens", tags=["Itens"])


def _normalizar(texto: str) -> str:
    """Ignora acentos e maiúsculas ('Óculos' encontra 'oculos')."""
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


def obter_item_ou_404(item_id: int, session: Session) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item


def _eh_dono_ou_admin(item: Item, usuario: Usuario) -> bool:
    return usuario.perfil == Perfil.admin or item.registrado_por_id == usuario.id


def verificar_permissao_de_alteracao(item: Item, usuario: Usuario) -> None:
    """Admin altera qualquer item; usuário, só os seus. Entregues ficam congelados."""
    if not _eh_dono_ou_admin(item, usuario):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Você só pode alterar os itens registrados por você."
        )
    if item.status == StatusItem.entregue:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Itens já entregues não podem ser alterados."
        )


def _exigir_tipo_existente(tipo_id: int, session: Session) -> None:
    if session.get(Tipo, tipo_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Tipo de objeto não encontrado.")


@router.get("", response_model=list[ItemPublico])
def buscar_itens(
    nome: str | None = None,
    tipo_id: int | None = None,
    local: str | None = None,
    data: date | None = None,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """Busca de itens. Sem filtros, devolve todos (menos os entregues)."""
    consulta = select(Item).where(Item.status != StatusItem.entregue)
    if tipo_id is not None:
        consulta = consulta.where(Item.tipo_id == tipo_id)
    if data is not None:
        consulta = consulta.where(Item.data == data)
    consulta = consulta.order_by(col(Item.data_registro).desc(), col(Item.id).desc())

    itens = session.exec(consulta).all()
    if nome:
        itens = [i for i in itens if _normalizar(nome) in _normalizar(i.nome)]
    if local:
        itens = [i for i in itens if _normalizar(local) in _normalizar(i.local)]
    return itens


@router.get("/meus", response_model=list[ItemResponse])
def meus_itens(
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """Histórico de quem está logado."""
    consulta = (
        select(Item)
        .where(Item.registrado_por_id == usuario.id)
        .order_by(col(Item.data_registro).desc(), col(Item.id).desc())
    )
    return session.exec(consulta).all()


@router.get("/{item_id}", response_model=ItemPublico)
def detalhar_item(
    item_id: int,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    item = obter_item_ou_404(item_id, session)
    if item.status == StatusItem.entregue and not _eh_dono_ou_admin(item, usuario):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item


@router.post("", response_model=ItemResponse, status_code=201)
def cadastrar_item(
    dados: ItemCreate,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """Usuário cadastra item PERDIDO; administrador cadastra item ACHADO."""
    _exigir_tipo_existente(dados.tipo_id, session)

    eh_admin = usuario.perfil == Perfil.admin
    item = Item(
        **dados.model_dump(),
        status=StatusItem.achado if eh_admin else StatusItem.perdido,
        tipo_registro=TipoRegistro.achado if eh_admin else TipoRegistro.perdido,
        registrado_por_id=usuario.id,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def editar_item(
    item_id: int,
    dados: ItemUpdate,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    item = obter_item_ou_404(item_id, session)
    verificar_permissao_de_alteracao(item, usuario)

    campos = dados.model_dump(exclude_unset=True, exclude_none=True)
    if "tipo_id" in campos:
        _exigir_tipo_existente(campos["tipo_id"], session)
    for campo, valor in campos.items():
        setattr(item, campo, valor)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def excluir_item(
    item_id: int,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    item = obter_item_ou_404(item_id, session)
    verificar_permissao_de_alteracao(item, usuario)
    session.delete(item)
    session.commit()


@router.post("/{item_id}/solicitar", response_model=ItemPublico)
def solicitar_devolucao(
    item_id: int,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """O usuário diz que o item achado é dele. O pedido é registrado uma única vez."""
    if usuario.perfil == Perfil.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Administradores não solicitam devolução."
        )

    item = obter_item_ou_404(item_id, session)
    if item.status != StatusItem.achado:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Só é possível solicitar a devolução de itens achados.",
        )

    pedido_existente = session.exec(
        select(SolicitacaoDevolucao).where(
            SolicitacaoDevolucao.item_id == item.id,
            SolicitacaoDevolucao.usuario_id == usuario.id,
        )
    ).first()

    if pedido_existente is None:
        session.add(SolicitacaoDevolucao(item_id=item.id, usuario_id=usuario.id))
        session.commit()
        session.refresh(item)
    return item


@router.get("/solicitacoes/minhas", response_model=list[ItemPublico])
def minhas_solicitacoes(
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """Itens achados que o usuário logado já solicitou."""
    consulta = (
        select(Item)
        .join(SolicitacaoDevolucao, SolicitacaoDevolucao.item_id == Item.id)
        .where(
            SolicitacaoDevolucao.usuario_id == usuario.id,
            Item.status == StatusItem.achado,
        )
        .order_by(col(Item.id).desc())
    )
    return session.exec(consulta).all()


@router.delete("/{item_id}/solicitar", status_code=204)
def cancelar_solicitacao(
    item_id: int,
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    """O usuário cancela o próprio pedido. Nunca consegue cancelar o de outra pessoa."""
    pedido = session.exec(
        select(SolicitacaoDevolucao).where(
            SolicitacaoDevolucao.item_id == item_id,
            SolicitacaoDevolucao.usuario_id == usuario.id,
        )
    ).first()
    if pedido is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Você não tem solicitação para esse item."
        )
    session.delete(pedido)
    session.commit()