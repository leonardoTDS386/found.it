"""Tipos de objeto (Acessório, Eletrônico...)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.database import get_session
from app.dependencies import exigir_admin, usuario_atual
from app.models import Item, Tipo, Usuario
from app.schemas.tipo import TipoCreate, TipoResponse, TipoUso

router = APIRouter(prefix="/api/tipos", tags=["Tipos de objeto"])


@router.get("", response_model=list[TipoResponse])
def listar_tipos(
    usuario: Usuario = Depends(usuario_atual),
    session: Session = Depends(get_session),
):
    return session.exec(select(Tipo).order_by(Tipo.id)).all()


@router.get("/uso", response_model=list[TipoUso])
def listar_tipos_com_uso(
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    """Cada tipo com a quantidade de itens que o usam."""
    consulta = (
        select(Tipo, func.count(Item.id))
        .join(Item, Item.tipo_id == Tipo.id, isouter=True)
        .group_by(Tipo.id)
        .order_by(Tipo.id)
    )
    return [
        TipoUso(id=tipo.id, nome=tipo.nome, quantidade_itens=quantidade)
        for tipo, quantidade in session.exec(consulta).all()
    ]


@router.post("", response_model=TipoResponse, status_code=201)
def adicionar_tipo(
    dados: TipoCreate,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    nome = " ".join(dados.nome.split())    # tira espaços repetidos
    if len(nome) < 2:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Informe o nome do tipo.")

    existentes = session.exec(select(Tipo)).all()
    if any(t.nome.casefold() == nome.casefold() for t in existentes):
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse tipo de objeto já existe.")

    tipo = Tipo(nome=nome)
    session.add(tipo)
    session.commit()
    session.refresh(tipo)
    return tipo


@router.delete("/{tipo_id}", status_code=204)
def excluir_tipo(
    tipo_id: int,
    admin: Usuario = Depends(exigir_admin),
    session: Session = Depends(get_session),
):
    tipo = session.get(Tipo, tipo_id)
    if tipo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tipo de objeto não encontrado.")

    em_uso = session.exec(select(func.count(Item.id)).where(Item.tipo_id == tipo_id)).one()
    if em_uso:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Esse tipo está em uso por itens cadastrados e não pode ser excluído.",
        )

    total = session.exec(select(func.count(Tipo.id))).one()
    if total <= 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "É preciso manter pelo menos um tipo de objeto."
        )

    session.delete(tipo)
    session.commit()