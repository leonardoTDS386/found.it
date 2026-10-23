"""Found.it - Sistema de achados e perdidos.

Servidor Flask usado para servir o front-end.
A integração com a API REST (back-end) será feita em uma etapa posterior.

ATENÇÃO - CÓDIGO PROVISÓRIO
As contas abaixo e o armazenamento em memória (armazenamento.py) existem só
para o site ficar funcional durante o desenvolvimento do front-end. Quando o
back-end estiver pronto, a autenticação e o armazenamento de itens passam a ser
feitos pela API REST, e estas partes devem ser removidas.
"""

import hmac
import os
import re
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import armazenamento

app = Flask(__name__)

# Chave usada para assinar a sessão. Em produção, defina FOUNDIT_SECRET_KEY.
app.secret_key = os.environ.get(
    "FOUNDIT_SECRET_KEY", "foundit-chave-provisoria-de-desenvolvimento"
)

# --- Contas provisórias -----------------------------------------------------
CONTAS_PROVISORIAS = [
    {
        "perfil": "usuario",
        "nome": "Leonardo Vínicius",
        "email": "usuario@foundit.com",
        "senha": "123456",
    },
    {
        "perfil": "admin",
        "nome": "Administrador Found.it",
        "email": "admin@foundit.com",
        "senha": "admin123",
    },
]

ROTULOS_STATUS = {"perdido": "Perdido", "achado": "Achado", "entregue": "Entregue"}


# --- Filtros usados nos templates -------------------------------------------
@app.template_filter("data_br")
def data_br(valor):
    """'2026-10-23' -> '23/10/2026'. Sem data, mostra um traço."""
    if not valor:
        return "—"
    ano, mes, dia = valor.split("-")
    return f"{dia}/{mes}/{ano}"


@app.template_filter("rotulo_status")
def rotulo_status(valor):
    return ROTULOS_STATUS.get(valor, valor)


