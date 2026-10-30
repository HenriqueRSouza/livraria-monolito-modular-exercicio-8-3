"""API pública do Estoque (R03, R05, R06) e o evento que este módulo publica."""
from dataclasses import asdict, dataclass

from livraria.compartilhado import RegraInvalida, filtrar, obter
from livraria.compartilhado.texto import normalizar
from livraria.modulos.estoque.dominio import Alerta, Estoque, Loja


@dataclass(frozen=True)
class EstoqueReposto:
    edicao_id: int
    loja_id: int
    clientes: tuple  # clientes que pediram alerta


class EstoqueAPI:
    def __init__(self, repo, usuarios, barramento):
        self.repo = repo
        self.usuarios = usuarios
        self.barramento = barramento

    def listar_lojas(self, bairro=""):
        return [loja for loja in self.repo.listar(Loja) if normalizar(bairro) in normalizar(loja.bairro)]

    def obter_loja(self, loja_id):
        return obter(self.repo, Loja, "Loja inválida.", id=loja_id)

    def obter(self, edicao_id, loja_id):
        return obter(self.repo, Estoque, "Sem estoque nesta unidade/edição.", edicao_id=edicao_id, loja_id=loja_id)

    def disponibilidade(self, edicao_id):
        """Quantidade e seção da edição em cada loja."""
        lojas = {loja.id: loja.nome for loja in self.repo.listar(Loja)}
        return [dict(asdict(e), loja_nome=lojas[e.loja_id]) for e in filtrar(self.repo, Estoque, edicao_id=edicao_id)]

    def debitar(self, edicao_id, loja_id):
        with self.repo.transacao():
            estoque = self.obter(edicao_id, loja_id)
            estoque.debitar()
            self.repo.salvar(estoque)

    def devolver(self, edicao_id, loja_id):
        with self.repo.transacao():
            estoque = self.obter(edicao_id, loja_id)
            estoque.quantidade += 1
            self.repo.salvar(estoque)

    def alertar(self, cliente_id, edicao_id, loja_id):
        self.usuarios.obter(cliente_id)
        with self.repo.transacao():
            estoque = filtrar(self.repo, Estoque, edicao_id=edicao_id, loja_id=loja_id)
            if not estoque or estoque[0].quantidade != 0:
                raise RegraInvalida("Alerta permitido apenas para edição esgotada na unidade.")
            self.repo.salvar(Alerta(cliente_id, edicao_id, loja_id))

    def repor(self, edicao_id, loja_id):
        """Reposição simulada: +1 unidade; os alertas atendidos saem e viram o evento EstoqueReposto."""
        with self.repo.transacao():
            estoque = obter(self.repo, Estoque, "Edição ou loja inválida.", edicao_id=edicao_id, loja_id=loja_id)
            estoque.quantidade += 1
            self.repo.salvar(estoque)
            alertas = filtrar(self.repo, Alerta, edicao_id=edicao_id, loja_id=loja_id)
            for alerta in alertas:
                self.repo.remover(alerta)
        self.barramento.publicar(EstoqueReposto(edicao_id, loja_id, tuple(a.cliente_id for a in alertas)))
