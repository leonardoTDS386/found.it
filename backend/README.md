# Back-end (API REST)

API REST do Found.it, feita com **FastAPI** e **SQLModel**, com banco SQLite.

## Como rodar

Na pasta `backend`, com o ambiente virtual ativado:

    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 5001

- API: http://127.0.0.1:5001
- Documentação interativa (Swagger): http://127.0.0.1:5001/docs
- Verificação rápida: http://127.0.0.1:5001/api/saude

O banco `foundit.db` é criado na primeira execução, junto com os tipos, as contas
e os itens de demonstração (`app/seed.py`). Para recomeçar do zero, pare a API e
apague o arquivo `foundit.db`.

## Autenticação

1. `POST /api/auth/login` devolve `access_token` (15 minutos) e `refresh_token` (7 dias).
2. As rotas protegidas recebem `Authorization: Bearer <access_token>`.
3. `POST /api/auth/refresh` troca o refresh por um par novo (cada refresh vale uma vez).
4. `POST /api/auth/logout` revoga o refresh.

No Swagger, use o botão **Authorize** e cole o `access_token`.

## Variáveis de ambiente

| Variável | Para que serve |
|---|---|
| `FOUNDIT_JWT_SECRET` | Chave que assina os tokens (defina uma própria em produção) |