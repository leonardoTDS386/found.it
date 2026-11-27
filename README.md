# Found.it - Sistema de achados e perdidos

Sistema web para registrar, procurar e devolver objetos perdidos. Pensado para
empresas privadas, mas também aplicável a instituições como o IFPI.

Projeto Integrador do curso técnico em Desenvolvimento de Sistemas
(Instituto Federal do Piauí - IFPI).

> **Situação do projeto:** completo. O **front-end** (Flask) e o **back-end**
> (API REST em FastAPI, com banco de dados SQLite e autenticação por tokens)
> estão integrados.

## O problema

Pessoas perdem objetos em ambientes compartilhados e, hoje, a única forma de
recuperá-los é ir pessoalmente aos setores responsáveis. O Found.it centraliza
os itens perdidos e achados em um só lugar, facilita a busca e registra a
devolução ao dono verdadeiro.

## Como o sistema é organizado

```
Navegador ──► Site (Flask, porta 5000) ──► API REST (FastAPI, porta 5001) ──► SQLite
```

O navegador conversa só com o site. O servidor do site chama a API e guarda os
tokens na sessão (cookie assinado e HttpOnly), então o JavaScript nunca toca
nos tokens.

## Perfis de usuário

| Perfil | O que faz |
|---|---|
| **Usuário** | Cria conta, cadastra itens perdidos, busca itens, vê os detalhes, solicita a devolução de itens achados (e cancela o pedido), consulta o próprio histórico e edita ou exclui os itens que cadastrou |
| **Administrador** | Cadastra itens achados, consulta o histórico de todos os itens, edita e exclui itens, marca itens como entregues (com nome e e-mail de quem retirou), acompanha e recusa solicitações de devolução e gerencia os tipos de objeto |

## Status dos itens

| Status | Quem define |
|---|---|
| **Perdido** | Cadastrado pelo usuário |
| **Achado** | Cadastrado pelo administrador |
| **Entregue** | Definido pelo administrador na devolução. Itens entregues não podem mais ser editados nem excluídos |

## Telas do sistema

**Área do usuário**
- Login (`/login`) e criação de conta (`/cadastro`), com validação de CPF,
  telefone, confirmação de senha, indicador de força da senha e consentimento (LGPD)
- Busca de itens (`/busca`): filtros por nome, tipo, local e data, e balão com os detalhes.
  Nos itens achados, o botão **Solicitar devolução** registra o pedido e mostra como
  retirar o item (local, horário, o que levar e link do Google Maps). O pedido pode ser cancelado
- Cadastro de item perdido (`/cadastrar-item-perdido`)
- Meu histórico (`/historico`): balão com detalhes e opções de editar e excluir

**Área do administrador**
- Login (`/admin/login`)
- Página inicial (`/admin`): resumo por status (cada quadro leva ao histórico já filtrado).
  O quadro **Solicitações** fica em destaque só quando há pedidos de devolução pendentes
- Cadastro de item achado (`/admin/cadastrar-item-achado`)
- Histórico (`/admin/historico`): todos os itens, com filtro (inclusive "Solicitados"),
  selo "Solicitado", detalhes com a lista de quem pediu o item (com opção de recusar),
  edição, exclusão e entrega
- Tipos de objeto (`/admin/tipos`): adicionar e excluir tipos

## API REST

A documentação interativa (Swagger) fica em `http://127.0.0.1:5001/docs`.

