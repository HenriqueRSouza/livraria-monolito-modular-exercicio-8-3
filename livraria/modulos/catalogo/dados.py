"""Armazenamento do catálogo (catalogo.txt) e dados de exemplo gravados na primeira execução."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.catalogo.dominio import Avaliacao, Edicao, Livro, Promocao


def dados_exemplo():
    return [
        Livro(1, "A Casa das Marés", "L. Andrade", "Ficção", "Uma viagem às memórias de uma cidade costeira."),
        Livro(2, "Python para Todos", "Ana Ribeiro", "Tecnologia", "Introdução prática à programação."),
        Edicao(1, 1, "Brochura", 2024, 5000), Edicao(2, 1, "Capa dura", 2025, 7500), Edicao(3, 2, "Brochura", 2024, 8000),
        Promocao(1, 1, "Oferta de demonstração", 1000, True),
        Avaliacao(1, 1, 5, "Envolvente", "Leitora demo"),
    ]


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Livro, Edicao, Promocao, Avaliacao), dados_iniciais=dados_exemplo())
