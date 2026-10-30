"""Entidades internas de pagamentos. Outros módulos não importam este arquivo."""
from dataclasses import dataclass

from livraria.compartilhado import RegraInvalida


@dataclass
class Cupom:
    codigo: str
    descricao: str
    tipo: str  # "percentual" ou "fixo"
    valor: int
    ativo: bool

    def aplicar(self, preco_centavos):
        if not self.ativo:
            raise RegraInvalida(f"Cupom {self.codigo} inativo.")
        desconto = preco_centavos * self.valor // 100 if self.tipo == "percentual" else self.valor
        return max(0, preco_centavos - desconto)


@dataclass
class UsoCupom:
    """Um cupom usado por um cliente em um pedido (referência = código da reserva ou da compra)."""
    id: int
    cliente_id: int
    codigo: str
    referencia: str


@dataclass
class Pagamento:
    """Pagamento simulado: nenhuma cobrança real é feita."""
    id: int
    referencia: str
    valor_centavos: int
    situacao: str
