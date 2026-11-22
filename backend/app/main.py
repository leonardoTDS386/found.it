"""Found.it - API REST"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from app import models # Registra as tabelas
from app.database import criar_tabelas, get_session
from app.routers import admin, auth, itens, tipos
from app.seed import popular_banco

@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    criar_tabelas()
    popular_banco()
    yield


app = FastAPI(
    title="Found.it - API",
    description="API REST do sistema de achados e perdidos Found.it",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.include_router(auth.router)
app.include_router(itens.router)
app.include_router(admin.router)
app.include_router(tipos.router)


@app.get("/api/saude", tags=["Saúde"])
def saude(session: Session = Depends(get_session)):
    """Confirma que a API e o banco estão funcionando"""
    session.exec(select(models.Tipo)).first()
    return {"status": "ok"}