| Método e rota | Descrição | Acesso |
|---|---|---|
| `POST /api/auth/cadastro` | Cria uma conta de usuário | público |
| `POST /api/auth/login` | Devolve token de acesso e token de refresh | público |
| `POST /api/auth/refresh` | Troca o refresh por um par novo de tokens | público |
| `POST /api/auth/logout` | Revoga o refresh token | público |
| `GET /api/auth/me` | Dados de quem está logado | logado |
| `GET /api/itens` | Busca de itens (sem os entregues) | logado |
| `GET /api/itens/meus` | Histórico de quem está logado | logado |
| `GET /api/itens/{id}` | Detalhes de um item | logado |
| `POST /api/itens` | Cadastra item (perdido ou achado, conforme o perfil) | logado |
| `PUT /api/itens/{id}` | Edita um item | dono ou administrador |
| `DELETE /api/itens/{id}` | Exclui um item | dono ou administrador |
| `GET /api/tipos` | Lista os tipos de objeto | logado |
| `GET /api/tipos/uso` | Tipos com a quantidade de itens | administrador |
| `POST /api/tipos` | Adiciona um tipo | administrador |
| `DELETE /api/tipos/{id}` | Exclui um tipo (se não estiver em uso) | administrador |
| `GET /api/admin/itens` | Todos os itens | administrador |
| `GET /api/admin/itens/{id}` | Detalhes completos de um item | administrador |
| `GET /api/admin/resumo` | Contagem por status e de itens com solicitações pendentes | administrador |
| `POST /api/admin/itens/{id}/entregar` | Marca como entregue | administrador |
| `POST /api/itens/{id}/solicitar` | Registra a solicitação de devolução de um item achado | usuário |
| `DELETE /api/itens/{id}/solicitar` | Cancela a própria solicitação | usuário |
| `GET /api/itens/solicitacoes/minhas` | Itens que o usuário solicitou | usuário |
| `DELETE /api/admin/itens/{id}/solicitacoes/{usuario_id}` | Recusa (remove) a solicitação de um usuário | administrador |

### Segurança

- Senhas guardadas com hash Argon2, nunca em texto.
- **Token de acesso** (JWT) com validade de 15 minutos, enviado em
  `Authorization: Bearer ...`.
- **Token de refresh** com validade de 7 dias, de uso único (a cada renovação o
  anterior é revogado). No banco fica só o hash do token.
- O perfil (usuário ou administrador) vem do token, nunca do cliente.
- Permissões conferidas na API: o usuário só altera os próprios itens.

## Tecnologias

- **Front-end:** Python, Flask, Jinja2, HTML, CSS, JavaScript, Bootstrap 5 e
  Bootstrap Icons (por CDN, exigem internet)
- **Back-end:** Python, FastAPI, SQLModel (SQLAlchemy + Pydantic), SQLite, PyJWT
  e pwdlib (Argon2)
- **Comunicação site e API:** biblioteca `requests`

## Estrutura do projeto

```
found.it/
├── backend/
│   ├── app/
│   │   ├── main.py             # Liga a API e as rotas
│   │   ├── config.py           # Configurações (banco, chaves, duração dos tokens)
│   │   ├── database.py         # Conexão com o banco
│   │   ├── security.py         # Hash de senha e tokens
│   │   ├── dependencies.py     # Proteção das rotas (logado, administrador)
│   │   ├── seed.py             # Dados iniciais (tipos, contas e itens de exemplo)
│   │   ├── models/             # Tabelas do banco
│   │   ├── schemas/            # Formatos de entrada e saída da API
│   │   └── routers/            # Rotas: auth, itens, tipos e admin
│   └── requirements.txt
├── docs/                       # Mockup e documentação do projeto
├── frontend/
│   ├── app.py                  # Servidor Flask: rotas do site e validações
│   ├── api_cliente.py          # Comunicação com a API (tokens e renovação)
│   ├── retirada.py             # Dados de retirada dos itens achados (editar aqui)
│   ├── static/                 # CSS, JavaScript e imagens
│   └── templates/              # Páginas e componentes (Jinja2)
├── .gitignore
├── README.md
└── requirements.txt            # Dependências do site
```

## Como rodar

Requer **Python 3.10 ou superior** e acesso à internet (para o Bootstrap).

```bash
# 1. entre na pasta do projeto
cd found.it

# 2. crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

# 3. instale as dependências do site e da API
pip install -r requirements.txt -r backend/requirements.txt
```

