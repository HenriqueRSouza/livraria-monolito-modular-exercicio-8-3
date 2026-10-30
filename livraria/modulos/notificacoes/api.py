"""API pública de Notificações (R04, R06). Reage aos eventos ClienteCadastrado e EstoqueReposto.

Nenhum email, push ou SMS é enviado: as notificações ficam no arquivo e aparecem na área do cliente.
"""
from livraria.compartilhado import filtrar
from livraria.compartilhado.texto import normalizar
from livraria.modulos.notificacoes.dominio import Notificacao


class NotificacoesAPI:
    def __init__(self, repo, catalogo, estoque):
        self.repo = repo
        self.catalogo = catalogo
        self.estoque = estoque

    def listar(self, cliente_id):
        return sorted(filtrar(self.repo, Notificacao, cliente_id=cliente_id), key=lambda n: n.id, reverse=True)

    def avisar_promocoes(self, cliente_id, interesses):
        """Uma notificação por promoção ativa de gênero de interesse do cliente."""
        generos = {normalizar(i) for i in interesses}
        with self.repo.transacao():
            for promocao in self.catalogo.promocoes_ativas():
                if normalizar(promocao["genero"]) in generos:
                    self.repo.salvar(Notificacao(0, cliente_id, "promocao", promocao["descricao"]))

    def avisar_reposicao(self, edicao_id, loja_id, clientes):
        livro = self.catalogo.obter_livro(self.catalogo.obter_edicao(edicao_id).livro_id)
        loja = self.estoque.obter_loja(loja_id)
        with self.repo.transacao():
            for cliente_id in clientes:
                self.repo.salvar(Notificacao(0, cliente_id, "reposicao", f"Reposição simulada: {livro.titulo} em {loja.nome}"))
