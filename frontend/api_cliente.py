"""Cliente da API REST do Found.it.

Tudo que o site pede à API passa por aqui. Os tokens ficam na sessão do Flask
(cookie assinado e HttpOnly), então o navegador nunca os manipula.
"""

import os

import requests
from flask import session

URL_API = os.environ.get("FOUNDIT_API_URL", "http://127.0.0.1:5001")
TEMPO_LIMITE = 5  # segundos de espera pela API


class ErroApi(Exception):
    """A API respondeu com erro. 'status' é o código HTTP e 'mensagem' vem da API."""

    def __init__(self, mensagem, status=500):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class ApiIndisponivel(ErroApi):
    """A API está desligada ou não respondeu a tempo."""

    def __init__(self):
        super().__init__("Não foi possível falar com o servidor agora.", 503)


class SessaoExpirada(ErroApi):
    """O token de acesso venceu e o refresh também não serviu."""

    def __init__(self):
        super().__init__("Sessão expirada.", 401)


def _enviar(metodo, caminho, json=None, params=None, token=None):
    """Faz uma chamada HTTP à API, com o token de acesso se houver."""
    cabecalhos = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return requests.request(
            metodo,
            URL_API + caminho,
            json=json,
            params=params,
            headers=cabecalhos,
            timeout=TEMPO_LIMITE,
        )
    except requests.RequestException:
        raise ApiIndisponivel()


def _resultado(resposta):
    """Devolve o JSON da resposta ou levanta ErroApi se a API reclamou."""
    if resposta.status_code >= 400:
        try:
            corpo = resposta.json()
        except ValueError:
            corpo = None
        detalhe = corpo.get("detail") if isinstance(corpo, dict) else None
        if not isinstance(detalhe, str):
            detalhe = "Dados inválidos."
        raise ErroApi(detalhe, resposta.status_code)
    if resposta.status_code == 204:
        return None
    return resposta.json()


def _renovar_tokens():
    """Troca o refresh token por um par novo. Devolve True se deu certo."""
    refresh = session.get("token_refresh")
    if not refresh:
        return False
    resposta = _enviar("POST", "/api/auth/refresh", json={"refresh_token": refresh})
    if resposta.status_code != 200:
        return False
    tokens = resposta.json()
    session["token_acesso"] = tokens["access_token"]
    session["token_refresh"] = tokens["refresh_token"]
    return True


def requisitar(metodo, caminho, json=None, params=None):
    """Chamada autenticada. Se o token de acesso venceu, renova e tenta de novo."""
    resposta = _enviar(metodo, caminho, json, params, session.get("token_acesso"))
    if resposta.status_code == 401:
        if not _renovar_tokens():
            raise SessaoExpirada()
        resposta = _enviar(metodo, caminho, json, params, session.get("token_acesso"))
        if resposta.status_code == 401:
            raise SessaoExpirada()
    return _resultado(resposta)


def entrar(email, senha):
    """Login. Devolve (tokens, usuario). Não mexe na sessão: quem chama decide."""
    tokens = _resultado(
        _enviar("POST", "/api/auth/login", json={"email": email, "senha": senha})
    )
    usuario = _resultado(_enviar("GET", "/api/auth/me", token=tokens["access_token"]))
    return tokens, usuario


def sair(refresh_token):
    """Revoga o refresh token na API. Se falhar, o logout local acontece mesmo assim."""
    if not refresh_token:
        return
    try:
        _resultado(
            _enviar("POST", "/api/auth/logout", json={"refresh_token": refresh_token})
        )
    except ErroApi:
        pass


def listar_tipos():
    """Tipos de objeto: lista de {id, nome}."""
    return requisitar("GET", "/api/tipos")


def cadastrar_usuario(dados):
    """Cria uma conta de usuário (rota pública, sem token)."""
    return _resultado(_enviar("POST", "/api/auth/cadastro", json=dados))