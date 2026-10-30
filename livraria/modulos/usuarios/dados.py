"""Armazenamento de usuários (usuarios.txt). Começa vazio."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.usuarios.dominio import Cliente, Favorito


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Cliente, Favorito), chaves={Favorito: ("cliente_id", "livro_id")})
