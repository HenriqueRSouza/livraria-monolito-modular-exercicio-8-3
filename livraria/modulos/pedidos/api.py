"""API pública de Pedidos (R05, R08) e os eventos que este módulo publica.

Reservar e comprar envolvem quatro módulos, cada um com o seu arquivo. Não existe transação única entre eles,
então a operação segue o padrão saga: valida tudo antes, debita o estoque e, se gravar o pedido falhar,
devolve a unidade (compensação).
"""
import threading
from dataclasses import asdict, dataclass

from livraria.compartilhado import filtrar, obter
from livraria.modulos.pedidos.dominio import Compra, Reserva, pontos


@dataclass(frozen=True)
class ReservaCancelada:
    cliente_id: int
    codigo: str


@dataclass(frozen=True)
class CompraRegistrada:
    referencia: str
    cliente_id: int
    valor_centavos: int


class PedidosAPI:
    def __init__(self, repo, usuarios, catalogo, estoque, pagamentos, barramento):
        self.repo = repo
        self.usuarios = usuarios
        self.catalogo = catalogo
        self.estoque = estoque
        self.pagamentos = pagamentos
        self.barramento = barramento
        self.trava = threading.RLock()  # cupom e estoque são conferidos e gravados sem outro pedido no meio

    def reservar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.trava:
            self.usuarios.obter(cliente_id)
            preco, cupom = self.pagamentos.aplicar_cupom(cliente_id, self.catalogo.preco_atual(edicao_id), cupom)
            self.estoque.debitar(edicao_id, loja_id)
            try:
                with self.repo.transacao():
                    reserva = self.repo.salvar(Reserva(0, cliente_id, edicao_id, loja_id, "", "confirmada", preco, cupom))
                    reserva.codigo = f"RES-{reserva.id:06d}"
                    self.repo.salvar(reserva)
                    if cupom:
                        self.pagamentos.registrar_uso(cliente_id, cupom, reserva.codigo)
            except Exception:
                self.estoque.devolver(edicao_id, loja_id)  # compensação
                raise
            return reserva

    def _reserva(self, cliente_id, codigo):
        self.usuarios.obter(cliente_id)
        return obter(self.repo, Reserva, "Reserva inexistente, de outro cliente ou já finalizada.", codigo=codigo)

    def cancelar(self, cliente_id, codigo):
        with self.trava:
            with self.repo.transacao():
                reserva = self._reserva(cliente_id, codigo)
                reserva.cancelar(cliente_id)
                self.repo.salvar(reserva)
            self.estoque.devolver(reserva.edicao_id, reserva.loja_id)
            self.barramento.publicar(ReservaCancelada(cliente_id, codigo))

    def retirar(self, cliente_id, codigo):
        with self.trava:
            with self.repo.transacao():
                reserva = self._reserva(cliente_id, codigo)
                compra = reserva.retirar(cliente_id)
                self.repo.salvar(reserva)
                compra = self.repo.salvar(compra)
            self.barramento.publicar(CompraRegistrada(compra.referencia, cliente_id, compra.preco_centavos))
            return compra

    def comprar(self, cliente_id, edicao_id, loja_id, cupom=""):
        with self.trava:
            self.usuarios.obter(cliente_id)
            preco, cupom = self.pagamentos.aplicar_cupom(cliente_id, self.catalogo.preco_atual(edicao_id), cupom)
            self.estoque.debitar(edicao_id, loja_id)
            try:
                with self.repo.transacao():
                    compra = self.repo.salvar(Compra(0, cliente_id, edicao_id, loja_id, preco, None, cupom))
                    if cupom:
                        self.pagamentos.registrar_uso(cliente_id, cupom, compra.referencia)
            except Exception:
                self.estoque.devolver(edicao_id, loja_id)  # compensação
                raise
            self.barramento.publicar(CompraRegistrada(compra.referencia, cliente_id, compra.preco_centavos))
            return compra

    def historico(self, cliente_id):
        self.usuarios.obter(cliente_id)
        reservas = sorted(filtrar(self.repo, Reserva, cliente_id=cliente_id), key=lambda r: r.id, reverse=True)
        compras = sorted(filtrar(self.repo, Compra, cliente_id=cliente_id), key=lambda c: c.id, reverse=True)
        return {"reservas": [dict(self._descricao(r), secao=self.estoque.obter(r.edicao_id, r.loja_id).secao)
                             for r in reservas],
                "compras": [self._descricao(c) for c in compras],
                "pontos": pontos(compras)}

    def _descricao(self, pedido):
        edicao = self.catalogo.obter_edicao(pedido.edicao_id)
        livro = self.catalogo.obter_livro(edicao.livro_id)
        loja = self.estoque.obter_loja(pedido.loja_id)
        return dict(asdict(pedido), titulo=livro.titulo, edicao=edicao.nome, loja=loja.nome)
