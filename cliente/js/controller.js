// Controller: recebe os eventos da tela (links e formulários), chama o Model e manda a View redesenhar.

import { estado, Livraria } from "./model.js";
import * as View from "./view.js";

const topo = document.querySelector("#topo");
const app = document.querySelector("#app");

const avisar = (texto, erro = false) => estado.mensagens.push({ texto, erro });
const irPara = (destino) => history.pushState(null, "", destino);
const filtrosPreenchidos = (dados) => new URLSearchParams(Object.entries(dados).filter(([, valor]) => valor)).toString();

function lerRota() {
  const [caminho, query = ""] = location.hash.slice(1).split("?");
  return { partes: (caminho || "/").split("/").filter(Boolean), params: Object.fromEntries(new URLSearchParams(query)) };
}

async function telaAtual() {
  const { partes, params } = lerRota();
  if (partes[0] === "livro") return View.livro(await Livraria.livro(partes[1]), estado.cliente);
  if (partes[0] === "lojas") return View.lojas(await Livraria.lojas(params.bairro || ""), params.bairro || "");
  if (partes[0] === "cliente") return estado.cliente ? View.area(await Livraria.minhaArea()) : View.entrada();
  return View.catalogo(await Livraria.buscarLivros(params), params);
}

async function desenhar() {
  let html;
  try {
    html = await telaAtual();
  } catch (erro) {
    avisar(erro.message, true);
    html = erro.status === 401 ? View.entrada() : "";
  }
  topo.innerHTML = View.cabecalho(estado.cliente);
  app.innerHTML = View.mensagens(estado.mensagens.splice(0)) + html;
}

// Cada data-acao dos formulários da View aponta para uma destas ações.
const acoes = {
  buscar: async (d) => irPara(`#/?${filtrosPreenchidos(d)}`),
  filtrarLojas: async (d) => irPara(`#/lojas?${filtrosPreenchidos(d)}`),
  async cadastrar(d) {
    avisar((await Livraria.cadastrar(d)).mensagem);
    irPara("#/cliente");
  },
  async entrar(d) {
    await Livraria.entrar(d.email);
    irPara("#/cliente");
  },
  async sair() {
    await Livraria.sair();
    irPara("#/");
  },
  favoritar: async (d) => avisar((await Livraria.favoritar(d.livro_id, true)).mensagem),
  desfavoritar: async (d) => avisar((await Livraria.favoritar(d.livro_id, false)).mensagem),
  async reservar(d) {
    avisar((await Livraria.reservar(d)).mensagem);
    irPara("#/cliente");
  },
  async comprar(d) {
    avisar((await Livraria.comprar(d)).mensagem);
    irPara("#/cliente");
  },
  retirar: async (d) => avisar((await Livraria.retirar(d.codigo)).mensagem),
  cancelar: async (d) => avisar((await Livraria.cancelar(d.codigo)).mensagem),
  alertar: async (d) => avisar((await Livraria.alertar(d)).mensagem),
  repor: async (d) => avisar((await Livraria.repor(d)).mensagem),
  avaliar: async (d) => avisar((await Livraria.avaliar(d.livro_id, d)).mensagem),
};

document.addEventListener("submit", async (evento) => {
  const form = evento.target.closest("form[data-acao]");
  if (!form) return;
  evento.preventDefault();
  try {
    await acoes[form.dataset.acao](Object.fromEntries(new FormData(form)));
  } catch (erro) {
    avisar(erro.message, true);
  }
  await desenhar();
});

window.addEventListener("hashchange", desenhar);
window.addEventListener("popstate", desenhar);

Livraria.carregarSessao().catch(() => {}).finally(desenhar);
