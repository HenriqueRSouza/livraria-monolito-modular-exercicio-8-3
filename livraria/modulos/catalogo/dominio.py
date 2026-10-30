"""Entidades internas do catálogo. Outros módulos não importam este arquivo."""
from dataclasses import dataclass
from typing import Optional

from livraria.compartilhado import RegraInvalida


@dataclass
class Livro:
    id: int
    titulo: str
    autor: str
    genero: str
    sinopse: str


@dataclass
class Edicao:
    id: int
    livro_id: int
    nome: str
    ano: int
    preco_centavos: int


@dataclass
class Promocao:
    id: int
    edicao_id: int
    descricao: str
    desconto_centavos: int
    ativa: bool


@dataclass
class Avaliacao:
    id: int
    livro_id: int
    nota: int
    texto: str
    autor: str
    cliente_id: Optional[int] = None

    @staticmethod
    def validar(nota, texto):
        if not 1 <= nota <= 5:
            raise RegraInvalida("A nota deve ser um inteiro de 1 a 5.")
        texto = (texto or "").strip()
        if len(texto) > 500:
            raise RegraInvalida("O texto da avaliação deve ter até 500 caracteres.")
        return nota, texto


def preco_promocional(edicao, promocoes):
    return max(0, edicao.preco_centavos - sum(p.desconto_centavos for p in promocoes if p.ativa))


def media(avaliacoes):
    return round(sum(a.nota for a in avaliacoes) / len(avaliacoes), 1) if avaliacoes else None
