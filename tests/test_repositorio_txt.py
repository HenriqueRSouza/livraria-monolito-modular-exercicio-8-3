"""Persistência em TXT por módulo: formato legível, dados que continuam lá ao reabrir e transação que não grava pela metade."""
import json
import tempfile
import unittest
from pathlib import Path

from livraria.aplicacao import montar_modulos
from livraria.compartilhado.repositorio import RepositorioModulo
from livraria.modulos.catalogo import dados as dados_catalogo
from livraria.modulos.catalogo.dominio import Livro


class RepositorioTxtTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pasta = Path(tmp.name)

    def test_implementa_a_interface_e_grava_dados_de_exemplo(self):
        repo = dados_catalogo.criar_repositorio(self.pasta / "catalogo.txt")
        self.assertIsInstance(repo, RepositorioModulo)
        self.assertEqual(len(repo.listar(Livro)), 2)
        linhas = (self.pasta / "catalogo.txt").read_text(encoding="utf-8").splitlines()
        self.assertTrue(linhas[0].startswith("# catalogo"))
        for linha in linhas[1:]:
            tipo, conteudo = linha.split("\t")
            self.assertIsInstance(json.loads(conteudo), dict)
        self.assertIn('livro\t{"autor": "L. Andrade"', "\n".join(linhas))
        dados_catalogo.criar_repositorio(self.pasta / "catalogo.txt")  # reabrir não duplica os dados de exemplo
        self.assertEqual(len(dados_catalogo.criar_repositorio(self.pasta / "catalogo.txt").listar(Livro)), 2)

    def test_dados_persistem_ao_reabrir(self):
        m = montar_modulos(self.pasta)
        ana = m.usuarios.cadastrar("Ana", "ana@example.com", "Centro")
        reserva = m.pedidos.reservar(ana, 1, 1, "LEITURA10")
        reaberto = montar_modulos(self.pasta)
        self.assertEqual(reaberto.estoque.obter(1, 1).quantidade, 0)
        self.assertEqual(reaberto.pedidos.historico(ana)["reservas"][0]["codigo"], reserva.codigo)
        self.assertIn("LEITURA10", (self.pasta / "pagamentos.txt").read_text(encoding="utf-8"))
        self.assertNotIn("LEITURA10", (self.pasta / "estoque.txt").read_text(encoding="utf-8"))

    def test_erro_no_meio_da_operacao_nao_grava_nada(self):
        repo = dados_catalogo.criar_repositorio(self.pasta / "catalogo.txt")
        antes = (self.pasta / "catalogo.txt").read_text(encoding="utf-8")
        with self.assertRaises(RuntimeError):
            with repo.transacao():
                repo.salvar(Livro(0, "Rascunho", "X", "Y", "Z"))
                raise RuntimeError("falha simulada")
        self.assertEqual((self.pasta / "catalogo.txt").read_text(encoding="utf-8"), antes)


if __name__ == "__main__":
    unittest.main()
