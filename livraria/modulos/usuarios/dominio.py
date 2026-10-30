"""Entidades internas de usuários. Outros módulos não importam este arquivo."""
import re
from dataclasses import dataclass, field

from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.texto import normalizar


@dataclass
class Cliente:
    id: int
    nome: str
    email: str
    bairro: str
    interesses: list = field(default_factory=list)

    @classmethod
    def novo(cls, nome, email, bairro, interesses=""):
        nome, email, bairro = nome.strip(), email.strip().lower(), bairro.strip()
        if not nome or not bairro or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise RegraInvalida("Informe nome, email válido e bairro.")
        return cls(0, nome, email, bairro, [p.strip() for p in interesses.split(",") if p.strip()])

    def interessado_em(self, genero):
        return normalizar(genero) in [normalizar(i) for i in self.interesses]


@dataclass
class Favorito:
    cliente_id: int
    livro_id: int