# --- Autenticação -----------------------------------------------------------
def _igual(a, b):
    """Compara textos em tempo constante (evita vazar informação pelo tempo)."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def autenticar(perfil, email, senha):
    """Devolve a conta se e-mail e senha conferem para o perfil, senão None."""
    email = (email or "").strip().lower()
    senha = senha or ""
    for conta in CONTAS_PROVISORIAS:
        if conta["perfil"] != perfil:
            continue
        if _igual(conta["email"], email) and _igual(conta["senha"], senha):
            return conta
    return None


def iniciar_sessao(conta):
    session.clear()
    session["usuario_nome"] = conta["nome"]
    session["usuario_email"] = conta["email"]
    session["perfil"] = conta["perfil"]


def login_obrigatorio(perfil):
    """Só deixa entrar quem está logado com o perfil pedido."""

    def decorador(funcao):
        @wraps(funcao)
        def envolvida(*args, **kwargs):
            atual = session.get("perfil")
            if atual == perfil:
                return funcao(*args, **kwargs)
            if atual == "admin":
                return redirect(url_for("admin_painel"))
            if atual == "usuario":
                flash("Esta área é exclusiva para administradores.", "erro")
                return redirect(url_for("busca"))
            flash("Faça login para acessar esta página.", "erro")
            destino = "admin_login" if perfil == "admin" else "login"
            return redirect(url_for(destino))

        return envolvida

    return decorador


@app.after_request
def nao_guardar_em_cache(resposta):
    """Páginas de quem está logado não ficam no cache do navegador.

    Assim, depois de sair da conta, o botão "voltar" não mostra a página antiga.
    """
    if session.get("perfil"):
        resposta.headers["Cache-Control"] = "no-store"
    return resposta


# --- Páginas públicas -------------------------------------------------------
@app.route("/")
def index():
    """A primeira página do sistema é o login."""
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        conta = autenticar("usuario", email, request.form.get("senha"))
        if conta:
            iniciar_sessao(conta)
            primeiro_nome = conta["nome"].split()[0]
            flash(
                f"Boas-vindas ao Found.it, {primeiro_nome}! "
                "Procure seus objetos ou cadastre um item perdido.",
                "boas-vindas",
            )
            return redirect(url_for("busca"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("login.html", email=email)


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        conta = autenticar("admin", email, request.form.get("senha"))
        if conta:
            iniciar_sessao(conta)
            flash("Boas-vindas ao Found.it, Administrador!", "boas-vindas")
            return redirect(url_for("admin_painel"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("admin_login.html", email=email)


@app.route("/logout")
def logout():
    destino = "admin_login" if session.get("perfil") == "admin" else "login"
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for(destino))


# --- Validação dos formulários de item --------------------------------------
def validar_item(form, achado=False):
    """Valida os dados do formulário no servidor. Devolve a lista de erros."""
    erros = []
    verbo = "encontrado" if achado else "perdido"

    nome = form.get("nome", "").strip()
    if not nome or len(nome) > 120:
        erros.append("Informe o nome do objeto (até 120 caracteres).")

    if form.get("tipo") not in armazenamento.listar_tipos():
        erros.append("Selecione um tipo de objeto válido.")

    descricao = form.get("descricao", "").strip()
    if not descricao or len(descricao) > 1000:
        erros.append("Informe a descrição do objeto (até 1000 caracteres).")

    local = form.get("local", "").strip()
    if not local or len(local) > 200:
        erros.append(f"Informe o local onde o objeto foi {verbo}.")

    try:
        data_item = date.fromisoformat(form.get("data", ""))
    except ValueError:
        erros.append("Informe uma data válida.")
    else:
        if data_item > date.today():
            erros.append(
                f"A data em que o objeto foi {verbo} não pode ser futura."
            )

    try:
        datetime.strptime(form.get("horario", ""), "%H:%M")
    except ValueError:
        erros.append("Informe um horário válido.")

    return erros


def dados_do_item(form):
    """Campos do formulário já limpos, prontos para guardar."""
    return {
        "nome": form["nome"].strip(),
        "tipo": form["tipo"],
        "descricao": form["descricao"].strip(),
        "local": form["local"].strip(),
        "data": form["data"],
        "horario": form["horario"],
    }


# --- Área do usuário --------------------------------------------------------
@app.route("/busca")
@login_obrigatorio("usuario")
def busca():
    """Página inicial do usuário: busca de itens perdidos e achados."""
    return render_template("busca.html", tipos=armazenamento.listar_tipos())


@app.route("/api/itens")
def api_itens():
    """Itens para a busca. Futuramente virá da API REST."""
    if session.get("perfil") != "usuario":
        return jsonify({"erro": "Faça login para buscar itens."}), 401
    return jsonify(armazenamento.listar_publicos())


@app.route("/cadastrar-item-perdido", methods=["GET", "POST"])
@login_obrigatorio("usuario")
def cadastrar_item_perdido():
    if request.method == "POST":
        erros = validar_item(request.form)
        if erros:
            for erro in erros:
                flash(erro, "erro")
            return (
                render_template(
                    "cadastrar_item_perdido.html", tipos=armazenamento.listar_tipos()
                ),
                400,
            )

        armazenamento.adicionar(
            tipo_registro="perdido",
            registrado_por=session["usuario_email"],
            **dados_do_item(request.form),
        )
        flash(
            "Item cadastrado com sucesso! Você pode acompanhá-lo em "
            "Meu histórico.",
            "sucesso",
        )
        return redirect(url_for("busca"))

    return render_template("cadastrar_item_perdido.html", tipos=armazenamento.listar_tipos())


def pode_alterar(item, perfil, email):
    """Itens entregues ficam congelados. Admin altera os demais; o usuário, só os seus."""
    if item is None or item["status"] == "entregue":
        return False
    return perfil == "admin" or item["registrado_por"] == email


def _item_alteravel_ou_redireciona(item_id, destino):
    """Devolve (item, None) se o perfil logado pode alterar, senão (None, resposta)."""
    item = armazenamento.obter(item_id)
    if item is None:
        flash("Item não encontrado.", "erro")
        return None, redirect(url_for(destino))
    if not pode_alterar(item, session["perfil"], session["usuario_email"]):
        if item["status"] == "entregue":
            flash("Itens já entregues não podem ser alterados.", "erro")
        else:
            flash("Você só pode alterar os itens registrados por você.", "erro")
        return None, redirect(url_for(destino))
    return item, None


def _editar_item(item_id, destino, template_voltar):
    item, resposta = _item_alteravel_ou_redireciona(item_id, destino)
    if resposta:
        return resposta
    admin = session["perfil"] == "admin"
    acao = url_for("admin_editar_item" if admin else "editar_item", item_id=item_id)

    if request.method == "POST":
        erros = validar_item(request.form, achado=item["tipo_registro"] == "achado")
        if erros:
            for erro in erros:
                flash(erro, "erro")
            enviado = {c: request.form.get(c, "") for c in armazenamento.CAMPOS_EDITAVEIS}
            return (
                render_template(
                    "editar_item.html",
                    item={**item, **enviado},
                    tipos=armazenamento.listar_tipos(),
                    admin=admin,
                    acao=acao,
                    voltar=url_for(destino),
                ),
                400,
            )
        armazenamento.atualizar(item_id, dados_do_item(request.form))
        flash("Item atualizado com sucesso!", "sucesso")
        return redirect(url_for(destino))

    return render_template(
        "editar_item.html",
        item=item,
        tipos=armazenamento.listar_tipos(),
        admin=admin,
        acao=acao,
        voltar=url_for(destino),
    )


def _excluir_item(item_id, destino):
    item, resposta = _item_alteravel_ou_redireciona(item_id, destino)
    if resposta:
        return resposta
    armazenamento.excluir(item_id)
    flash(f"O item \u201c{item['nome']}\u201d foi excluído.", "sucesso")
    return redirect(url_for(destino))


@app.route("/item/<int:item_id>/editar", methods=["GET", "POST"])
@login_obrigatorio("usuario")
def editar_item(item_id):
    return _editar_item(item_id, "historico", "historico")


@app.route("/item/<int:item_id>/excluir", methods=["POST"])
@login_obrigatorio("usuario")
def excluir_item(item_id):
    return _excluir_item(item_id, "historico")


@app.route("/historico")
@login_obrigatorio("usuario")
def historico():
    """Itens registrados pelo usuário e os registros de devolução."""
    itens = armazenamento.listar_do_usuario(session["usuario_email"])
    return render_template("historico.html", itens=itens)


# --- Área do administrador --------------------------------------------------
@app.route("/admin")
@login_obrigatorio("admin")
def admin_painel():
    """Página inicial do administrador."""
    return render_template(
        "admin_inicio.html", contagem=armazenamento.contar_por_status()
    )


@app.route("/admin/cadastrar-item-achado", methods=["GET", "POST"])
@login_obrigatorio("admin")
def cadastrar_item_achado():
    if request.method == "POST":
        erros = validar_item(request.form, achado=True)
        if erros:
            for erro in erros:
                flash(erro, "erro")
            return (
                render_template(
                    "cadastrar_item_achado.html", tipos=armazenamento.listar_tipos()
                ),
                400,
            )

        armazenamento.adicionar(
            tipo_registro="achado",
            registrado_por=session["usuario_email"],
            **dados_do_item(request.form),
        )
        flash(
            "Item achado cadastrado com sucesso! Ele já aparece na busca "
            "dos usuários.",
            "sucesso",
        )
        return redirect(url_for("admin_painel"))

    return render_template("cadastrar_item_achado.html", tipos=armazenamento.listar_tipos())


@app.route("/admin/historico")
@login_obrigatorio("admin")
def admin_historico():
    """Todos os itens perdidos e achados registrados no sistema."""
    return render_template(
        "admin_historico.html",
        itens=armazenamento.listar_todos(),
        contagem=armazenamento.contar_por_status(),
    )


@app.route("/admin/item/<int:item_id>/editar", methods=["GET", "POST"])
@login_obrigatorio("admin")
def admin_editar_item(item_id):
    return _editar_item(item_id, "admin_historico", "admin_historico")


@app.route("/admin/item/<int:item_id>/excluir", methods=["POST"])
@login_obrigatorio("admin")
def admin_excluir_item(item_id):
    return _excluir_item(item_id, "admin_historico")


@app.route("/admin/item/<int:item_id>/entregar", methods=["POST"])
@login_obrigatorio("admin")
def admin_entregar_item(item_id):
    """Marca como entregue e registra quem retirou o objeto."""
    item, resposta = _item_alteravel_ou_redireciona(item_id, "admin_historico")
    if resposta:
        return resposta
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    erros = []
    if len(nome) < 3 or len(nome) > 120:
        erros.append("Informe o nome completo de quem retirou o item.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 120:
        erros.append("Informe um e-mail válido de quem retirou o item.")
    if erros:
        for erro in erros:
            flash(erro, "erro")
        return redirect(url_for("admin_historico"))
    armazenamento.marcar_entregue(item_id, nome, email)
    flash(f"O item \u201c{item['nome']}\u201d foi marcado como entregue.", "sucesso")
    return redirect(url_for("admin_historico"))


@app.route("/admin/tipos", methods=["GET", "POST"])
@login_obrigatorio("admin")
def admin_tipos():
    """Lista os tipos de objeto e permite adicionar novos."""
    if request.method == "POST":
        nome = " ".join(request.form.get("nome", "").split())
        if not nome or len(nome) > 40:
            flash("Informe o nome do tipo (até 40 caracteres).", "erro")
        else:
            erro = armazenamento.adicionar_tipo(nome)
            if erro:
                flash(erro, "erro")
            else:
                flash(f"Tipo \u201c{nome}\u201d adicionado.", "sucesso")
        return redirect(url_for("admin_tipos"))
    return render_template(
        "admin_tipos.html", uso=armazenamento.contar_por_tipo()
    )


@app.route("/admin/tipos/excluir", methods=["POST"])
@login_obrigatorio("admin")
def admin_excluir_tipo():
    nome = request.form.get("nome", "")
    erro = armazenamento.remover_tipo(nome)
    if erro:
        flash(erro, "erro")
    else:
        flash(f"Tipo \u201c{nome}\u201d excluído.", "sucesso")
    return redirect(url_for("admin_tipos"))


if __name__ == "__main__":
    # debug=True recarrega o servidor ao editar arquivos. Desative em produção.
    app.run(debug=True)
