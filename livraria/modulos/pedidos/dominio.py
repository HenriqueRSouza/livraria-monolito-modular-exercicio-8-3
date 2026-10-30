"""Entidades internas de pedidos. Outros módulos não importam este arquivo."""
from dataclasses import dataclass
from typing import Optional

from livraria.compartilhado import RegraInvalida


@dataclass
class Reserva:
    id: int
    cliente_id: int
    edicao_id: int
    loja_id: int
    codigo: str
    estado: str  # confirmada, retirada ou cancelada
    preco_centavos: int
    cupom: Optional[str] = None

    def _confirmada_de(self, cliente_id):
        if self.estado != "confirmada" or self.cliente_id != cliente_id:
            raise RegraInvalida("Reserva inexistente, de outro cliente ou já finalizada.")

    def cancelar(self, cliente_id):
        self._confirmada_de(cliente_id)
        self.estado = "cancelada"

    def retirar(self, cliente_id):
        """Vira compra sem novo débito de estoque."""
        self._confirmada_de(cliente_id)
        self.estado = "retirada"
        return Compra(0, self.cliente_id, self.edicao_id, self.loja_id, self.preco_centavos, self.id, self.cupom)


@dataclass
class Compra:
    id: int
    cliente_id: int
    edicao_id: int
    loja_id: int
    preco_centavos: int
    reserva_id: Optional[int] = None
    cupom: Optional[str] = None

    @property
    def referencia(self):
        return f"COMPRA-{self.id:06d}"


def pontos(compras):
    return sum(c.preco_centavos // 100 for c in compras)
