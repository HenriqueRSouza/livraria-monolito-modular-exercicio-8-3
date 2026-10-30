"""Armazenamento de notificações (notificacoes.txt). Começa vazio."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.notificacoes.dominio import Notificacao


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Notificacao,))
