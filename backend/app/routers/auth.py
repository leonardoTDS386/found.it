"""Cadastro, login, refresh e logout."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.config import DURACAO_TOKEN_REFRESH
from app.database import get_session
from app.dependencies import usuario_atual
from app.models import Perfil, TokenRefresh, Usuario
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.security import (
    agora_utc,
    criar_token_acesso,
    gerar_token_refresh,
    hash_senha,
    hash_token,
    verificar_senha,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


def _emitir_tokens(usuario: Usuario, session: Session) -> TokenResponse:
    """Cria o par de tokens e guarda o hash do refresh no banco."""
    refresh = gerar_token_refresh()
    session.add(
        TokenRefresh(
            token_hash=hash_token(refresh),
            expira_em=agora_utc() + DURACAO_TOKEN_REFRESH,
            usuario_id=usuario.id,
        )
    )
    session.commit()
    return TokenResponse(
        access_token=criar_token_acesso(usuario.id, usuario.perfil.value),
        refresh_token=refresh,
    )


@router.post("/cadastro", response_model=UsuarioResponse, status_code=201)
def cadastrar(dados: UsuarioCreate, session: Session = Depends(get_session)):
    email = dados.email.lower()
    if session.exec(select(Usuario).where(Usuario.email == email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com esse e-mail.")

    campos = dados.model_dump(exclude={"senha", "email"})
    usuario = Usuario(
        **campos,
        email=email,
        senha_hash=hash_senha(dados.senha),
        perfil=Perfil.usuario,      # nunca vem do cliente
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, session: Session = Depends(get_session)):
    usuario = session.exec(
        select(Usuario).where(Usuario.email == dados.email.lower())
    ).first()
    # Mesma mensagem para e-mail inexistente e senha errada (não revela qual foi).
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos.")
    return _emitir_tokens(usuario, session)


@router.post("/refresh", response_model=TokenResponse)
def renovar(dados: RefreshRequest, session: Session = Depends(get_session)):
    registro = session.exec(
        select(TokenRefresh).where(TokenRefresh.token_hash == hash_token(dados.refresh_token))
    ).first()
    if registro is None or registro.revogado or registro.expira_em < agora_utc():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido ou expirado.")

    registro.revogado = True        # cada refresh vale uma vez só
    session.add(registro)
    return _emitir_tokens(registro.usuario, session)


@router.post("/logout", status_code=204)
def sair(dados: RefreshRequest, session: Session = Depends(get_session)):
    registro = session.exec(
        select(TokenRefresh).where(TokenRefresh.token_hash == hash_token(dados.refresh_token))
    ).first()
    if registro is not None and not registro.revogado:
        registro.revogado = True
        session.add(registro)
        session.commit()


@router.get("/me", response_model=UsuarioResponse)
def meus_dados(usuario: Usuario = Depends(usuario_atual)):
    return usuario