"""Entidades internas do estoque. Outros módulos não importam este arquivo."""
from dataclasses import dataclass

from livraria.compartilhado import RegraInvalida


@dataclass
class Loja:
    id: int
    nome: str
    bairro: str
    endereco: str
    horario: str
    pagamentos: str
    servicos: str
    cafe: bool
    eventos: str


@dataclass
class Estoque:
    edicao_id: int
    loja_id: int
    quantidade: int
    secao: str

    def debitar(self):
        if self.quantidade <= 0:
            raise RegraInvalida("Sem estoque nesta unidade/edição.")
        self.quantidade -= 1


@dataclass
class Alerta:
    cliente_id: int
    edicao_id: int
    loja_id: int
