"""Entidade interna de notificações. Outros módulos não importam este arquivo."""
from dataclasses import dataclass


@dataclass
class Notificacao:
    id: int
    cliente_id: int
    tipo: str
    mensagem: str
