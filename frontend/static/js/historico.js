/* Found.it - Históricos (usuário e administrador)
 * - Filtra os registros por status (só existe no histórico do administrador).
 * - Abre o balão com os detalhes e as ações (editar, excluir, marcar como entregue).
 * Os dados vêm do JSON embutido na página (#historico-dados).
 * Elementos são preenchidos com textContent (nunca innerHTML).
 */
(function () {
  "use strict";

  const STATUS = { perdido: "Perdido", achado: "Achado", entregue: "Entregue" };

  function formataData(iso) {
    if (!iso) return "—";
    const [ano, mes, dia] = iso.split("-");
    return dia + "/" + mes + "/" + ano;
  }

  // ---------- Filtros ----------
  const botoes = document.querySelectorAll("[data-filtro]");
  const registros = document.querySelectorAll(".historico-card");
  const contador = document.getElementById("historico-contador");
  const vazio = document.getElementById("historico-filtro-vazio");

  function aplicar(filtro) {
    let visiveis = 0;
    registros.forEach(function (registro) {
      const mostrar = filtro === "todos" || registro.dataset.status === filtro;
      registro.hidden = !mostrar;
      if (mostrar) visiveis += 1;
    });
    botoes.forEach(function (botao) {
      const ativo = botao.dataset.filtro === filtro;
      botao.classList.toggle("ativo", ativo);
      botao.setAttribute("aria-pressed", String(ativo));
    });
    contador.textContent = visiveis + (visiveis === 1 ? " registro" : " registros");
    if (vazio) vazio.hidden = visiveis !== 0;
  }

  if (botoes.length && contador) {
    botoes.forEach(function (botao) {
      botao.addEventListener("click", function () {
        aplicar(botao.dataset.filtro);
      });
    });
  }

  // ---------- Balão de detalhes ----------
  const modalEl = document.getElementById("item-modal");
  const dadosEl = document.getElementById("historico-dados");
  if (!modalEl || !dadosEl) return;

  const itens = JSON.parse(dadosEl.textContent);
  const modal = new bootstrap.Modal(modalEl);
  const admin = modalEl.dataset.admin === "sim";
  const $ = (id) => document.getElementById(id);

  const painelEntregar = $("painel-entregar");
  const painelExcluir = $("painel-excluir");
  const acoes = $("modal-acoes");
  const paineis = [painelEntregar, painelExcluir].filter(Boolean);

  const urlDe = (modelo, id) => modelo.replace("/0/", "/" + id + "/");

  function fecharPaineis() {
    paineis.forEach(function (p) {
      p.hidden = true;
    });
    acoes.hidden = false;
  }

  function abrirPainel(painel) {
    fecharPaineis();
    painel.hidden = false;
    acoes.hidden = true;
    const campo = painel.querySelector("input");
    if (campo) campo.focus();
  }

  function abrir(id) {
    const item = itens.find(function (i) {
      return String(i.id) === String(id);
    });
    if (!item) return;

    const achado = item.tipo_registro === "achado";
    const verbo = achado ? "achado" : "perdido";
    const entregue = item.status === "entregue";

    $("modal-nome").textContent = item.nome;
    const status = $("modal-status");
    status.className = "badge badge-status mb-2 " + item.status;
    status.textContent = STATUS[item.status] || item.status;

    $("modal-tipo-objeto").textContent = item.tipo;
    $("modal-registro").textContent = achado
      ? "Item achado (registrado pelo administrador)"
      : "Item perdido (registrado por um usuário)";
    $("modal-descricao").textContent = item.descricao;
    $("modal-local-rotulo").textContent = "Local onde foi " + verbo;
    $("modal-local").textContent = item.local;
    $("modal-data-rotulo").textContent = "Data e horário em que foi " + verbo;
    $("modal-data").textContent = formataData(item.data) + " às " + item.horario;
    $("modal-data-registro").textContent = formataData(item.data_registro);
    $("modal-devolucao").textContent = formataData(item.data_devolucao);

    const retirado = $("modal-retirado");
    if (retirado) {
      retirado.textContent = item.retirado_por_nome
        ? item.retirado_por_nome + " (" + item.retirado_por_email + ")"
        : "—";
    }

    // Data da devolução e quem retirou só fazem sentido para itens entregues.
    modalEl.querySelectorAll(".grupo-entregue").forEach(function (el) {
      el.hidden = !entregue;
    });
    $("modal-bloqueado").hidden = !entregue;
    acoes.hidden = entregue;

    fecharPaineis();
    acoes.hidden = entregue;

    $("acao-editar").href = urlDe(modalEl.dataset.urlEditar, item.id);
    painelExcluir.action = urlDe(modalEl.dataset.urlExcluir, item.id);
    if (admin) painelEntregar.action = urlDe(modalEl.dataset.urlEntregar, item.id);

    modal.show();
  }

  document.addEventListener("click", function (evento) {
    const cartao = evento.target.closest(".historico-card");
    if (cartao) abrir(cartao.dataset.id);
  });

  $("acao-excluir").addEventListener("click", function () {
    abrirPainel(painelExcluir);
  });
  if (admin) {
    $("acao-entregar").addEventListener("click", function () {
      painelEntregar.reset();
      abrirPainel(painelEntregar);
    });
    painelEntregar.addEventListener("submit", function (evento) {
      if (!painelEntregar.checkValidity()) {
        evento.preventDefault();
        painelEntregar.reportValidity();
      }
    });
  }
  modalEl.querySelectorAll("[data-fechar-painel]").forEach(function (b) {
    b.addEventListener("click", fecharPaineis);
  });
})();
