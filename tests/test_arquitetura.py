"""Regras do monólito modular verificadas no código-fonte.

1. Um módulo só importa outro módulo pela api.py dele (nunca dominio.py ou dados.py).
2. Módulos não importam o gateway nem o Flask: só o gateway conhece HTTP.
3. Cada módulo grava no seu próprio arquivo de dados.
"""
import ast
import tempfile
import unittest
from pathlib import Path

from livraria.aplicacao import montar_modulos

RAIZ = Path(__file__).resolve().parent.parent / "livraria"
MODULOS = sorted(p.name for p in (RAIZ / "modulos").iterdir() if p.is_dir() and not p.name.startswith("_"))


def importacoes(arquivo):
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.ImportFrom) and no.module:
            yield no.module
        elif isinstance(no, ast.Import):
            yield from (a.name for a in no.names)


class ArquiteturaTest(unittest.TestCase):
    def test_modulos_do_diagrama(self):
        self.assertEqual(MODULOS, ["busca", "catalogo", "estoque", "notificacoes", "pagamentos", "pedidos", "usuarios"])

    def test_modulo_so_usa_outro_pela_api(self):
        for modulo in MODULOS:
            for arquivo in (RAIZ / "modulos" / modulo).glob("*.py"):
                for nome in importacoes(arquivo):
                    partes = nome.split(".")
                    if partes[:2] == ["livraria", "modulos"] and len(partes) > 2 and partes[2] != modulo:
                        self.assertEqual(partes[3:], ["api"], f"{arquivo.relative_to(RAIZ)} importa {nome}")

    def test_modulos_nao_conhecem_http(self):
        for arquivo in (RAIZ / "modulos").rglob("*.py"):
            for nome in importacoes(arquivo):
                self.assertFalse(nome.startswith(("flask", "livraria.gateway", "livraria.aplicacao")),
                                 f"{arquivo.relative_to(RAIZ)} importa {nome}")

    def test_cada_modulo_tem_seu_arquivo_de_dados(self):
        with tempfile.TemporaryDirectory() as pasta:
            montar_modulos(pasta)
            arquivos = sorted(p.name for p in Path(pasta).glob("*.txt"))
        self.assertEqual(arquivos, ["catalogo.txt", "estoque.txt", "notificacoes.txt", "pagamentos.txt",
                                    "pedidos.txt", "usuarios.txt"])  # busca só lê o catálogo


if __name__ == "__main__":
    unittest.main()