São dois servidores, cada um em um terminal (com o ambiente ativado):

```bash
# Terminal 1 - API (porta 5001)
cd backend
uvicorn app.main:app --reload --port 5001

# Terminal 2 - Site (porta 5000)
cd frontend
python app.py
```

Abra `http://127.0.0.1:5000` no navegador. Na primeira execução, a API cria o
arquivo `backend/foundit.db` com os tipos, as contas e os itens de demonstração.

Para voltar ao estado inicial, pare a API, apague `backend/foundit.db` e inicie de novo.

## Contas de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Usuário | `usuario@foundit.com` | `123456` |
| Administrador | `admin@foundit.com` | `admin123` |

O login do administrador fica em `/admin/login` (há um link na tela de login do usuário).

### Roteiro para apresentar

1. Crie uma conta nova em **Criar conta** e entre com ela.
2. Cadastre um item perdido e veja-o em **Meu histórico**. Edite-o pelo balão.
3. Saia e entre como **administrador**. Cadastre um item achado.
4. No histórico, abra o item perdido e marque-o como **entregue**, informando quem retirou.
5. Na página inicial, clique em um dos quadros de resumo e veja o histórico já filtrado.
6. Em **Tipos de objeto**, adicione um tipo novo e veja-o nos formulários.
7. Como usuário, abra um item **achado** na busca e clique em **Solicitar devolução**.
   Veja o quadro de retirada e o link do mapa.
8. Como administrador, note o quadro **Solicitações** em destaque na página inicial.
   Abra o histórico filtrado, veja quem pediu o item e use **Recusar** se quiser.

## Observações importantes

- **Contas de demonstração:** as senhas das contas de exemplo estão em
  `backend/app/seed.py`. Elas servem só para o desenvolvimento e devem ser
  trocadas ou removidas antes de qualquer uso real.
- **Chaves secretas:** em produção, defina as variáveis de ambiente
  `FOUNDIT_SECRET_KEY` (sessão do site) e `FOUNDIT_JWT_SECRET` (tokens da API)
  com valores longos e secretos. `FOUNDIT_API_URL` indica onde a API está
  (padrão `http://127.0.0.1:5001`).
- **Modo debug:** `python app.py` inicia o Flask com `debug=True`. Não use esse
  modo em produção.
- **Dados de retirada:** o local, o horário e as orientações mostrados depois de
  solicitar a devolução ficam em `frontend/retirada.py`. Hoje são dados provisórios
  ("Empresa Exemplo Ltda."): edite o dicionário `RETIRADA` com os dados reais. O link
  do Google Maps é gerado sozinho a partir do endereço.
- **Solicitações:** recusar ou cancelar apenas remove o pedido (não há status
  "recusado"). A solicitação deixa de contar quando o item é marcado como entregue.

## Identidade visual

| Uso | Cor |
|---|---|
| Principal (petróleo) | `#0F4C5C` |
| Destaque (âmbar) | `#F59E0B` |
| Status Perdido | `#E4572E` |
| Status Achado | `#2F6FED` |
| Status Entregue | `#2E9E6B` |

## Próximos passos

- [x] Solicitação de devolução feita pelo usuário
- [ ] Notificações por e-mail: avisar o administrador de novas solicitações e o usuário quando o pedido for recusado
- [ ] Notificações por e-mail de novos itens
- [ ] Status "recusado" para solicitações, com motivo
- [ ] Imagem do item (campo opcional)
- [ ] Proteção contra CSRF nos formulários do site
- [ ] Banco de dados PostgreSQL e publicação em um servidor

## Equipe

Alunos: William, João Vitor e Leonardo.

Mockup de baixa fidelidade, mapa de navegação e fluxos de uso:
[`docs/Mockup_Found.it_v1.3.pdf`](docs/Mockup_Found.it_v1.3.pdf).