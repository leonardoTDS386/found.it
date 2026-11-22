"""Dados iniciais: tipos de objeto, contas e itens de demonstração."""

from datetime import date, time

from sqlmodel import Session, select

from app.database import engine
from app.models import Item, Perfil, StatusItem, Tipo, TipoRegistro, Usuario
from app.security import hash_senha

TIPOS_INICIAIS = [
    "Acessório", "Eletrônico", "Documento",
    "Material de estudo", "Vestuário", "Outro",
]

EMAIL_ADMIN = "admin@foundit.com"
EMAIL_USUARIO = "usuario@foundit.com"

# PROVISÓRIO: contas de demonstração (as mesmas do site).
CONTAS_INICIAIS = [
    ("Administrador Found.it", EMAIL_ADMIN, "admin123", Perfil.admin),
    ("Leonardo Vínicius", EMAIL_USUARIO, "123456", Perfil.usuario),
]


def _demo(nome, descricao, tipo, local, data, horario, registro,
          devolucao=None, retirado_por=None):
    """Monta um item de exemplo. 'registro' é 'perdido' ou 'achado'."""
    return {
        "nome": nome, "descricao": descricao, "tipo": tipo, "local": local,
        "data": data, "horario": horario, "registro": registro,
        "devolucao": devolucao, "retirado_por": retirado_por,
    }

# Para apresentação
ITENS_INICIAIS = [
    _demo("Garrafa térmica azul", "Garrafa térmica de aço inox, cor azul, com adesivo de montanha na lateral e tampa preta.", "Acessório", "Refeitório", "2026-10-21", "12:40", "perdido"),
    _demo("Fone de ouvido sem fio", "Fone intra-auricular branco, com estojo de carregamento riscado na tampa.", "Eletrônico", "Sala de reuniões 2", "2026-10-20", "16:15", "achado"),
    _demo("Carteira marrom", "Carteira de couro marrom com zíper. Contém cartões e documentos.", "Documento", "Recepção", "2026-10-20", "09:05", "achado"),
    _demo("Chaves com chaveiro", "Três chaves em um chaveiro de metal em formato de estrela.", "Acessório", "Estacionamento", "2026-10-19", "18:30", "perdido"),
    _demo("Celular Samsung preto", "Celular Samsung preto com capinha transparente e tela trincada no canto.", "Eletrônico", "Auditório", "2026-10-19", "14:20", "achado"),
    _demo("Guarda-chuva preto", "Guarda-chuva preto, automático, com cabo emborrachado.", "Acessório", "Recepção", "2026-10-16", "17:50", "perdido"),
    _demo("Mochila cinza", "Mochila cinza com zíperes pretos e um chaveiro de panda pendurado.", "Vestuário", "Biblioteca", "2026-10-15", "11:10", "perdido"),
    _demo("Óculos de grau", "Óculos de grau com armação preta redonda, dentro de um estojo azul.", "Acessório", "Corredor do 2º andar", "2026-10-14", "10:30", "achado"),
    _demo("Carregador de notebook", "Carregador de notebook preto, 65W, com cabo enrolado por velcro.", "Eletrônico", "Sala de reuniões 2", "2026-10-13", "15:00", "perdido"),
    _demo("Calculadora científica", "Calculadora científica cinza com capa deslizante e nome escrito no verso.", "Material de estudo", "Biblioteca", "2026-10-12", "09:40", "perdido",
          devolucao="2026-10-13", retirado_por=("Leonardo Vínicius", EMAIL_USUARIO)),
    _demo("Caderno universitário", "Caderno universitário de capa vermelha, 10 matérias, com anotações de cálculo.", "Material de estudo", "Biblioteca", "2026-10-09", "13:25", "achado"),
    _demo("Garrafa de água transparente", "Garrafa plástica transparente, devolvida ao dono.", "Acessório", "Refeitório", "2026-10-08", "12:00", "achado",
          devolucao="2026-10-09", retirado_por=("Marcos Oliveira", "marcos.oliveira@exemplo.com")),
    _demo("Casaco de moletom azul", "Casaco de moletom azul-marinho com capuz e logotipo branco no peito.", "Vestuário", "Refeitório", "2026-10-07", "19:15", "achado"),
    _demo("Cartão de acesso", "Cartão de acesso magnético com foto, preso a um cordão verde.", "Documento", "Recepção", "2026-10-05", "08:45", "perdido"),
]


def _popular_itens(session: Session):
    """Cria os itens de exemplo, mas só se a tabela de itens estiver vazia."""
    if session.exec(select(Item)).first():
        return

    tipos = {t.nome: t.id for t in session.exec(select(Tipo)).all()}
    ids = {u.email: u.id for u in session.exec(select(Usuario)).all()}

    for d in ITENS_INICIAIS:
        entregue = d["devolucao"] is not None
        dono = EMAIL_USUARIO if d["registro"] == "perdido" else EMAIL_ADMIN
        nome_retirou, email_retirou = d["retirado_por"] or (None, None)
        session.add(
            Item(
                nome=d["nome"],
                descricao=d["descricao"],
                local=d["local"],
                data=date.fromisoformat(d["data"]),
                horario=time.fromisoformat(d["horario"]),
                tipo_id=tipos[d["tipo"]],
                status=StatusItem.entregue if entregue else StatusItem(d["registro"]),
                tipo_registro=TipoRegistro(d["registro"]),
                registrado_por_id=ids[dono],
                data_registro=date.fromisoformat(d["data"]),
                data_devolucao=date.fromisoformat(d["devolucao"]) if entregue else None,
                retirado_por_nome=nome_retirou,
                retirado_por_email=email_retirou,
            )
        )
    session.commit()


def popular_banco():
    with Session(engine) as session:
        for nome in TIPOS_INICIAIS:
            if not session.exec(select(Tipo).where(Tipo.nome == nome)).first():
                session.add(Tipo(nome=nome))

        for nome, email, senha, perfil in CONTAS_INICIAIS:
            if not session.exec(select(Usuario).where(Usuario.email == email)).first():
                session.add(
                    Usuario(nome=nome, email=email, senha_hash=hash_senha(senha), perfil=perfil)
                )
        session.commit()

        _popular_itens(session)