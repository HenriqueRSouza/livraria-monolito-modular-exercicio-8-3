"""Interface de repositório (DIP): cada módulo depende desta abstração, não do arquivo TXT.

Qualquer classe que implemente estes métodos pode guardar os dados de um módulo (TXT, SQLite, PostgreSQL...).
"""
from abc import ABC, abstractmethod


class RepositorioModulo(ABC):
    @abstractmethod
    def listar(self, tipo):
        """Devolve todos os registros de uma entidade (ex.: listar(Livro))."""

    @abstractmethod
    def salvar(self, registro):
        """Insere (id 0 recebe um id novo) ou atualiza o registro e o devolve."""

    @abstractmethod
    def remover(self, registro):
        """Apaga o registro, se existir."""

    @abstractmethod
    def transacao(self):
        """Context manager: tudo o que for salvo dentro dele é gravado junto, ou nada é gravado."""
