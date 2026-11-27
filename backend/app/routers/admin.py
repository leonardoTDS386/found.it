"""Rotas exclusivas do administrador."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, func, select

from app.database import get_session
from app.dependencies import exigir_admin
from app.models import Item, StatusItem, Usuario, SolicitacaoDevolucao
from app.routers.itens import obter_item_ou_404
from app.schemas.item import EntregaRequest, ItemAdminResponse

router = APIRouter(prefix="/api/admin", tags=["Administrador"])


@router.get("/itens", response_model=list[ItemAdminResponse])
def listar_todos(
    status_item: StatusItem | None = None,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    """Histórico de todos os itens. Use ?status_item=achado para filtrar."""
    consulta = select(Item).order_by(col(Item.data_registro).desc(), col(Item.id).desc())
    if status_item is not None:
        consulta = consulta.where(Item.status == status_item)
    return session.exec(consulta).all()


@router.get("/itens/{item_id}", response_model=ItemAdminResponse)
def detalhar_item(
    item_id: int,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    return obter_item_ou_404(item_id, session)


@router.get("/resumo", response_model=dict[str, int])
def resumo(
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    """Quantidade de itens em cada status e de itens achados com pedido de retirada."""
    contagem = {"perdido": 0, "achado": 0, "entregue": 0, "solicitados": 0}
    linhas = session.exec(select(Item.status, func.count()).group_by(Item.status)).all()
    for situacao, quantidade in linhas:
        contagem[situacao.value] = quantidade

    # Itens achados com pelo menos um pedido (item entregue deixa de contar).
    contagem["solicitados"] = session.exec(
        select(func.count(func.distinct(SolicitacaoDevolucao.item_id)))
        .select_from(SolicitacaoDevolucao)
        .join(Item, Item.id == SolicitacaoDevolucao.item_id)
        .where(Item.status == StatusItem.achado)
    ).one()
    return contagem


@router.post("/itens/{item_id}/entregar", response_model=ItemAdminResponse)
def entregar_item(
    item_id: int,
    dados: EntregaRequest,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    """Marca como entregue e guarda quem retirou o objeto."""
    item = obter_item_ou_404(item_id, session)
    if item.status == StatusItem.entregue:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse item já foi entregue.")

    item.status = StatusItem.entregue
    item.data_devolucao = date.today()
    item.retirado_por_nome = dados.nome.strip()
    item.retirado_por_email = dados.email.lower()

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/itens/{item_id}/solicitacoes/{usuario_id}", status_code=204)
def recusar_solicitacao(
    item_id: int,
    usuario_id: int,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    """O administrador recusa (remove) o pedido de um usuário para um item."""
    pedido = session.exec(
        select(SolicitacaoDevolucao).where(
            SolicitacaoDevolucao.item_id == item_id,
            SolicitacaoDevolucao.usuario_id == usuario_id,
        )
    ).first()
    if pedido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação não encontrada.")
    session.delete(pedido)
    session.commit()