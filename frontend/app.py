"""Found.it - Sistema de achados e perdidos.

Servidor Flask do front-end. Ele serve as páginas e conversa com a API REST
(pasta backend) por meio do api_cliente.py. Os tokens de acesso ficam na
sessão do Flask
"""

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


import api_cliente
from api_cliente import ApiIndisponivel, ErroApi, SessaoExpirada

app = Flask(__name__)

# Chave usada para assinar a sessão. Em produção, defina FOUNDIT_SECRET_KEY.
app.secret_key = os.environ.get(
    "FOUNDIT_SECRET_KEY", "foundit-chave-provisoria-de-desenvolvimento"
)

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

MENSAGEM_API_FORA = "Não foi possível falar com o servidor agora. Tente novamente em instantes."

# --- Contas provisórias -----------------------------------------------------
"""CONTAS_PROVISORIAS = [
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
]"""

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


def nomes_dos_tipos():
    """Nomes dos tipos de objeto, vindos da API (para listas e validação)."""
    return [t["nome"] for t in api_cliente.listar_tipos()]


def item_do_site(item):
    """Converte um item da API para o formato que os templates e scripts usam."""
    convertido = dict(item)
    convertido["tipo"] = item["tipo"]["nome"]      # a API manda {id, nome}
    convertido["horario"] = item["horario"][:5]    # "12:30:00" -> "12:30"
    return convertido


def tipo_id_por_nome(nome):
    """Id do tipo na API, ou None se não existir."""
    return next(
        (t["id"] for t in api_cliente.listar_tipos() if t["nome"] == nome), None
    )


def buscar_item_para_alterar(item_id):
    """Item no formato do site, ou None se não existir ou não for do usuário."""
    try:
        if session["perfil"] == "admin":
            item = api_cliente.requisitar("GET", f"/api/admin/itens/{item_id}")
        else:
            meus = api_cliente.requisitar("GET", "/api/itens/meus")
            item = next((i for i in meus if i["id"] == item_id), None)
    except ErroApi as erro:
        if erro.status == 404:
            return None
        raise
    return item_do_site(item) if item else None


def cadastrar_pela_api(form, achado=False):
    """Valida e cadastra o item pela API. Devolve a lista de erros (vazia se deu certo)."""
    erros = validar_item(form, achado=achado)
    if erros:
        return erros

    dados = dados_do_item(form)
    nome_do_tipo = dados.pop("tipo")      # tira o nome do tipo uma única vez
    tipo_id = next(
        (t["id"] for t in api_cliente.listar_tipos() if t["nome"] == nome_do_tipo),
        None,
    )
    if tipo_id is None:
        return ["Selecione um tipo de objeto válido."]
    dados["tipo_id"] = tipo_id

    try:
        api_cliente.requisitar("POST", "/api/itens", json=dados)
    except (ApiIndisponivel, SessaoExpirada):
        raise
    except ErroApi as erro:
        return [erro.mensagem]
    return []


# --- Autenticação -----------------------------------------------------------
def autenticar(perfil, email, senha):
    """Entra pela API. Devolve (usuario, tokens) ou None se não servir para o perfil."""
    try:
        tokens, usuario = api_cliente.entrar(email.strip(), senha)
    except ApiIndisponivel:
        raise
    except ErroApi as erro:
        if erro.status in (401, 422):    # senha errada ou e-mail em formato inválido
            return None
        raise

    if usuario["perfil"] != perfil:
        # Ex.: conta de administrador tentando entrar pelo login de usuário.
        api_cliente.sair(tokens["refresh_token"])
        return None
    return usuario, tokens


