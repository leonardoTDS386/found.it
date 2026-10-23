# Back-end (etapa futura)

Esta pasta é reservada para a **API REST em Python** do Found.it.

## O que está previsto

- Validação de dados (cadastros de usuários e de itens perdidos e achados)
- Controle de usuários: cadastro, autenticação e perfis (usuário e administrador)
- Armazenamento em banco de dados
- Registro de devolução, que altera o status do item para **Entregue**
- Envio de notificações por e-mail sobre novos itens

## Situação atual

Enquanto a API não existe, o front-end (pasta `frontend/`) usa dados provisórios:

- `frontend/armazenamento.py`: guarda os itens na memória do servidor.
- `frontend/app.py`: contém as contas de demonstração.

Quando a API estiver pronta, esses dois pontos devem ser trocados por chamadas
a ela. Os trechos a substituir estão marcados com `TODO` no código.
