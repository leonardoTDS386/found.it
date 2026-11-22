"""Hash de senhas e criação/leitura dos tokens."""

import hashlib
import secrets
from datetime import datetime, timezone

import jwt
from pwdlib import PasswordHash

from app.config import ALGORITMO_JWT, CHAVE_JWT, DURACAO_TOKEN_ACESSO

_hasher = PasswordHash.recommended()   # Argon2


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return _hasher.verify(senha, senha_hash)


def agora_utc() -> datetime:
    """Hora atual em UTC, sem fuso (como o SQLite guarda)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def criar_token_acesso(usuario_id: int, perfil: str) -> str:
    agora = datetime.now(timezone.utc)
    dados = {
        "sub": str(usuario_id),      # quem é
        "perfil": perfil,
        "tipo": "acesso",
        "iat": agora,                # criado em
        "exp": agora + DURACAO_TOKEN_ACESSO,   # expira em
    }
    return jwt.encode(dados, CHAVE_JWT, algorithm=ALGORITMO_JWT)


def decodificar_token_acesso(token: str) -> dict:
    """Levanta jwt.PyJWTError se o token for falso, alterado ou vencido."""
    dados = jwt.decode(token, CHAVE_JWT, algorithms=[ALGORITMO_JWT])
    if dados.get("tipo") != "acesso":
        raise jwt.InvalidTokenError("Tipo de token inválido")
    return dados


def gerar_token_refresh() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()