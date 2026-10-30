"""Critérios C01–C07, C09 e C10 testados direto nas APIs dos módulos (arquivos em pasta temporária)."""
import tempfile
import unittest

from livraria.aplicacao import montar_modulos
from livraria.compartilhado import RegraInvalida
from livraria.gateway.bff import LivrariaBFF
from livraria.modulos.pagamentos.dominio import Cupom


class ModulosTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.m = montar_modulos(tmp.name)

    def cliente(self, email="ana@example.com"):
        return self.m.usuarios.cadastrar("Ana", email, "Centro", "Ficção")

    def estoque(self, edicao_id, loja_id):
        return self.m.estoque.obter(edicao_id, loja_id).quantidade

    def test_c01_busca(self):
        self.assertEqual(len(self.m.busca.buscar_livros()), 2)
        self.assertEqual([b.id for b in self.m.busca.buscar_livros("mares", "ANDRADE", "ficcao")], [1])
        self.assertEqual(self.m.busca.buscar_livros(titulo="inexistente"), [])

    def test_c02_detalhes_e_preco_promocional(self):
        livro = LivrariaBFF(self.m).pagina_livro(1)["livro"]
        self.assertEqual(len(livro["edicoes"]), 2)
        self.assertEqual(livro["edicoes"][0]["preco_final_centavos"], 4000)
        self.assertEqual({s["loja_id"]: s["quantidade"] for s in livro["edicoes"][0]["estoques"]}, {1: 1, 2: 2})
        with self.assertRaises(RegraInvalida):
            self.m.catalogo.obter_livro(999)

    def test_c03_lojas_por_bairro(self):
        self.assertEqual([l.nome for l in self.m.estoque.listar_lojas("CENTRO")], ["Unidade Centro"])
        self.assertEqual(self.m.estoque.obter(1, 1).secao, "Literatura")

    def test_c04_cadastro_favoritos_recomendacoes(self):
        for nome, email, bairro in (("", "ok@example.com", "Centro"), ("Ana", "ruim", "Centro"), ("Ana", "ok@example.com", "")):
            with self.assertRaises(RegraInvalida):
                self.m.usuarios.cadastrar(nome, email, bairro)
        ana = self.cliente()
        with self.assertRaises(RegraInvalida):
            self.cliente("ANA@example.com")
        self.assertEqual([b.id for b in self.m.usuarios.recomendacoes(ana)], [1])
        self.m.usuarios.favoritar(ana, 1)
        self.m.usuarios.favoritar(ana, 1)
        self.assertEqual(len(self.m.usuarios.favoritos(ana)), 1)
        self.assertEqual(self.m.usuarios.recomendacoes(ana), [])
        self.m.usuarios.favoritar(ana, 1, adicionar=False)
        self.assertEqual(self.m.usuarios.favoritos(ana), [])
        # evento ClienteCadastrado -> módulo Notificações
        self.assertTrue(any(n.tipo == "promocao" for n in self.m.notificacoes.listar(ana)))

    def test_c05_reserva_ultimo_exemplar_e_cancelamento(self):
        ana = self.cliente()
        reserva = self.m.pedidos.reservar(ana, 1, 1)
        self.assertEqual((reserva.codigo, reserva.estado, reserva.preco_centavos), ("RES-000001", "confirmada", 4000))
        self.assertEqual((self.estoque(1, 1), self.estoque(1, 2)), (0, 2))
        with self.assertRaises(RegraInvalida):
            self.m.pedidos.reservar(ana, 1, 1)
        self.m.pedidos.cancelar(ana, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 1)
        with self.assertRaises(RegraInvalida):
            self.m.pedidos.cancelar(ana, reserva.codigo)

    def test_c06_retirada_compra_direta_pontos_e_pagamento(self):
        ana, bia = self.cliente(), self.cliente("bia@example.com")
        reserva = self.m.pedidos.reservar(ana, 1, 1)
        with self.assertRaises(RegraInvalida):
            self.m.pedidos.retirar(bia, reserva.codigo)
        self.m.pedidos.retirar(ana, reserva.codigo)
        with self.assertRaises(RegraInvalida):
            self.m.pedidos.retirar(ana, reserva.codigo)
        self.assertEqual(self.estoque(1, 1), 0)
        self.m.pedidos.comprar(ana, 1, 2)
        self.assertEqual(self.estoque(1, 2), 1)
        self.assertEqual(self.m.pedidos.historico(ana)["pontos"], 80)
        with self.assertRaises(RegraInvalida):
            self.m.pedidos.comprar(ana, 2, 1)
        # evento CompraRegistrada -> módulo Pagamentos
        self.assertEqual([(p.referencia, p.valor_centavos) for p in self.m.pagamentos.pagamentos()],
                         [("COMPRA-000001", 4000), ("COMPRA-000002", 4000)])

    def test_c07_alerta_e_reposicao(self):
        ana = self.cliente()
        self.m.estoque.alertar(ana, 2, 1)
        self.m.estoque.alertar(ana, 2, 1)
        self.m.estoque.repor(2, 1)
        self.assertEqual(self.estoque(2, 1), 1)
        # evento EstoqueReposto -> módulo Notificações
        self.assertEqual(sum(n.tipo == "reposicao" for n in self.m.notificacoes.listar(ana)), 1)
        with self.assertRaises(RegraInvalida):
            self.m.estoque.alertar(ana, 2, 1)
        with self.assertRaises(RegraInvalida):
            self.m.estoque.alertar(999, 2, 2)

    def test_c09_avaliacoes(self):
        ana = self.cliente()
        bff = LivrariaBFF(self.m)
        bff.avaliar(ana, 1, {"nota": "4", "texto": "  Bom ritmo  "})
        bff.avaliar(ana, 1, {"nota": "3", "texto": "Mudei de ideia"})  # atualiza, não duplica
        avaliacoes = self.m.catalogo.avaliacoes(1)
        self.assertEqual((avaliacoes["media"], avaliacoes["total_avaliacoes"]), (4.0, 2))
        self.assertEqual([(a["titulo"], a["nota"]) for a in self.m.catalogo.avaliacoes_do_cliente(ana)],
                         [("A Casa das Marés", 3)])
        for cliente_id, livro_id, nota, texto in ((ana, 1, 0, ""), (ana, 1, 6, ""), (ana, 1, 5, "x" * 501),
                                                  (ana, 99, 5, ""), (999, 1, 5, "")):
            with self.assertRaises(RegraInvalida):
                bff.avaliar(cliente_id, livro_id, {"nota": nota, "texto": texto})
        self.assertEqual(self.m.catalogo.avaliacoes(2)["media"], None)

    def test_c10_cupons(self):
        self.assertEqual(Cupom("P", "", "percentual", 10, True).aplicar(4005), 3605)  # desconto arredondado para baixo
        self.assertEqual(Cupom("F", "", "fixo", 500, True).aplicar(300), 0)
        ana = self.cliente()
        reserva = self.m.pedidos.reservar(ana, 1, 2, " leitura10 ")
        self.assertEqual((reserva.preco_centavos, reserva.cupom), (3600, "LEITURA10"))
        for cupom in ("LEITURA10", "NAOEXISTE", "ANTIGO20"):  # já usado, inexistente, inativo
            with self.assertRaises(RegraInvalida):
                self.m.pedidos.comprar(ana, 1, 2, cupom)
        self.assertEqual(self.estoque(1, 2), 1)  # nada foi debitado nas falhas
        self.m.pedidos.cancelar(ana, reserva.codigo)  # evento ReservaCancelada libera o cupom em Pagamentos
        self.assertEqual(self.m.pedidos.comprar(ana, 1, 2, "LEITURA10").preco_centavos, 3600)
        self.assertEqual(self.m.pedidos.comprar(ana, 3, 1, "BEMVINDO5").preco_centavos, 7500)

    def test_saga_devolve_estoque_se_o_pedido_falhar(self):
        ana = self.cliente()
        self.m.pagamentos.registrar_uso = lambda *args: (_ for _ in ()).throw(RuntimeError("falha simulada"))
        with self.assertRaises(RuntimeError):
            self.m.pedidos.reservar(ana, 1, 2, "LEITURA10")
        self.assertEqual(self.estoque(1, 2), 2)  # compensação devolveu a unidade
        self.assertEqual(self.m.pedidos.historico(ana)["reservas"], [])


if __name__ == "__main__":
    unittest.main()
