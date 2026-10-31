"""Regras da arquitetura Cliente-Servidor verificadas no código-fonte.

Cliente (cliente/js):
1. Só o Model conversa com o servidor (fetch na API REST).
2. A View só gera HTML: não importa Model nem Controller e não trata eventos.
3. O Controller liga View e Model.
Servidor (livraria/):
4. Routes só usam a API pública dos módulos (camada de Negócios), nunca dominio.py ou dados.py.
5. Negócios não conhecem HTTP: módulos não importam Flask nem o servidor.
6. Um módulo só usa outro pela api.py dele, e cada módulo grava no seu próprio arquivo de dados.
"""
import ast
import re
import tempfile
import unittest
from pathlib import Path

from livraria.aplicacao import montar_modulos

RAIZ = Path(__file__).resolve().parent.parent
LIVRARIA = RAIZ / "livraria"
JS = RAIZ / "cliente" / "js"
MODULOS = sorted(p.name for p in (LIVRARIA / "modulos").iterdir() if p.is_dir() and not p.name.startswith("_"))


def importacoes(arquivo):
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.ImportFrom) and no.module:
            yield no.module
        elif isinstance(no, ast.Import):
            yield from (a.name for a in no.names)


def importacoes_js(arquivo):
    return set(re.findall(r'from\s+"\./([\w-]+)\.js"', arquivo.read_text(encoding="utf-8")))


class ClienteMvcTest(unittest.TestCase):
    def test_so_o_model_fala_com_o_servidor(self):
        for arquivo in JS.glob("*.js"):
            usa_rede = re.search(r"\bfetch\(|XMLHttpRequest", arquivo.read_text(encoding="utf-8"))
            self.assertEqual(bool(usa_rede), arquivo.name == "model.js", arquivo.name)

    def test_view_so_gera_html(self):
        texto = (JS / "view.js").read_text(encoding="utf-8")
        self.assertEqual(importacoes_js(JS / "view.js"), set())
        self.assertNotIn("addEventListener", texto)
        self.assertNotIn("document.", texto)

    def test_controller_liga_view_e_model(self):
        self.assertEqual(importacoes_js(JS / "controller.js"), {"model", "view"})
        self.assertEqual(importacoes_js(JS / "model.js"), set())

    def test_cliente_usa_rotas_que_existem_no_servidor(self):
        from app import criar_app
        with tempfile.TemporaryDirectory() as pasta:
            regras = [r.rule for r in criar_app(pasta).url_map.iter_rules() if r.rule.startswith("/api")]
        padroes = [re.compile("^" + re.sub(r"<[^>]+>", "[^/?]+", regra) + "$") for regra in regras]
        caminhos = re.findall(r'api\(\s*[^,]+,\s*[`"](/[^`"?]*)', (JS / "model.js").read_text(encoding="utf-8"))
        self.assertGreater(len(caminhos), 10)
        for caminho in caminhos:
            caminho = "/api" + re.sub(r"\$\{[^}]+\}", "x", caminho)
            self.assertTrue(any(p.match(caminho) for p in padroes), caminho)


class ServidorCamadasTest(unittest.TestCase):
    def test_modulos_da_camada_de_negocios(self):
        self.assertEqual(MODULOS, ["busca", "catalogo", "estoque", "notificacoes", "pagamentos", "pedidos", "usuarios"])

    def test_rotas_so_usam_a_api_dos_modulos(self):
        for arquivo in (LIVRARIA / "servidor").glob("*.py"):
            for nome in importacoes(arquivo):
                self.assertFalse(nome.startswith("livraria.modulos"), f"{arquivo.name} importa {nome}")

    def test_negocios_nao_conhecem_http(self):
        for arquivo in (LIVRARIA / "modulos").rglob("*.py"):
            for nome in importacoes(arquivo):
                self.assertFalse(nome.startswith(("flask", "livraria.servidor", "livraria.aplicacao")),
                                 f"{arquivo.relative_to(LIVRARIA)} importa {nome}")

    def test_modulo_so_usa_outro_pela_api(self):
        for modulo in MODULOS:
            for arquivo in (LIVRARIA / "modulos" / modulo).glob("*.py"):
                for nome in importacoes(arquivo):
                    partes = nome.split(".")
                    if partes[:2] == ["livraria", "modulos"] and len(partes) > 2 and partes[2] != modulo:
                        self.assertEqual(partes[3:], ["api"], f"{arquivo.relative_to(LIVRARIA)} importa {nome}")

    def test_cada_modulo_tem_seu_arquivo_de_dados(self):
        with tempfile.TemporaryDirectory() as pasta:
            montar_modulos(pasta)
            arquivos = sorted(p.name for p in Path(pasta).glob("*.txt"))
        self.assertEqual(arquivos, ["catalogo.txt", "estoque.txt", "notificacoes.txt", "pagamentos.txt",
                                    "pedidos.txt", "usuarios.txt"])  # busca só lê o catálogo


if __name__ == "__main__":
    unittest.main()
