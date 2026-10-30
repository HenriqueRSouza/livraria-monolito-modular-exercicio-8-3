"""Armazenamento de pedidos (pedidos.txt). Começa vazio."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.pedidos.dominio import Compra, Reserva


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Reserva, Compra))
