"""API pública do Catálogo (R01, R02, R07). É a única porta de entrada para os outros módulos."""
from dataclasses import asdict

from livraria.compartilhado import filtrar, obter
from livraria.modulos.catalogo.dominio import Avaliacao, Edicao, Livro, Promocao, media, preco_promocional


class CatalogoAPI:
    def __init__(self, repo):
        self.repo = repo

    def listar_livros(self):
        return self.repo.listar(Livro)

    def obter_livro(self, livro_id):
        return obter(self.repo, Livro, "Livro não encontrado.", id=livro_id)

    def obter_edicao(self, edicao_id):
        return obter(self.repo, Edicao, "Edição inválida.", id=edicao_id)

    def edicoes(self, livro_id):
        """Edições do livro com promoções ativas e preço atual."""
        self.obter_livro(livro_id)
        resultado = []
        for edicao in filtrar(self.repo, Edicao, livro_id=livro_id):
            promocoes = filtrar(self.repo, Promocao, edicao_id=edicao.id, ativa=True)
            resultado.append(dict(asdict(edicao), promocoes=promocoes,
                                  preco_final_centavos=preco_promocional(edicao, promocoes)))
        return resultado

    def preco_atual(self, edicao_id):
        """R02: preço da edição menos promoções ativas, nunca negativo."""
        edicao = self.obter_edicao(edicao_id)
        return preco_promocional(edicao, filtrar(self.repo, Promocao, edicao_id=edicao_id))

    def promocoes_ativas(self):
        """Promoções ativas com o gênero do livro, para avisos de promoção."""
        resultado = []
        for promocao in filtrar(self.repo, Promocao, ativa=True):
            livro = self.obter_livro(self.obter_edicao(promocao.edicao_id).livro_id)
            resultado.append({"descricao": promocao.descricao, "genero": livro.genero})
        return resultado

    def avaliar(self, cliente_id, autor, livro_id, nota, texto=""):
        """R07: uma avaliação por cliente e livro; avaliar de novo atualiza. O cliente é validado por quem chama."""
        nota, texto = Avaliacao.validar(nota, texto)
        with self.repo.transacao():
            self.obter_livro(livro_id)
            existentes = filtrar(self.repo, Avaliacao, cliente_id=cliente_id, livro_id=livro_id)
            avaliacao = existentes[0] if existentes else Avaliacao(0, livro_id, nota, texto, autor, cliente_id)
            avaliacao.nota, avaliacao.texto = nota, texto
            return self.repo.salvar(avaliacao)

    def avaliacoes(self, livro_id):
        lista = filtrar(self.repo, Avaliacao, livro_id=livro_id)
        return {"avaliacoes": lista, "media": media(lista), "total_avaliacoes": len(lista)}

    def avaliacoes_do_cliente(self, cliente_id):
        titulos = {livro.id: livro.titulo for livro in self.listar_livros()}
        return [dict(asdict(a), titulo=titulos[a.livro_id]) for a in filtrar(self.repo, Avaliacao, cliente_id=cliente_id)]
