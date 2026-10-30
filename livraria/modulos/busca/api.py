"""API pública da Busca (R01)."""
from livraria.compartilhado.texto import normalizar


class BuscaAPI:
    def __init__(self, catalogo):
        self.catalogo = catalogo

    def buscar_livros(self, titulo="", autor="", genero=""):
        """Trechos sem diferenciar caixa/acentos, filtros combinados com E, em ordem de id."""
        filtros = {"titulo": titulo, "autor": autor, "genero": genero}
        return [livro for livro in self.catalogo.listar_livros()
                if all(normalizar(termo) in normalizar(getattr(livro, campo)) for campo, termo in filtros.items() if termo)]
