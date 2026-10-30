"""Armazenamento de pagamentos (pagamentos.txt) e cupons de demonstração."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.pagamentos.dominio import Cupom, Pagamento, UsoCupom


def dados_exemplo():
    return [
        Cupom("LEITURA10", "10% de desconto", "percentual", 10, True),
        Cupom("BEMVINDO5", "R$ 5,00 de desconto", "fixo", 500, True),
        Cupom("ANTIGO20", "Cupom expirado de demonstração", "percentual", 20, False),
    ]


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Cupom, UsoCupom, Pagamento), {Cupom: ("codigo",)}, dados_exemplo())
