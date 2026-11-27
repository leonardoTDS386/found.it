"""Configuarações da APi"""

import os
from datetime import timedelta
from pathlib import Path

PASTA_BACKEND = Path(__file__).resolve().parent.parent

#BACK SQlite
URL_BANCO = f"sqlite:///{PASTA_BACKEND / 'foundit.db'}"

# Chave token
CHAVE_JWT = os.environ.get("FOUNDIT_JWT_SECRET", "chave-provisoria-de desenvolvimento")
ALGORITMO_JWT = "HS256"

# Duração dos tokens
DURACAO_TOKEN_ACESSO = timedelta(minutes=15)
DURACAO_TOKEN_REFRESH = timedelta(days=7)