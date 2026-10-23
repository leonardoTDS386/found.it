/* Found.it - Página de busca de itens
 *
 * Por enquanto os itens vêm de um arquivo de exemplo (static/data/itens.json).
 * Quando a API REST estiver pronta, só a função buscarItens() precisa mudar.
 */
(function () {
  "use strict";

  const form = document.getElementById("busca-form");
  const botao = document.getElementById("busca-botao");
  const rotuloBotao = botao.querySelector(".rotulo");
  const area = document.getElementById("resultados");
  const campoNome = document.getElementById("nome");
  const campoTipo = document.getElementById("tipo");
  const campoLocal = document.getElementById("local");
  const campoData = document.getElementById("data");

  const modalEl = document.getElementById("item-modal");
  const modal = new bootstrap.Modal(modalEl);
  const botaoSolicitar = document.getElementById("modal-solicitar");
  const avisoModal = document.getElementById("modal-aviso");

  let itensEncontrados = [];

  // A data da busca não pode ser no futuro (usa o dia local do usuário).
  campoData.max = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 10);

  // ---------- Utilitários ----------
  // Ignora maiúsculas, minúsculas e acentos ("Óculos" encontra "oculos").
  const normaliza = (texto) =>
    (texto || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .trim();

  function formataData(iso) {
    const [ano, mes, dia] = iso.split("-");
    return dia + "/" + mes + "/" + ano;
  }

  // Cria elementos com textContent (nunca innerHTML), para evitar injeção de HTML.
  function criar(tag, classe, texto) {
    const el = document.createElement(tag);
    if (classe) el.className = classe;
    if (texto !== undefined) el.textContent = texto;
    return el;
  }

  function icone(nome) {
    const i = criar("i", "bi " + nome);
    i.setAttribute("aria-hidden", "true");
    return i;
  }

  const STATUS = { perdido: "Perdido", achado: "Achado", entregue: "Entregue" };

  // Tipo do objeto (aceita "categoria" para compatibilidade com dados antigos).
  const tipoDoItem = (item) => item.tipo || item.categoria || "Não informado";

  // ---------- Acesso aos dados ----------
  // TODO: trocar por uma chamada à API REST, por exemplo:
  //   GET /api/itens?nome=...&tipo=...&local=...&data=...
  async function buscarItens(filtros) {
    const resposta = await fetch(form.dataset.itensUrl);
    if (!resposta.ok) throw new Error("Falha ao carregar os itens.");
    const itens = await resposta.json();

    return itens.filter(function (item) {
      // Itens já entregues ficam só no histórico, não aparecem na busca.
      if (item.status === "entregue") return false;
      if (filtros.nome && !normaliza(item.nome).includes(filtros.nome))
        return false;
      if (filtros.tipo && normaliza(tipoDoItem(item)) !== filtros.tipo)
        return false;
      if (filtros.local && !normaliza(item.local).includes(filtros.local))
        return false;
      if (filtros.data && item.data !== filtros.data) return false;
      return true;
    });
  }

  // ---------- Exibição dos resultados ----------
  function mostrarVazio() {
    const bloco = criar("div", "estado-vazio");
    bloco.appendChild(icone("bi-emoji-frown"));
    bloco.appendChild(criar("h2", null, "Nenhum item encontrado"));
    bloco.appendChild(
      criar(
        "p",
        null,
        "Não encontramos nenhum item com os dados informados. " +
          "Confira o nome, o tipo, o local e a data, ou tente buscar com menos filtros.",
      ),
    );

    const link = criar("a", "btn btn-outline-primary btn-sm");
    link.href = form.dataset.cadastrarUrl;
    link.appendChild(icone("bi-plus-circle"));
    link.appendChild(document.createTextNode(" Cadastrar item perdido"));
    bloco.appendChild(link);

    area.replaceChildren(bloco);
  }

  function mostrarErro() {
    const bloco = criar("div", "estado-vazio");
    bloco.appendChild(icone("bi-exclamation-triangle"));
    bloco.appendChild(criar("h2", null, "Não foi possível buscar agora"));
    bloco.appendChild(
      criar(
        "p",
        null,
        "Ocorreu um erro ao carregar os itens. Tente novamente em instantes.",
      ),
    );
    area.replaceChildren(bloco);
  }

  function criarCartao(item) {
    const coluna = criar("div", "col");

    const cartao = criar("button", "item-card");
    cartao.type = "button";
    cartao.dataset.id = item.id;
    cartao.setAttribute("aria-label", item.nome + " - ver detalhes");

    const iconeBox = criar("span", "item-card-icon");
    iconeBox.appendChild(icone("bi-box-seam"));

    const corpo = criar("span", "item-card-body");
    corpo.appendChild(criar("strong", "item-card-nome", item.nome));

    const data = criar("span", "item-card-meta");
    data.appendChild(icone("bi-calendar-event"));
    data.appendChild(criar("span", null, formataData(item.data)));
    corpo.appendChild(data);

    const local = criar("span", "item-card-meta");
    local.appendChild(icone("bi-geo-alt"));
    local.appendChild(criar("span", null, item.local));
    corpo.appendChild(local);

    const tipo = criar("span", "item-card-meta");
    tipo.appendChild(icone("bi-grid"));
    tipo.appendChild(criar("span", null, tipoDoItem(item)));
    corpo.appendChild(tipo);

    cartao.appendChild(iconeBox);
    cartao.appendChild(corpo);
    cartao.appendChild(icone("bi-chevron-right item-card-seta"));
    coluna.appendChild(cartao);
    return coluna;
  }

  function mostrarResultados(itens) {
    const total = itens.length;
    const titulo = criar(
      "h2",
      "resultados-titulo",
      total + (total === 1 ? " item encontrado" : " itens encontrados"),
    );

    const grade = criar(
      "div",
      "row row-cols-1 row-cols-md-2 row-cols-xl-3 g-3",
    );
    itens.forEach(function (item) {
      grade.appendChild(criarCartao(item));
    });

    area.replaceChildren(titulo, grade);
  }

  // ---------- Balão de detalhes ----------
  function abrirDetalhes(id) {
    const item = itensEncontrados.find(function (i) {
      return String(i.id) === String(id);
    });
    if (!item) return;

    const achado = item.status === "achado";
    const verbo = achado ? "achado" : "perdido";

    document.getElementById("modal-nome").textContent = item.nome;

    const status = document.getElementById("modal-status");
    status.className = "badge badge-status mb-2 " + item.status;
    status.textContent = STATUS[item.status] || item.status;

    document.getElementById("modal-tipo-objeto").textContent = tipoDoItem(item);
    document.getElementById("modal-registro").textContent = achado
      ? "Item achado (registrado pelo administrador)"
      : "Item perdido (registrado por um usuário)";
    document.getElementById("modal-descricao").textContent = item.descricao;
    document.getElementById("modal-local-rotulo").textContent =
      "Local onde foi " + verbo;
    document.getElementById("modal-local").textContent = item.local;
    document.getElementById("modal-data-rotulo").textContent =
      "Data e horário em que foi " + verbo;
    document.getElementById("modal-data").textContent =
      formataData(item.data) + " às " + item.horario;

    // Só itens achados podem ter a devolução solicitada.
    botaoSolicitar.classList.toggle("d-none", !achado);
    avisoModal.classList.add("d-none");

    modal.show();
  }

  area.addEventListener("click", function (evento) {
    const cartao = evento.target.closest(".item-card");
    if (cartao) abrirDetalhes(cartao.dataset.id);
  });

  // Ainda não foi decidido como a solicitação será feita (fica para o back-end).
  botaoSolicitar.addEventListener("click", function () {
    avisoModal.textContent =
      "A solicitação de devolução será habilitada quando o back-end " +
      "estiver conectado.";
    avisoModal.classList.remove("d-none");
  });

  // ---------- Envio da busca ----------
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const filtros = {
      nome: normaliza(campoNome.value),
      tipo: normaliza(campoTipo.value),
      local: normaliza(campoLocal.value),
      data: campoData.value,
    };

    botao.disabled = true;
    rotuloBotao.textContent = "Buscando...";

    try {
      itensEncontrados = await buscarItens(filtros);
      if (itensEncontrados.length === 0) {
        mostrarVazio();
      } else {
        mostrarResultados(itensEncontrados);
      }
    } catch (erro) {
      mostrarErro();
    } finally {
      botao.disabled = false;
      rotuloBotao.textContent = "Buscar";
    }
  });
})();
