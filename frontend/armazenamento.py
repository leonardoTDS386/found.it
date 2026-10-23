"""Armazenamento PROVISÓRIO de itens, guardado na memória do servidor.

Serve para o front-end funcionar de ponta a ponta (cadastrar, buscar e consultar
o histórico) enquanto o back-end com API REST e banco de dados não existe.

Os dados iniciais vêm de dados/itens_iniciais.json. Tudo que for cadastrado
fica só na memória: ao reiniciar o servidor, volta ao estado inicial.

Quando a API REST estiver pronta, este módulo deve ser substituído por
chamadas à API.
"""

import json
import threading
from datetime import date
from pathlib import Path

_ARQUIVO_INICIAL = Path(__file__).parent / "dados" / "itens_iniciais.json"
_trava = threading.Lock()
_itens = json.loads(_ARQUIVO_INICIAL.read_text(encoding="utf-8"))

# Tipos de objeto oferecidos nos formulários e na busca (o administrador gerencia).
_tipos = [
    "Acessório",
    "Eletrônico",
    "Documento",
    "Material de estudo",
    "Vestuário",
    "Outro",
]

# Campos que o administrador ou o dono podem alterar na edição.
CAMPOS_EDITAVEIS = ("nome", "tipo", "descricao", "local", "data", "horario")

# Campos que podem ser enviados ao navegador na busca (sem dados de quem registrou).
CAMPOS_PUBLICOS = (
    "id",
    "nome",
    "descricao",
    "tipo",
    "local",
    "data",
    "horario",
    "status",
)


def _ordenados(itens):
    """Mais recentes primeiro (data do registro e, em empate, o último criado)."""
    return sorted(itens, key=lambda i: (i["data_registro"], i["id"]), reverse=True)


def listar_publicos():
    """Itens para a busca do usuário, só com os campos públicos."""
    with _trava:
        return [{c: i[c] for c in CAMPOS_PUBLICOS} for i in _itens]


def listar_todos():
    """Todos os registros (uso do administrador)."""
    with _trava:
        return _ordenados([dict(i) for i in _itens])


def listar_do_usuario(email):
    """Registros feitos por um usuário (histórico do usuário)."""
    with _trava:
        return _ordenados(
            [dict(i) for i in _itens if i["registrado_por"] == email]
        )


def contar_por_status():
    """Quantidade de itens em cada status."""
    contagem = {"perdido": 0, "achado": 0, "entregue": 0}
    with _trava:
        for item in _itens:
            contagem[item["status"]] += 1
    return contagem


def adicionar(*, tipo_registro, registrado_por, nome, tipo, descricao,
              local, data, horario):
    """Cadastra um item. tipo_registro é "perdido" (usuário) ou "achado" (admin)."""
    with _trava:
        novo = {
            "id": max((i["id"] for i in _itens), default=0) + 1,
            "nome": nome,
            "descricao": descricao,
            "tipo": tipo,
            "local": local,
            "data": data,
            "horario": horario,
            "status": tipo_registro,
            "tipo_registro": tipo_registro,
            "registrado_por": registrado_por,
            "data_registro": date.today().isoformat(),
            "data_devolucao": None,
        }
        _itens.append(novo)
        return dict(novo)


def obter(item_id):
    """Um item pelo id (cópia) ou None."""
    with _trava:
        for item in _itens:
            if item["id"] == item_id:
                return dict(item)
    return None


def atualizar(item_id, dados):
    """Altera os campos editáveis de um item. Devolve o item ou None."""
    with _trava:
        for item in _itens:
            if item["id"] == item_id:
                for campo in CAMPOS_EDITAVEIS:
                    item[campo] = dados[campo]
                return dict(item)
    return None


def excluir(item_id):
    """Remove um item. Devolve True se existia."""
    with _trava:
        for posicao, item in enumerate(_itens):
            if item["id"] == item_id:
                del _itens[posicao]
                return True
    return False


def marcar_entregue(item_id, nome, email):
    """Muda o status para entregue e guarda quem retirou o item."""
    with _trava:
        for item in _itens:
            if item["id"] == item_id:
                item["status"] = "entregue"
                item["data_devolucao"] = date.today().isoformat()
                item["retirado_por_nome"] = nome
                item["retirado_por_email"] = email
                return dict(item)
    return None


# --- Tipos de objeto ---------------------------------------------------------
def listar_tipos():
    with _trava:
        return list(_tipos)


def contar_por_tipo():
    """{tipo: quantidade de itens que usam o tipo}."""
    with _trava:
        contagem = {t: 0 for t in _tipos}
        for item in _itens:
            if item["tipo"] in contagem:
                contagem[item["tipo"]] += 1
        return contagem


def adicionar_tipo(nome):
    """Devolve None se deu certo ou a mensagem de erro."""
    with _trava:
        if any(t.casefold() == nome.casefold() for t in _tipos):
            return "Esse tipo de objeto já existe."
        _tipos.append(nome)
    return None


def remover_tipo(nome):
    """Devolve None se deu certo ou a mensagem de erro."""
    with _trava:
        if nome not in _tipos:
            return "Tipo de objeto não encontrado."
        if any(i["tipo"] == nome for i in _itens):
            return "Esse tipo está em uso por itens cadastrados e não pode ser excluído."
        if len(_tipos) == 1:
            return "É preciso manter pelo menos um tipo de objeto."
        _tipos.remove(nome)
    return None
