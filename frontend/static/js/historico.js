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

  let filtroAtual = "todos";

  function aplicar(filtro) {
    let visiveis = 0;
    filtroAtual = filtro;
    registros.forEach(function (registro) {
            const mostrar =
        filtro === "todos" ||
        (filtro === "solicitado"
          ? registro.dataset.solicitado === "sim"
          : registro.dataset.status === filtro);
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

    // Vindo dos containers da página inicial: /admin/historico?status=achado
    const pedido = new URLSearchParams(window.location.search).get("status");
    if (pedido && ["perdido", "achado", "entregue", "solicitado"].includes(pedido)) {
      aplicar(pedido);
    }
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

    // ---------- Solicitações de devolução (só no balão do administrador) ----------
  const URL_ITENS_ADMIN = "/api/admin/itens/";
  const caixaSolicitacoes = $("modal-solicitacoes");
  const rotuloSolicitacoes = $("modal-solicitacoes-rotulo");
  let itemAberto = null;

  // Lista quem pediu o item, cada um com um botão "Recusar".
  function mostrarSolicitantes(item) {
    if (!caixaSolicitacoes) return;
    const lista = item.status === "achado" ? item.solicitacoes || [] : [];
    rotuloSolicitacoes.hidden = lista.length === 0;
    caixaSolicitacoes.hidden = lista.length === 0;
    caixaSolicitacoes.replaceChildren();

    const ul = document.createElement("ul");
    ul.className = "solicitantes-lista";
    lista.forEach(function (s) {
      const li = document.createElement("li");

      const info = document.createElement("div");
      const nome = document.createElement("strong");
      nome.textContent = s.usuario.nome;
      const detalhe = document.createElement("small");
      detalhe.textContent = s.usuario.email + " · " + formataData(s.criada_em);
      info.append(nome, detalhe);

      const botao = document.createElement("button");
      botao.type = "button";
      botao.className = "btn btn-outline-danger btn-sm";
      botao.dataset.usuario = s.usuario_id;
      botao.textContent = "Recusar";

      li.append(info, botao);
      ul.appendChild(li);
    });

    const erro = document.createElement("p");
    erro.className = "solicitacao-erro text-danger small mb-0 mt-2";
    erro.hidden = true;

    caixaSolicitacoes.append(ul, erro);
  }

  // Depois de recusar: tira o selo do cartão e acerta o número do filtro.
  function atualizarMarcas(item) {
    const cartao = document.querySelector(
      '.historico-card[data-id="' + item.id + '"]',
    );
    if (cartao && item.solicitacoes.length === 0) {
      cartao.dataset.solicitado = "nao";
      const selo = cartao.querySelector(".badge-solicitado");
      if (selo) selo.remove();
    }

    const total = itens.filter(function (i) {
      return i.status === "achado" && i.solicitacoes && i.solicitacoes.length;
    }).length;
    const numero = document.querySelector('[data-filtro="solicitado"] span');
    if (numero) numero.textContent = total;

    if (botoes.length && contador) aplicar(filtroAtual);
  }

  if (caixaSolicitacoes) {
    caixaSolicitacoes.addEventListener("click", async function (evento) {
      const botao = evento.target.closest("button[data-usuario]");
      if (!botao || !itemAberto) return;

      const erro = caixaSolicitacoes.querySelector(".solicitacao-erro");
      erro.hidden = true;
      botao.disabled = true;

      try {
        const resposta = await fetch(
          URL_ITENS_ADMIN +
            itemAberto.id +
            "/solicitacoes/" +
            botao.dataset.usuario,
          { method: "DELETE" },
        );
        if (!resposta.ok) {
          let corpo = null;
          try {
            corpo = await resposta.json();
          } catch (e) {
            /* resposta sem JSON */
          }
          throw new Error(
            (corpo && corpo.erro) || "Não foi possível recusar agora.",
          );
        }
        itemAberto.solicitacoes = itemAberto.solicitacoes.filter(function (s) {
          return String(s.usuario_id) !== botao.dataset.usuario;
        });
        mostrarSolicitantes(itemAberto);
        atualizarMarcas(itemAberto);
      } catch (e) {
        erro.textContent = e.message;
        erro.hidden = false;
        botao.disabled = false;
      }
    });
  }

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
    
    itemAberto = item;
    mostrarSolicitantes(item);

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
