# Found.it - Sistema de achados e perdidos

Sistema web para registrar, procurar e devolver objetos perdidos. Pensado para
empresas privadas, mas também aplicável a instituições como o IFPI.

Projeto Integrador do curso técnico em Desenvolvimento de Sistemas
(Instituto Federal do Piauí - IFPI).

> **Situação do projeto:** o **front-end está completo e navegável**. O back-end
> com API REST e banco de dados é a próxima etapa. Enquanto isso, o site usa
> contas de demonstração e guarda os dados na memória do servidor
> (veja [Observações importantes](#observações-importantes)).

## O problema

Pessoas perdem objetos em ambientes compartilhados e, hoje, a única forma de
recuperá-los é ir pessoalmente aos setores responsáveis. O Found.it centraliza
os itens perdidos e achados em um só lugar, facilita a busca e registra a
devolução ao dono verdadeiro.

## Perfis de usuário

| Perfil | O que faz |
|---|---|
| **Usuário** | Cria conta, cadastra itens perdidos, busca itens, vê os detalhes, consulta o próprio histórico e edita ou exclui os itens que cadastrou |
| **Administrador** | Cadastra itens achados, consulta o histórico de todos os itens, edita e exclui itens, marca itens como entregues (com nome e e-mail de quem retirou) e gerencia os tipos de objeto |

## Status dos itens

| Status | Quem define |
|---|---|
| **Perdido** | Cadastrado pelo usuário |
| **Achado** | Cadastrado pelo administrador |
| **Entregue** | Definido pelo administrador na devolução do item (guarda nome e e-mail de quem retirou). Itens entregues não podem mais ser editados nem excluídos |

## Telas do sistema

**Área do usuário**
- Login (`/login`) e criação de conta (`/cadastro`), com validação de CPF, telefone,
  confirmação de senha, indicador de força da senha e consentimento (LGPD)
- Busca de itens (`/busca`): filtros por nome, tipo, local e data, resultados na
  própria página e balão com todos os detalhes do item
- Cadastro de item perdido (`/cadastrar-item-perdido`)
- Meu histórico (`/historico`): itens registrados pelo usuário; ao clicar em um item abre o balão com os detalhes e as opções **Editar** e **Excluir** (apenas itens próprios e ainda não entregues)
- Edição de item (`/item/<id>/editar`)

**Área do administrador**
- Login (`/admin/login`)
- Página inicial (`/admin`): resumo de itens por status e atalhos
- Cadastro de item achado (`/admin/cadastrar-item-achado`)
- Histórico (`/admin/historico`): todos os itens em cartões, com filtro por status; o balão mostra todos os detalhes (inclusive horário e, nos entregues, quem retirou) e permite **marcar como entregue**, **editar** e **excluir**
- Tipos de objeto (`/admin/tipos`): adicionar e excluir tipos (um tipo em uso por algum item não pode ser excluído). Os tipos aparecem nos formulários e na busca

O projeto também traz menu do usuário com iniciais, balão com o nome ao passar o
cursor, mensagem de boas-vindas ao entrar e logout.

## Tecnologias

- **Python** e **Flask** (servidor do front-end, rotas e sessão)
- **HTML**, **CSS** e **JavaScript**
- **Bootstrap 5** e **Bootstrap Icons**, carregados por CDN (exigem internet)
- **Jinja2** (templates reutilizáveis)
- API REST em Python para o back-end (etapa futura)

## Estrutura do projeto

```
foundit/
├── backend/                    # API REST (etapa futura)
├── docs/                       # Mockup e documentação do projeto
├── frontend/
│   ├── app.py                  # Servidor Flask: rotas, sessão e validações
│   ├── armazenamento.py        # Armazenamento provisório em memória
│   ├── dados/
│   │   └── itens_iniciais.json # Itens de exemplo
│   ├── static/
│   │   ├── css/style.css       # Identidade visual do Found.it
│   │   ├── js/                 # Scripts de cada página
│   │   └── img/                # Logo, ícone e favicon
│   └── templates/              # Páginas e componentes (Jinja2)
├── .gitignore
├── README.md
└── requirements.txt
```

## Como rodar

Requer **Python 3.9 ou superior** e acesso à internet (para o Bootstrap).

```bash
# 1. entre na pasta do projeto
cd foundit

# 2. (opcional) crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. instale as dependências
pip install -r requirements.txt

# 4. inicie o servidor
cd frontend
python app.py
```

Abra `http://127.0.0.1:5000` no navegador.

## Contas de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Usuário | `usuario@foundit.com` | `123456` |
| Administrador | `admin@foundit.com` | `admin123` |

O login do administrador fica em `/admin/login` (há um link na tela de login do usuário).

### Roteiro para apresentar

1. Entre como **administrador**, cadastre um item achado e consulte o histórico.
2. Saia e entre como **usuário**.
3. Na busca, procure o item que o administrador cadastrou e abra o balão de detalhes.
4. Cadastre um item perdido, veja-o em **Meu histórico** e edite-o pelo balão.
5. Volte ao administrador, abra o item no histórico e marque-o como **entregue** informando quem retirou.
6. Em **Tipos de objeto**, adicione um tipo novo e veja-o nos formulários.

## Observações importantes

- **Dados provisórios:** os itens ficam na memória do servidor
  (`frontend/armazenamento.py`), inclusive os tipos de objeto. Ao reiniciar o servidor, voltam ao estado
  inicial (`frontend/dados/itens_iniciais.json`).
- **Contas de demonstração:** as senhas estão escritas em `frontend/app.py`. Isso
  é só para a fase de front-end e **deve ser removido** quando o back-end existir.
- **Cadastro de usuário:** a tela valida os dados e volta ao login, mas ainda não
  cria uma conta de verdade.
- **Solicitar devolução:** o botão aparece nos itens achados, mas a forma da
  solicitação ainda será definida junto com o back-end.
- **Chave da sessão:** em produção, defina a variável de ambiente
  `FOUNDIT_SECRET_KEY` com um valor secreto.
- **Modo debug:** `python app.py` inicia o Flask com `debug=True`. Não use esse
  modo em produção.

## Identidade visual

| Uso | Cor |
|---|---|
| Principal (petróleo) | `#0F4C5C` |
| Destaque (âmbar) | `#F59E0B` |
| Status Perdido | `#E4572E` |
| Status Achado | `#2F6FED` |
| Status Entregue | `#2E9E6B` |

## Próximos passos

- [ ] API REST em Python e banco de dados
- [ ] Autenticação real e cadastro de usuários
- [ ] Solicitação de devolução feita pelo usuário (hoje o administrador registra a entrega)
- [ ] Notificações por e-mail de novos itens
- [ ] Imagem do item (campo opcional)

## Equipe

Alunos: William, João Vitor e Leonardo.

Mockup de baixa fidelidade, mapa de navegação e fluxos de uso:
[`docs/Mockup_Found.it_v1.3.pdf`](docs/Mockup_Found.it_v1.3.pdf).