def iniciar_sessao(usuario, tokens):
    session.clear()
    session["usuario_nome"] = usuario["nome"]
    session["usuario_email"] = usuario["email"]
    session["perfil"] = usuario["perfil"]
    session["token_acesso"] = tokens["access_token"]
    session["token_refresh"] = tokens["refresh_token"]


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
        try:
            resultado = autenticar("usuario", email, request.form.get("senha", ""))
        except ApiIndisponivel:
            flash(MENSAGEM_API_FORA, "erro")
            return render_template("login.html", email=email), 503
        if resultado:
            usuario, tokens = resultado
            iniciar_sessao(usuario, tokens)
            primeiro_nome = usuario["nome"].split()[0]
            flash(
                f"Boas-vindas ao Found.it, {primeiro_nome}! "
                "Procure seus objetos ou cadastre um item perdido.",
                "boas-vindas",
            )
            return redirect(url_for("busca"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("login.html", email=email)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        erros = validar_cadastro(request.form)
        if not erros:
            try:
                api_cliente.cadastrar_usuario(dados_do_cadastro(request.form))
            except ApiIndisponivel:
                erros = [MENSAGEM_API_FORA]
            except ErroApi as erro:
                erros = [erro.mensagem]

        if erros:
            for mensagem in erros:
                flash(mensagem, "erro")
            return render_template("cadastro.html", valores=request.form), 400

        flash("Cadastro realizado com sucesso! Entre com seu e-mail e senha.", "sucesso")
        return redirect(url_for("login"))

    return render_template("cadastro.html", valores={})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        try:
            resultado = autenticar("admin", email, request.form.get("senha", ""))
        except ApiIndisponivel:
            flash(MENSAGEM_API_FORA, "erro")
            return render_template("admin_login.html", email=email), 503
        if resultado:
            usuario, tokens = resultado
            iniciar_sessao(usuario, tokens)
            flash("Boas-vindas ao Found.it, Administrador!", "boas-vindas")
            return redirect(url_for("admin_painel"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("admin_login.html", email=email)


@app.route("/logout")
def logout():
    destino = "admin_login" if session.get("perfil") == "admin" else "login"
    api_cliente.sair(session.get("token_refresh"))   # revoga o refresh na API
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

    if form.get("tipo") not in nomes_dos_tipos():
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


def cpf_valido(cpf):
    """CPF com 11 dígitos e dígitos verificadores corretos (mesma regra do site)."""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for t in (9, 10):
        soma = sum(int(cpf[i]) * (t + 1 - i) for i in range(t))
        if ((soma * 10) % 11) % 10 != int(cpf[t]):
            return False
    return True


def validar_cadastro(form):
    """Valida o cadastro no servidor. Devolve a lista de erros."""
    erros = []

    nome = " ".join(form.get("nome", "").split())
    if len(nome.split()) < 2 or len(nome) > 150:
        erros.append("Informe nome e sobrenome.")

    email = form.get("email", "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 120:
        erros.append("Informe um e-mail válido.")

    if not cpf_valido(re.sub(r"\D", "", form.get("cpf", ""))):
        erros.append("Informe um CPF válido.")

    telefone = form.get("telefone", "").strip()
    if len(re.sub(r"\D", "", telefone)) not in (10, 11) or len(telefone) > 20:
        erros.append("Informe um telefone válido com DDD.")

    endereco = form.get("endereco", "").strip()
    if len(endereco) < 10 or len(endereco) > 255:
        erros.append("Informe o endereço completo.")

    senha = form.get("senha", "")
    if (
        len(senha) < 8
        or len(senha) > 128
        or not re.search(r"[A-Za-z]", senha)
        or not re.search(r"\d", senha)
    ):
        erros.append("A senha deve ter pelo menos 8 caracteres, com letras e números.")
    elif senha != form.get("senha2", ""):
        erros.append("As senhas não coincidem.")

    if not form.get("consentimento"):
        erros.append("É necessário autorizar o uso dos dados para criar a conta.")

    return erros


def dados_do_cadastro(form):
    """Campos do cadastro já limpos, no formato que a API espera."""
    cpf = re.sub(r"\D", "", form["cpf"])
    return {
        "nome": " ".join(form["nome"].split()),
        "email": form["email"].strip().lower(),
        "cpf": f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}",
        "telefone": form["telefone"].strip(),
        "endereco": form["endereco"].strip(),
        "senha": form["senha"],
    }


# --- Área do usuário --------------------------------------------------------
@app.route("/busca")
@login_obrigatorio("usuario")
def busca():
    """Página inicial do usuário: busca de itens perdidos e achados."""
    return render_template("busca.html", tipos=nomes_dos_tipos())


@app.route("/api/itens")
def api_itens():
    """Itens para a busca, vindos da API."""
    if session.get("perfil") != "usuario":
        return jsonify({"erro": "Faça login para buscar itens."}), 401
    itens = api_cliente.requisitar("GET", "/api/itens")
    return jsonify([item_do_site(i) for i in itens])


@app.route("/cadastrar-item-perdido", methods=["GET", "POST"])
@login_obrigatorio("usuario")
def cadastrar_item_perdido():
    if request.method == "POST":
        erros = cadastrar_pela_api(request.form)
        if erros:
            for erro in erros:
                flash(erro, "erro")
            return (
                render_template("cadastrar_item_perdido.html", tipos=nomes_dos_tipos()),
                400,
            )
        flash(
            "Item cadastrado com sucesso! Você pode acompanhá-lo em Meu histórico.",
            "sucesso",
        )
        return redirect(url_for("busca"))

    return render_template("cadastrar_item_perdido.html", tipos=nomes_dos_tipos())


def _editar_item(item_id, destino, template_voltar):
    item = buscar_item_para_alterar(item_id)
    if item is None:
        flash("Item não encontrado.", "erro")
        return redirect(url_for(destino))
    if item["status"] == "entregue":
        flash("Itens já entregues não podem ser alterados.", "erro")
        return redirect(url_for(destino))

    admin = session["perfil"] == "admin"
    acao = url_for("admin_editar_item" if admin else "editar_item", item_id=item_id)

    def mostrar(item_exibido, codigo=200):
        return (
            render_template(
                "editar_item.html",
                item=item_exibido,
                tipos=nomes_dos_tipos(),
                admin=admin,
                acao=acao,
                voltar=url_for(destino),
            ),
            codigo,
        )

    if request.method == "POST":
        erros = validar_item(request.form, achado=item["tipo_registro"] == "achado")
        if not erros:
            dados = dados_do_item(request.form)
            tipo_id = tipo_id_por_nome(dados.pop("tipo"))
            if tipo_id is None:
                erros = ["Selecione um tipo de objeto válido."]
            else:
                dados["tipo_id"] = tipo_id
                try:
                    api_cliente.requisitar("PUT", f"/api/itens/{item_id}", json=dados)
                except (ApiIndisponivel, SessaoExpirada):
                    raise
                except ErroApi as erro:
                    erros = [erro.mensagem]

        if erros:
            for mensagem in erros:
                flash(mensagem, "erro")
            campos = ("nome", "tipo", "descricao", "local", "data", "horario")
            enviado = {c: request.form.get(c, "") for c in campos}
            return mostrar({**item, **enviado}, 400)

        flash("Item atualizado com sucesso!", "sucesso")
        return redirect(url_for(destino))

    return mostrar(item)


def _excluir_item(item_id, destino):
    try:
        api_cliente.requisitar("DELETE", f"/api/itens/{item_id}")
    except (ApiIndisponivel, SessaoExpirada):
        raise
    except ErroApi as erro:
        flash(erro.mensagem, "erro")
    else:
        flash("Item excluído com sucesso.", "sucesso")
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
    """Itens registrados pelo usuário."""
    itens = api_cliente.requisitar("GET", "/api/itens/meus")
    return render_template("historico.html", itens=[item_do_site(i) for i in itens])


# --- Área do administrador --------------------------------------------------
@app.route("/admin")
@login_obrigatorio("admin")
def admin_painel():
    """Página inicial do administrador."""
    contagem = api_cliente.requisitar("GET", "/api/admin/resumo")
    return render_template("admin_inicio.html", contagem=contagem)

@app.route("/admin/cadastrar-item-achado", methods=["GET", "POST"])
@login_obrigatorio("admin")
def cadastrar_item_achado():
    if request.method == "POST":
        erros = cadastrar_pela_api(request.form, achado=True)
        if erros:
            for erro in erros:
                flash(erro, "erro")
            return (
                render_template("cadastrar_item_achado.html", tipos=nomes_dos_tipos()),
                400,
            )
        flash(
            "Item achado cadastrado com sucesso! Ele já aparece na busca dos usuários.",
            "sucesso",
        )
        return redirect(url_for("admin_painel"))

    return render_template("cadastrar_item_achado.html", tipos=nomes_dos_tipos())


@app.route("/admin/historico")
@login_obrigatorio("admin")
def admin_historico():
    """Todos os itens perdidos e achados registrados no sistema."""
    itens = api_cliente.requisitar("GET", "/api/admin/itens")
    contagem = api_cliente.requisitar("GET", "/api/admin/resumo")
    return render_template(
        "admin_historico.html",
        itens=[item_do_site(i) for i in itens],
        contagem=contagem,
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
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()

    erros = []
    if len(nome) < 3 or len(nome) > 120:
        erros.append("Informe o nome completo de quem retirou o item.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 120:
        erros.append("Informe um e-mail válido de quem retirou o item.")
    if erros:
        for mensagem in erros:
            flash(mensagem, "erro")
        return redirect(url_for("admin_historico"))

    try:
        api_cliente.requisitar(
            "POST",
            f"/api/admin/itens/{item_id}/entregar",
            json={"nome": nome, "email": email},
        )
    except (ApiIndisponivel, SessaoExpirada):
        raise
    except ErroApi as erro:
        flash(erro.mensagem, "erro")
    else:
        flash("O item foi marcado como entregue.", "sucesso")
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
            try:
                api_cliente.requisitar("POST", "/api/tipos", json={"nome": nome})
            except (ApiIndisponivel, SessaoExpirada):
                raise
            except ErroApi as erro:
                flash(erro.mensagem, "erro")
            else:
                flash(f"Tipo \u201c{nome}\u201d adicionado.", "sucesso")
        return redirect(url_for("admin_tipos"))

    tipos = api_cliente.requisitar("GET", "/api/tipos/uso")
    uso = {t["nome"]: t["quantidade_itens"] for t in tipos}
    return render_template("admin_tipos.html", uso=uso)


@app.route("/admin/tipos/excluir", methods=["POST"])
@login_obrigatorio("admin")
def admin_excluir_tipo():
    nome = request.form.get("nome", "")
    tipo_id = tipo_id_por_nome(nome)
    if tipo_id is None:
        flash("Tipo de objeto não encontrado.", "erro")
    else:
        try:
            api_cliente.requisitar("DELETE", f"/api/tipos/{tipo_id}")
        except (ApiIndisponivel, SessaoExpirada):
            raise
        except ErroApi as erro:
            flash(erro.mensagem, "erro")
        else:
            flash(f"Tipo \u201c{nome}\u201d excluído.", "sucesso")
    return redirect(url_for("admin_tipos"))


@app.errorhandler(SessaoExpirada)
def sessao_expirada(_erro):
    """O token venceu e não deu para renovar: volta ao login."""
    if request.path.startswith("/api/"):
        return jsonify({"erro": "Sessão expirada."}), 401
    destino = "admin_login" if session.get("perfil") == "admin" else "login"
    session.clear()
    flash("Sua sessão expirou. Entre novamente.", "erro")
    return redirect(url_for(destino))


@app.errorhandler(ApiIndisponivel)
def api_indisponivel(_erro):
    """A API está fora do ar."""
    if request.path.startswith("/api/"):
        return jsonify({"erro": MENSAGEM_API_FORA}), 503
    return render_template("erro_api.html"), 503

if __name__ == "__main__":
    # debug=True recarrega o servidor ao editar arquivos. Desative em produção.
    app.run(debug=True)
