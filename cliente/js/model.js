// Model: guarda o estado do cliente e é o único arquivo que conversa com o servidor (HTTP/REST em JSON).

export const estado = { cliente: null, mensagens: [] };

export class ErroApi extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.status = status;
  }
}

async function api(metodo, caminho, corpo) {
  const resposta = await fetch(`/api${caminho}`, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
    credentials: "same-origin",
  });
  const dados = resposta.status === 204 ? {} : await resposta.json();
  if (!resposta.ok) {
    if (resposta.status === 401) estado.cliente = null;
    throw new ErroApi(dados.erro || `Erro ${resposta.status}`, resposta.status);
  }
  return dados;
}

const consulta = (filtros) => new URLSearchParams(Object.entries(filtros).filter(([, valor]) => valor)).toString();

export const Livraria = {
  async carregarSessao() {
    estado.cliente = (await api("GET", "/sessao")).cliente;
  },
  buscarLivros: (filtros) => api("GET", `/livros?${consulta(filtros)}`),
  livro: (livroId) => api("GET", `/livros/${livroId}`),
  lojas: (bairro) => api("GET", `/lojas?${consulta({ bairro })}`),
  minhaArea: () => api("GET", "/minha-area"),

  async cadastrar(dados) {
    const resposta = await api("POST", "/clientes", dados);
    estado.cliente = resposta.cliente;
    return resposta;
  },
  async entrar(email) {
    estado.cliente = (await api("POST", "/sessao", { email })).cliente;
  },
  async sair() {
    await api("DELETE", "/sessao");
    estado.cliente = null;
  },

  favoritar: (livroId, adicionar) => api(adicionar ? "PUT" : "DELETE", `/favoritos/${livroId}`),
  reservar: (dados) => api("POST", "/reservas", dados),
  comprar: (dados) => api("POST", "/compras", dados),
  retirar: (codigo) => api("POST", `/reservas/${encodeURIComponent(codigo)}/retirada`),
  cancelar: (codigo) => api("POST", `/reservas/${encodeURIComponent(codigo)}/cancelamento`),
  alertar: (dados) => api("POST", "/alertas", dados),
  repor: (dados) => api("POST", "/estoque/reposicao", dados),
  avaliar: (livroId, dados) => api("PUT", `/livros/${livroId}/avaliacao`, dados),
};
