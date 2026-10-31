// View: telas da livraria. Só transforma dados em HTML; não chama o servidor nem trata eventos.
// Cada formulário leva data-acao="..." para o Controller saber o que fazer quando for enviado.

const e = (texto) => String(texto ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const reais = (centavos) =>
  "R$ " + (centavos / 100).toFixed(2).replace(".", ",").replace(/\B(?=(\d{3})+(?!\d))/g, ".");

const notaMedia = (media) => (media === null ? "sem avaliações" : media.toFixed(1).replace(".", ","));

const pedido = (edicaoId, lojaId) =>
  `<input type="hidden" name="edicao_id" value="${e(edicaoId)}"><input type="hidden" name="loja_id" value="${e(lojaId)}">`;

const cupom = '<input name="cupom" placeholder="Cupom (opcional)" size="14">';

export function cabecalho(cliente) {
  return `<h1>Livraria · Cliente-Servidor</h1>
<p><small>Cliente (HTML/JS) e servidor (API REST) separados. Pagamento, localização e mensagens são apenas simulações.</small></p>
<nav><a href="#/">Catálogo</a><a href="#/lojas">Lojas</a><a href="#/cliente">${cliente ? "Minha área" : "Cadastro / entrada"}</a>
${cliente ? `<span>Olá, ${e(cliente.nome)}</span><form data-acao="sair"><button>Sair</button></form>` : ""}</nav>`;
}

export function mensagens(lista) {
  return lista.map((m) => `<p class="${m.erro ? "erro" : ""}" role="status">${e(m.texto)}</p>`).join("");
}

export function catalogo(livros, filtros) {
  const campo = (nome, rotulo) => `<label>${rotulo} <input name="${nome}" value="${e(filtros[nome])}"></label>`;
  return `<section><h2>Catálogo</h2>
<form data-acao="buscar">${campo("titulo", "Título")}${campo("autor", "Autor")}${campo("genero", "Gênero")}<button>Pesquisar</button></form>
${livros.map((b) => `<div class="card"><h3><a href="#/livro/${b.id}">${e(b.titulo)}</a></h3><p>${e(b.autor)} · ${e(b.genero)}</p></div>`).join("")
  || "<p>Nenhum livro encontrado.</p>"}</section>`;
}

function estoqueDaLoja(ed, s) {
  const acoes = s.quantidade > 0
    ? `<form data-acao="reservar">${pedido(ed.id, s.loja_id)}${cupom}<button>Reservar para retirada</button></form>
<form data-acao="comprar">${pedido(ed.id, s.loja_id)}${cupom}<button>Compra presencial simulada</button></form>`
    : `<form data-acao="alertar">${pedido(ed.id, s.loja_id)}<button>Avisar reposição (local)</button></form>`;
  return `<div class="card"><strong>${e(s.loja_nome)}</strong> · Seção ${e(s.secao)} · ${s.quantidade} disponível(is)
${acoes}<form data-acao="repor">${pedido(ed.id, s.loja_id)}<button>Simular +1 no estoque</button></form></div>`;
}

export function livro(l, cliente) {
  const minha = cliente && l.avaliacoes.find((a) => a.cliente_id === cliente.id);
  const notas = [5, 4, 3, 2, 1].map((n) => `<option value="${n}" ${minha && minha.nota === n ? "selected" : ""}>${n}</option>`).join("");
  const formAvaliacao = cliente
    ? `<form data-acao="avaliar"><input type="hidden" name="livro_id" value="${l.id}"><fieldset>
<legend>${minha ? "Atualizar minha avaliação" : "Avaliar este livro"}</legend>
<label>Nota <select name="nota">${notas}</select></label>
<label>Comentário <input name="texto" maxlength="500" value="${e(minha ? minha.texto : "")}"></label>
<button>Enviar avaliação</button></fieldset></form>`
    : "<p><small>Entre na sua área para avaliar.</small></p>";
  const edicoes = l.edicoes.map((ed) => `<fieldset><legend>${e(ed.nome)} (${ed.ano})</legend>
<p>Preço: ${reais(ed.preco_centavos)} · Valor atual: ${reais(ed.preco_final_centavos)}</p>
${ed.promocoes.map((p) => `<p>Promoção de demonstração: ${e(p.descricao)} (−${reais(p.desconto_centavos)})</p>`).join("")}
${ed.estoques.map((s) => estoqueDaLoja(ed, s)).join("")}</fieldset>`).join("");
  return `<article><h2>${e(l.titulo)}</h2><p>${e(l.autor)} · ${e(l.genero)}</p><p>${e(l.sinopse)}</p>
${cliente ? `<form data-acao="favoritar"><input type="hidden" name="livro_id" value="${l.id}"><button>Salvar favorito</button></form>` : ""}
<h3>Avaliações</h3><p>Média: <strong>${notaMedia(l.media)}</strong> (${l.total_avaliacoes} avaliação(ões))</p>
${l.avaliacoes.map((a) => `<p>${a.nota}/5 — ${e(a.texto || "sem comentário")} (${e(a.autor)}${a.cliente_id ? "" : ", demonstração"})</p>`).join("")
  || "<p>Ainda sem avaliações.</p>"}
${formAvaliacao}
<h3>Compare as edições e a disponibilidade</h3>
<p><small>Cupons de demonstração: LEITURA10 (10%) e BEMVINDO5 (R$ 5,00), uma vez por cliente.</small></p>
${edicoes}</article>`;
}

export function lojas(lista, bairro) {
  return `<section><h2>Encontrar lojas por bairro (sem GPS)</h2>
<form data-acao="filtrarLojas"><label>Bairro <input name="bairro" value="${e(bairro)}"></label><button>Filtrar</button></form>
${lista.map((l) => `<div class="card"><h3>${e(l.nome)} · ${e(l.bairro)}</h3><p>${e(l.endereco)} · ${e(l.horario)}</p>
<p>Pagamentos simulados: ${e(l.pagamentos)} · Serviços: ${e(l.servicos)} · Café: ${l.cafe ? "Sim" : "Não"}</p>
<p>Eventos de demonstração: ${e(l.eventos)}</p></div>`).join("") || "<p>Nenhuma unidade encontrada.</p>"}</section>`;
}

export function entrada() {
  return `<section><h2>Cadastro simples de demonstração</h2><p>Sem senha ou autenticação de produção.</p>
<form data-acao="cadastrar"><label>Nome <input name="nome" required></label><label>Email <input name="email" type="email" required></label>
<label>Bairro <input name="bairro" required></label><label>Interesses (gêneros separados por vírgula) <input name="interesses"></label>
<button>Cadastrar</button></form>
<h3>Já cadastrou?</h3><form data-acao="entrar"><label>Email <input name="email" type="email" required></label><button>Entrar</button></form></section>`;
}

export function area(d) {
  const c = d.cliente;
  const h = d.historico;
  const comCupom = (p) => (p.cupom ? ` (cupom ${e(p.cupom)})` : "");
  const reservas = h.reservas.map((r) => `<div class="card">${e(r.codigo)} · ${e(r.titulo)} / ${e(r.edicao)} · ${e(r.loja)} · Seção ${e(r.secao)} · ${reais(r.preco_centavos)}${comCupom(r)} · ${e(r.estado)}
${r.estado === "confirmada" ? `<form data-acao="retirar"><input type="hidden" name="codigo" value="${e(r.codigo)}"><button>Agilizar compra: retirar com código</button></form>
<form data-acao="cancelar"><input type="hidden" name="codigo" value="${e(r.codigo)}"><button>Cancelar reserva</button></form>` : ""}</div>`).join("");
  const lista = (itens, vazio, item) => itens.map(item).join("") || `<p>${vazio}</p>`;
  return `<section><h2>Minha área · ${e(c.nome)}</h2>
<p>${e(c.email)} · ${e(c.bairro)} · Interesses: ${e(c.interesses.join(", ") || "nenhum")}</p>
<p>Fidelidade: <strong>${h.pontos} pontos</strong> (somente compras concluídas)</p>
<h3>Reservas e códigos para retirada</h3>${reservas || "<p>Sem reservas.</p>"}
<h3>Histórico de compras (pagamento simulado)</h3>${lista(h.compras, "Sem compras.", (p) =>
    `<p>#${p.id} · ${e(p.titulo)} / ${e(p.edicao)} · ${e(p.loja)} · ${reais(p.preco_centavos)}${comCupom(p)}</p>`)}
<h3>Favoritos</h3>${lista(d.favoritos, "Nenhum favorito.", (b) =>
    `<p><a href="#/livro/${b.id}">${e(b.titulo)}</a> <form data-acao="desfavoritar"><input type="hidden" name="livro_id" value="${b.id}"><button>Remover favorito</button></form></p>`)}
<h3>Minhas avaliações</h3>${lista(d.avaliacoes, "Você ainda não avaliou livros.", (a) =>
    `<p><a href="#/livro/${a.livro_id}">${e(a.titulo)}</a> · ${a.nota}/5 — ${e(a.texto || "sem comentário")}</p>`)}
<h3>Recomendações locais por interesse</h3>${lista(d.recomendacoes, "Sem recomendações no catálogo de demonstração.", (b) =>
    `<p><a href="#/livro/${b.id}">${e(b.titulo)}</a></p>`)}
<h3>Notificações locais</h3>${lista(d.notificacoes, "Nenhuma notificação.", (n) => `<p>${e(n.tipo)}: ${e(n.mensagem)}</p>`)}</section>`;
}
