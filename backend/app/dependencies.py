"""Dependências reutilizáveis: quem está logado e se é administrador."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_session
from app.models import Perfil, Usuario
from app.security import decodificar_token_acesso

esquema_bearer = HTTPBearer(description="Cole aqui o token de acesso")


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    session: Session = Depends(get_session),
) -> Usuario:
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dados = decodificar_token_acesso(credenciais.credentials)
    except jwt.PyJWTError:
        raise erro

    usuario = session.get(Usuario, int(dados["sub"]))
    if usuario is None:
        raise erro
    return usuario


def exigir_admin(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    if usuario.perfil != Perfil.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para administradores.",
        )
    return usuario