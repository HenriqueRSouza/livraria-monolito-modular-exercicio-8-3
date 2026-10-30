"""API pública de Usuários (R02, R04) e o evento que este módulo publica."""
from dataclasses import dataclass

from livraria.compartilhado import RegraInvalida, filtrar, obter
from livraria.modulos.usuarios.dominio import Cliente, Favorito


@dataclass(frozen=True)
class ClienteCadastrado:
    cliente_id: int
    interesses: tuple


class UsuariosAPI:
    def __init__(self, repo, catalogo, barramento):
        self.repo = repo
        self.catalogo = catalogo
        self.barramento = barramento

    def obter(self, cliente_id):
        return obter(self.repo, Cliente, "Cliente inválido; cadastre-se primeiro.", id=cliente_id)

    def cadastrar(self, nome, email, bairro, interesses=""):
        cliente = Cliente.novo(nome, email, bairro, interesses)
        with self.repo.transacao():
            if filtrar(self.repo, Cliente, email=cliente.email):
                raise RegraInvalida("Email já cadastrado.")
            cliente = self.repo.salvar(cliente)
        self.barramento.publicar(ClienteCadastrado(cliente.id, tuple(cliente.interesses)))
        return cliente.id

    def entrar(self, email):
        return obter(self.repo, Cliente, "Email não cadastrado.", email=email.strip().lower())

    def favoritar(self, cliente_id, livro_id, adicionar=True):
        self.obter(cliente_id)
        self.catalogo.obter_livro(livro_id)
        with self.repo.transacao():
            if adicionar:
                self.repo.salvar(Favorito(cliente_id, livro_id))
            else:
                self.repo.remover(Favorito(cliente_id, livro_id))

    def favoritos(self, cliente_id):
        ids = {f.livro_id for f in filtrar(self.repo, Favorito, cliente_id=self.obter(cliente_id).id)}
        return [livro for livro in self.catalogo.listar_livros() if livro.id in ids]

    def recomendacoes(self, cliente_id):
        cliente = self.obter(cliente_id)
        favoritos = {f.livro_id for f in filtrar(self.repo, Favorito, cliente_id=cliente_id)}
        return [livro for livro in self.catalogo.listar_livros()
                if livro.id not in favoritos and cliente.interessado_em(livro.genero)]
