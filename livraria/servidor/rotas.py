"""Routes (rotas/endpoints): a API REST que o cliente consome.

Só traduz HTTP/JSON para chamadas da camada de Negócios (livraria/modulos) e de volta. Regras ficam nos módulos.
Erros de regra viram {"erro": "..."} com 400 (ou 404 em consultas); falta de login vira 401.
"""
from dataclasses import asdict, is_dataclass

from flask import Blueprint, jsonify, request, session

from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.texto import reais


class NaoAutenticado(Exception):
    """Ação pessoal sem cliente na sessão."""


def json_de(valor):
    if is_dataclass(valor):
        return asdict(valor)
    if isinstance(valor, dict):
        return {k: json_de(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [json_de(v) for v in valor]
    return valor


def corpo():
    return request.get_json(silent=True) or {}


def inteiro(dados, campo):
    try:
        return int(dados[campo])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegraInvalida("Dados do formulário inválidos.") from exc


def com_cupom(pedido):
    return f" com cupom {pedido.cupom}" if pedido.cupom else ""


def criar_rotas(m):
    api = Blueprint("api", __name__, url_prefix="/api")

    @api.errorhandler(RegraInvalida)
    def regra_invalida(exc):
        return jsonify(erro=str(exc)), 404 if request.method == "GET" else 400

    @api.errorhandler(NaoAutenticado)
    def nao_autenticado(_exc):
        return jsonify(erro="Cadastre-se ou entre para continuar."), 401

    def cliente_logado():
        cliente_id = session.get("cliente_id")
        if not cliente_id:
            raise NaoAutenticado()
        try:
            return m.usuarios.obter(cliente_id)
        except RegraInvalida:  # sessão antiga de um cliente que não existe mais
            session.clear()
            raise NaoAutenticado() from None

    def pedido(dados):
        return inteiro(dados, "edicao_id"), inteiro(dados, "loja_id")

    # catálogo e lojas (público)
    @api.get("/livros")
    def livros():
        a = request.args
        return jsonify(json_de(m.busca.buscar_livros(a.get("titulo", ""), a.get("autor", ""), a.get("genero", ""))))

    @api.get("/livros/<int:livro_id>")
    def livro(livro_id):
        dados = dict(asdict(m.catalogo.obter_livro(livro_id)), **m.catalogo.avaliacoes(livro_id))
        dados["edicoes"] = [dict(ed, estoques=m.estoque.disponibilidade(ed["id"])) for ed in m.catalogo.edicoes(livro_id)]
        return jsonify(json_de(dados))

    @api.get("/lojas")
    def lojas():
        return jsonify(json_de(m.estoque.listar_lojas(request.args.get("bairro", ""))))

    # sessão e cadastro
    @api.get("/sessao")
    def sessao():
        try:
            return jsonify(cliente=json_de(cliente_logado()))
        except NaoAutenticado:
            return jsonify(cliente=None)

    @api.post("/sessao")
    def entrar():
        cliente = m.usuarios.entrar(corpo().get("email", ""))
        session["cliente_id"] = cliente.id
        return jsonify(cliente=json_de(cliente))

    @api.delete("/sessao")
    def sair():
        session.clear()
        return "", 204

    @api.post("/clientes")
    def cadastrar():
        d = corpo()
        cliente_id = m.usuarios.cadastrar(d.get("nome", ""), d.get("email", ""), d.get("bairro", ""), d.get("interesses", ""))
        session["cliente_id"] = cliente_id
        return jsonify(cliente=json_de(m.usuarios.obter(cliente_id)),
                       mensagem="Cadastro concluído. Esta é uma sessão local de demonstração."), 201

    @api.get("/minha-area")
    def minha_area():
        cliente = cliente_logado()
        return jsonify(json_de({
            "cliente": cliente, "historico": m.pedidos.historico(cliente.id),
            "favoritos": m.usuarios.favoritos(cliente.id), "recomendacoes": m.usuarios.recomendacoes(cliente.id),
            "notificacoes": m.notificacoes.listar(cliente.id), "avaliacoes": m.catalogo.avaliacoes_do_cliente(cliente.id)}))

    # ações do cliente
    @api.put("/favoritos/<int:livro_id>")
    def favoritar(livro_id):
        m.usuarios.favoritar(cliente_logado().id, livro_id, True)
        return jsonify(mensagem="Livro salvo nos favoritos.")

    @api.delete("/favoritos/<int:livro_id>")
    def desfavoritar(livro_id):
        m.usuarios.favoritar(cliente_logado().id, livro_id, False)
        return jsonify(mensagem="Livro removido dos favoritos.")

    @api.post("/reservas")
    def reservar():
        d = corpo()
        r = m.pedidos.reservar(cliente_logado().id, *pedido(d), d.get("cupom", ""))
        return jsonify(reserva=json_de(r), mensagem=(
            f"Reserva confirmada: {r.codigo} por {reais(r.preco_centavos)}{com_cupom(r)}. "
            "Retire na unidade selecionada; pagamento simulado apenas na retirada.")), 201

    @api.post("/reservas/<codigo>/retirada")
    def retirar(codigo):
        compra = m.pedidos.retirar(cliente_logado().id, codigo)
        return jsonify(compra=json_de(compra), mensagem=f"Retirada de {codigo} concluída; compra simulada registrada.")

    @api.post("/reservas/<codigo>/cancelamento")
    def cancelar(codigo):
        m.pedidos.cancelar(cliente_logado().id, codigo)
        return jsonify(mensagem=f"Reserva {codigo} cancelada; estoque devolvido.")

    @api.post("/compras")
    def comprar():
        d = corpo()
        c = m.pedidos.comprar(cliente_logado().id, *pedido(d), d.get("cupom", ""))
        return jsonify(compra=json_de(c), mensagem=(
            f"Compra presencial simulada registrada: #{c.id} por {reais(c.preco_centavos)}{com_cupom(c)} (sem cobrança real).")), 201

    @api.post("/alertas")
    def alertar():
        m.estoque.alertar(cliente_logado().id, *pedido(corpo()))
        return jsonify(mensagem="Alerta local registrado; consulte sua área após simular reposição."), 201

    @api.post("/estoque/reposicao")
    def repor():
        m.estoque.repor(*pedido(corpo()))
        return jsonify(mensagem="Reposição simulada: uma unidade adicionada e notificações locais geradas.")

    @api.put("/livros/<int:livro_id>/avaliacao")
    def avaliar(livro_id):
        cliente = cliente_logado()  # o Catálogo não conhece clientes: a rota valida e passa o nome
        d = corpo()
        avaliacao = m.catalogo.avaliar(cliente.id, cliente.nome, livro_id, inteiro(d, "nota"), d.get("texto", ""))
        return jsonify(avaliacao=json_de(avaliacao), mensagem="Avaliação registrada. Obrigado!")

    return api
