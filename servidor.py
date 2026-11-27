"""Servidor único do Found.it: a API (FastAPI) e o site (Flask) em um só processo.

Uso (na pasta raiz do projeto, com o ambiente virtual ativo):
    uvicorn servidor:raiz --port 8000

O site fica em "/" e a API em "/backend" (documentação em "/backend/docs").
"""
import importlib.util
import os
import sys
from pathlib import Path

from a2wsgi import WSGIMiddleware
from fastapi import FastAPI

RAIZ = Path(__file__).resolve().parent
PASTA_BACKEND = RAIZ / "backend"
PASTA_SITE = RAIZ / "frontend"

# Tanto o backend (pasta "app") quanto o site (arquivo "app.py") se chamam "app".
# O backend vai na frente da lista, então "import app" é o pacote do backend.
# O site é carregado mais abaixo, com outro nome.
sys.path.insert(0, str(PASTA_BACKEND))
sys.path.append(str(PASTA_SITE))

# O site chama a API no próprio servidor. Se FOUNDIT_API_URL já estiver definida,
# ela é respeitada. A Render informa a porta pela variável PORT.
PORTA = os.environ.get("PORT", "8000")
os.environ.setdefault("FOUNDIT_API_URL", f"http://127.0.0.1:{PORTA}/backend")

from app.main import app as api  # noqa: E402  (API do backend)

# Carrega frontend/app.py com o nome "site_flask" para não esbarrar no pacote "app".
especificacao = importlib.util.spec_from_file_location(
    "site_flask", PASTA_SITE / "app.py"
)
modulo_site = importlib.util.module_from_spec(especificacao)
sys.modules["site_flask"] = modulo_site
especificacao.loader.exec_module(modulo_site)
site = modulo_site.app

# A API usa "lifespan" para criar as tabelas e os dados de exemplo ao iniciar.
# Como ela fica montada dentro deste servidor, o lifespan dela é repassado para cá.
raiz = FastAPI(
    lifespan=api.router.lifespan_context,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
raiz.mount("/backend", api)
raiz.mount("/", WSGIMiddleware(site))