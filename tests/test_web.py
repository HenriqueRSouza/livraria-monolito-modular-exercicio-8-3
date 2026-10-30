"""C08–C10: navegação HTTP pelo gateway Flask, mais /health e a API REST, gravando em pasta temporária."""
import tempfile
import unittest

from app import criar_app


class FluxoHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = criar_app(self.tmp.name)
        self.app.testing = True
        self.web = self.app.test_client()

    def entrar(self):
        self.web.post("/cadastro", data={"nome": "Ana", "email": "ana@example.com", "bairro": "Centro", "interesses": "Ficção"})

    def test_health_e_api_rest(self):
        self.assertEqual(self.web.get("/health").json, {"status": "ok"})
        self.assertEqual([l["titulo"] for l in self.web.get("/api/livros?genero=tecnologia").json], ["Python para Todos"])
        livro = self.web.get("/api/livros/1").json
        self.assertEqual((livro["media"], len(livro["edicoes"])), (5.0, 2))
        self.assertEqual(livro["edicoes"][0]["estoques"][0]["loja_nome"], "Unidade Centro")
        self.assertEqual(self.web.get("/api/livros/999").status_code, 404)

    def test_c08_catalogo_detalhes_estoque_reserva_retirada(self):
        self.assertIn("A Casa das Marés", self.web.get("/?titulo=mares").text)
        self.assertIn("Seção Literatura", self.web.get("/livro/1").text)
        self.assertIn("Unidade Centro", self.web.get("/lojas?bairro=centro").text)
        self.assertNotIn("Unidade Jardim", self.web.get("/lojas?bairro=centro").text)
        self.entrar()
        resposta = self.web.post("/reservar", data={"edicao_id": 1, "loja_id": 1}, follow_redirects=True)
        self.assertIn("RES-000001", resposta.text)
        self.assertIn("Seção Literatura", resposta.text)
        self.assertIn("0 disponível(is)", self.web.get("/livro/1").text)
        resposta = self.web.post("/reserva/RES-000001/retirar", follow_redirects=True)
        self.assertIn("40 pontos", resposta.text)
        self.assertIn("retirada", resposta.text)
        self.assertIn("#1", resposta.text)

    def test_c08_favoritos_alerta_reposicao_compra_e_erros(self):
        self.entrar()
        self.web.post("/favorito/1/adicionar")
        self.assertIn("A Casa das Marés", self.web.get("/cliente").text)
        self.web.post("/favorito/1/remover")
        self.web.post("/alertar", data={"edicao_id": 2, "loja_id": 1})
        self.web.post("/repor", data={"edicao_id": 2, "loja_id": 1})
        self.assertIn("Reposição simulada", self.web.get("/cliente").text)
        self.web.post("/comprar", data={"edicao_id": 2, "loja_id": 1})
        self.assertIn("75 pontos", self.web.get("/cliente").text)
        resposta = self.web.post("/comprar", data={"edicao_id": 2, "loja_id": 1}, follow_redirects=True)
        self.assertIn("Sem estoque", resposta.text)

    def test_c09_avaliacao_pela_interface(self):
        self.assertIn("Entre na sua área para avaliar", self.web.get("/livro/1").text)
        self.entrar()
        resposta = self.web.post("/avaliar/1", data={"nota": "4", "texto": "Gostei"}, follow_redirects=True)
        self.assertIn("Avaliação registrada", resposta.text)
        self.assertIn("4,5", resposta.text)
        self.assertIn("Atualizar minha avaliação", resposta.text)
        self.assertIn("Gostei", self.web.get("/cliente").text)
        resposta = self.web.post("/avaliar/1", data={"nota": "9"}, follow_redirects=True)
        self.assertIn("nota deve ser", resposta.text)
        resposta = self.web.post("/avaliar/1", data={"nota": "abc"}, follow_redirects=True)
        self.assertIn("Dados do formulário inválidos", resposta.text)

    def test_c10_cupom_pela_interface(self):
        self.entrar()
        resposta = self.web.post("/reservar", data={"edicao_id": 1, "loja_id": 2, "cupom": "leitura10"}, follow_redirects=True)
        self.assertIn("R$ 36,00 com cupom LEITURA10", resposta.text)
        self.assertIn("(cupom LEITURA10)", resposta.text)
        resposta = self.web.post("/comprar", data={"edicao_id": 1, "loja_id": 2, "cupom": "LEITURA10"}, follow_redirects=True)
        self.assertIn("já utilizado", resposta.text)
        resposta = self.web.post("/comprar", data={"edicao_id": 1, "loja_id": 2, "cupom": ""}, follow_redirects=True)
        self.assertIn("R$ 40,00 (sem cobrança real)", resposta.text)

    def test_dados_compartilhados_entre_instancias(self):
        """Simula dois workers do gunicorn lendo a mesma pasta de dados."""
        self.entrar()
        self.web.post("/reservar", data={"edicao_id": 1, "loja_id": 1})
        outro = criar_app(self.tmp.name).test_client()
        self.assertIn("0 disponível(is)", outro.get("/livro/1").text)


if __name__ == "__main__":
    unittest.main()
