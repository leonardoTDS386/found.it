"""Conexão com o banco de dados"""

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import URL_BANCO

engine = create_engine(URL_BANCO, connect_args={"check_same_thread": False})


@event.listens_for(Engine, "connect")
def ativar_chaves_estrangeiras(conexao, _registro):
    """O SQLite só respeita chaves estrangeiras de essa função for ligada"""
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

def criar_tabelas():
    """Cria as tabelas que ainda não existem"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Entrega uma sessão por requisição e depois a fecha"""
    with Session(engine) as session:
        yield session