"""BFF (Backend for Frontend): recebe os dados da tela, chama os módulos e devolve dados/mensagens.

Não tem regra de negócio; só converte formulários e junta respostas de vários módulos numa página.
"""
from dataclasses import asdict

from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.texto import reais


def inteiro(form, campo):
    try:
        return int(form[campo])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegraInvalida("Dados do formulário inválidos.") from exc


def com_cupom(pedido):
    return f" com cupom {pedido.cupom}" if pedido.cupom else ""


class LivrariaBFF:
    def __init__(self, modulos):
        self.m = modulos

    # páginas
    def cliente_atual(self, cliente_id):
        try:
            return self.m.usuarios.obter(cliente_id) if cliente_id else None
        except RegraInvalida:  # sessão antiga de um cliente que não existe mais
            return None

    def pagina_catalogo(self, args):
        return {"pagina": "catalogo", "livros": self.m.busca.buscar_livros(
            args.get("titulo", ""), args.get("autor", ""), args.get("genero", ""))}

    def pagina_livro(self, livro_id, cliente_id=None):
        livro = dict(asdict(self.m.catalogo.obter_livro(livro_id)), **self.m.catalogo.avaliacoes(livro_id))
        livro["edicoes"] = [dict(ed, estoques=self.m.estoque.disponibilidade(ed["id"]))
                            for ed in self.m.catalogo.edicoes(livro_id)]
        minha = next((a for a in livro["avaliacoes"] if cliente_id and a.cliente_id == cliente_id), None)
        return {"pagina": "livro", "livro": livro, "minha_avaliacao": minha}

    def pagina_lojas(self, args):
        return {"pagina": "lojas", "lojas": self.m.estoque.listar_lojas(args.get("bairro", ""))}

    def pagina_cliente(self, cliente_id):
        if not cliente_id:
            return {"pagina": "entrada"}
        return {"pagina": "cliente", "historico": self.m.pedidos.historico(cliente_id),
                "favoritos": self.m.usuarios.favoritos(cliente_id),
                "recomendacoes": self.m.usuarios.recomendacoes(cliente_id),
                "notificacoes": self.m.notificacoes.listar(cliente_id),
                "avaliacoes": self.m.catalogo.avaliacoes_do_cliente(cliente_id)}

    # ações (devolvem a mensagem para o usuário)
    def cadastrar(self, form):
        return self.m.usuarios.cadastrar(form.get("nome", ""), form.get("email", ""), form.get("bairro", ""),
                                         form.get("interesses", ""))

    def entrar(self, form):
        return self.m.usuarios.entrar(form.get("email", "")).id

    def favoritar(self, cliente_id, livro_id, adicionar):
        self.m.usuarios.favoritar(cliente_id, livro_id, adicionar)

    def reservar(self, cliente_id, form):
        r = self.m.pedidos.reservar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"), form.get("cupom", ""))
        return (f"Reserva confirmada: {r.codigo} por {reais(r.preco_centavos)}{com_cupom(r)}. "
                "Retire na unidade selecionada; pagamento simulado apenas na retirada.")

    def comprar(self, cliente_id, form):
        c = self.m.pedidos.comprar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"), form.get("cupom", ""))
        return f"Compra presencial simulada registrada: #{c.id} por {reais(c.preco_centavos)}{com_cupom(c)} (sem cobrança real)."

    def retirar(self, cliente_id, codigo):
        self.m.pedidos.retirar(cliente_id, codigo)
        return f"Retirada de {codigo} concluída; compra simulada registrada."

    def cancelar(self, cliente_id, codigo):
        self.m.pedidos.cancelar(cliente_id, codigo)
        return f"Reserva {codigo} cancelada; estoque devolvido."

    def alertar(self, cliente_id, form):
        self.m.estoque.alertar(cliente_id, inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Alerta local registrado; consulte sua área após simular reposição."

    def repor(self, form):
        self.m.estoque.repor(inteiro(form, "edicao_id"), inteiro(form, "loja_id"))
        return "Reposição simulada: uma unidade adicionada e notificações locais geradas."

    def avaliar(self, cliente_id, livro_id, form):
        cliente = self.m.usuarios.obter(cliente_id)  # o Catálogo não conhece clientes: o BFF valida e passa o nome
        self.m.catalogo.avaliar(cliente.id, cliente.nome, livro_id, inteiro(form, "nota"), form.get("texto", ""))
        return "Avaliação registrada. Obrigado!"

    # API REST (JSON)
    def api_livros(self, args):
        return [asdict(livro) for livro in self.pagina_catalogo(args)["livros"]]

    def api_livro(self, livro_id):
        livro = self.pagina_livro(livro_id)["livro"]
        livro["avaliacoes"] = [asdict(a) for a in livro["avaliacoes"]]
        for edicao in livro["edicoes"]:
            edicao["promocoes"] = [asdict(p) for p in edicao["promocoes"]]
        return livro
