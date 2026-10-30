"""Raiz de composição do monólito modular.

Cria cada módulo com o seu próprio arquivo de dados, injeta as APIs de que ele depende e liga os eventos no
barramento. É o único lugar que conhece todos os módulos por dentro.

Dependências entre módulos (sem ciclos):
    busca -> catalogo
    usuarios -> catalogo
    estoque -> usuarios
    pedidos -> usuarios, catalogo, estoque, pagamentos
    notificacoes -> catalogo, estoque
Eventos:
    ClienteCadastrado (usuarios) -> notificacoes.avisar_promocoes
    EstoqueReposto    (estoque)  -> notificacoes.avisar_reposicao
    ReservaCancelada  (pedidos)  -> pagamentos.liberar_uso
    CompraRegistrada  (pedidos)  -> pagamentos.registrar_pagamento
"""
from pathlib import Path
from types import SimpleNamespace

from livraria.compartilhado.eventos import BarramentoEventos
from livraria.modulos.busca.api import BuscaAPI
from livraria.modulos.catalogo import dados as dados_catalogo
from livraria.modulos.catalogo.api import CatalogoAPI
from livraria.modulos.estoque import dados as dados_estoque
from livraria.modulos.estoque.api import EstoqueAPI, EstoqueReposto
from livraria.modulos.notificacoes import dados as dados_notificacoes
from livraria.modulos.notificacoes.api import NotificacoesAPI
from livraria.modulos.pagamentos import dados as dados_pagamentos
from livraria.modulos.pagamentos.api import PagamentosAPI
from livraria.modulos.pedidos import dados as dados_pedidos
from livraria.modulos.pedidos.api import CompraRegistrada, PedidosAPI, ReservaCancelada
from livraria.modulos.usuarios import dados as dados_usuarios
from livraria.modulos.usuarios.api import ClienteCadastrado, UsuariosAPI


def montar_modulos(pasta_dados):
    pasta = Path(pasta_dados)
    barramento = BarramentoEventos()

    catalogo = CatalogoAPI(dados_catalogo.criar_repositorio(pasta / "catalogo.txt"))
    busca = BuscaAPI(catalogo)
    usuarios = UsuariosAPI(dados_usuarios.criar_repositorio(pasta / "usuarios.txt"), catalogo, barramento)
    estoque = EstoqueAPI(dados_estoque.criar_repositorio(pasta / "estoque.txt"), usuarios, barramento)
    pagamentos = PagamentosAPI(dados_pagamentos.criar_repositorio(pasta / "pagamentos.txt"))
    pedidos = PedidosAPI(dados_pedidos.criar_repositorio(pasta / "pedidos.txt"),
                         usuarios, catalogo, estoque, pagamentos, barramento)
    notificacoes = NotificacoesAPI(dados_notificacoes.criar_repositorio(pasta / "notificacoes.txt"), catalogo, estoque)

    barramento.assinar(ClienteCadastrado, lambda e: notificacoes.avisar_promocoes(e.cliente_id, e.interesses))
    barramento.assinar(EstoqueReposto, lambda e: notificacoes.avisar_reposicao(e.edicao_id, e.loja_id, e.clientes))
    barramento.assinar(ReservaCancelada, lambda e: pagamentos.liberar_uso(e.codigo))
    barramento.assinar(CompraRegistrada, lambda e: pagamentos.registrar_pagamento(e.referencia, e.valor_centavos))

    return SimpleNamespace(catalogo=catalogo, busca=busca, usuarios=usuarios, estoque=estoque,
                           pagamentos=pagamentos, pedidos=pedidos, notificacoes=notificacoes)
