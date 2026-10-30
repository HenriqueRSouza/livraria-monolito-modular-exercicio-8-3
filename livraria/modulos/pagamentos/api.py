"""API pública de Pagamentos (R05 pagamento simulado, R08 cupons)."""
from livraria.compartilhado import RegraInvalida, filtrar, obter
from livraria.modulos.pagamentos.dominio import Cupom, Pagamento, UsoCupom


class PagamentosAPI:
    def __init__(self, repo):
        self.repo = repo

    def aplicar_cupom(self, cliente_id, preco_centavos, codigo):
        """Só calcula, sem gravar. Devolve (preço final, código normalizado ou None)."""
        codigo = (codigo or "").strip().upper()
        if not codigo:
            return preco_centavos, None
        cupom = obter(self.repo, Cupom, f"Cupom {codigo} inexistente.", codigo=codigo)
        if filtrar(self.repo, UsoCupom, cliente_id=cliente_id, codigo=codigo):
            raise RegraInvalida(f"Cupom {codigo} já utilizado por este cliente.")
        return cupom.aplicar(preco_centavos), codigo

    def registrar_uso(self, cliente_id, codigo, referencia):
        with self.repo.transacao():
            if filtrar(self.repo, UsoCupom, cliente_id=cliente_id, codigo=codigo):
                raise RegraInvalida(f"Cupom {codigo} já utilizado por este cliente.")
            self.repo.salvar(UsoCupom(0, cliente_id, codigo, referencia))

    def liberar_uso(self, referencia):
        """Reserva cancelada: o cupom volta a valer para o cliente."""
        with self.repo.transacao():
            for uso in filtrar(self.repo, UsoCupom, referencia=referencia):
                self.repo.remover(uso)

    def registrar_pagamento(self, referencia, valor_centavos):
        return self.repo.salvar(Pagamento(0, referencia, valor_centavos, "aprovado (simulado)"))

    def pagamentos(self):
        return self.repo.listar(Pagamento)
