"""C08–C10 pela API REST que o cliente consome (JSON), mais /health e entrega dos arquivos do cliente."""
import tempfile
import unittest

from app import criar_app


class ApiRestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = criar_app(self.tmp.name)
        self.app.testing = True
        self.web = self.app.test_client()

    def entrar(self):
        resposta = self.web.post("/api/clientes", json={"nome": "Ana", "email": "ana@example.com", "bairro": "Centro",
                                                       "interesses": "Ficção"})
        self.assertEqual(resposta.status_code, 201)
        return resposta.json["cliente"]

    def test_servidor_entrega_o_cliente_e_health(self):
        self.assertEqual(self.web.get("/health").json, {"status": "ok"})
        with self.web.get("/") as pagina:
            self.assertIn('<script type="module" src="/js/controller.js">', pagina.text)
        for arquivo in ("/js/model.js", "/js/view.js", "/js/controller.js", "/css/estilo.css"):
            with self.web.get(arquivo) as resposta:
                self.assertEqual(resposta.status_code, 200, arquivo)

    def test_c01_c03_consultas_publicas(self):
        self.assertEqual([l["titulo"] for l in self.web.get("/api/livros?titulo=mares").json], ["A Casa das Marés"])
        self.assertEqual(self.web.get("/api/livros?genero=inexistente").json, [])
        livro = self.web.get("/api/livros/1").json
        self.assertEqual((livro["media"], livro["total_avaliacoes"], len(livro["edicoes"])), (5.0, 1, 2))
        self.assertEqual(livro["edicoes"][0]["preco_final_centavos"], 4000)
        self.assertEqual(livro["edicoes"][0]["estoques"][0]["secao"], "Literatura")
        resposta = self.web.get("/api/livros/999")
        self.assertEqual((resposta.status_code, resposta.json["erro"]), (404, "Livro não encontrado."))
        self.assertEqual([l["nome"] for l in self.web.get("/api/lojas?bairro=centro").json], ["Unidade Centro"])

    def test_sessao_cadastro_entrada_e_saida(self):
        self.assertEqual(self.web.get("/api/sessao").json, {"cliente": None})
        self.assertEqual(self.web.get("/api/minha-area").status_code, 401)
        ana = self.entrar()
        self.assertEqual(self.web.get("/api/sessao").json["cliente"]["id"], ana["id"])
        repetido = self.web.post("/api/clientes", json={"nome": "Ana", "email": "ANA@example.com", "bairro": "Centro"})
        self.assertEqual((repetido.status_code, repetido.json["erro"]), (400, "Email já cadastrado."))
        self.assertEqual(self.web.delete("/api/sessao").status_code, 204)
        self.assertEqual(self.web.post("/api/reservas", json={"edicao_id": 1, "loja_id": 1}).status_code, 401)
        self.assertEqual(self.web.post("/api/sessao", json={"email": "ana@example.com"}).json["cliente"]["nome"], "Ana")
        self.assertEqual(self.web.post("/api/sessao", json={"email": "x@example.com"}).status_code, 400)

    def test_c08_reserva_retirada_e_historico(self):
        self.entrar()
        resposta = self.web.post("/api/reservas", json={"edicao_id": "1", "loja_id": "1"})
        self.assertEqual(resposta.status_code, 201)
        self.assertIn("RES-000001 por R$ 40,00", resposta.json["mensagem"])
        self.assertEqual(self.web.get("/api/livros/1").json["edicoes"][0]["estoques"][0]["quantidade"], 0)
        self.assertIn("concluída", self.web.post("/api/reservas/RES-000001/retirada").json["mensagem"])
        area = self.web.get("/api/minha-area").json
        self.assertEqual(area["historico"]["pontos"], 40)
        self.assertEqual(area["historico"]["reservas"][0]["estado"], "retirada")
        self.assertEqual(self.web.post("/api/reservas/RES-000001/cancelamento").status_code, 400)

    def test_c08_favoritos_alerta_reposicao_e_compra(self):
        self.entrar()
        self.web.put("/api/favoritos/1")
        self.assertEqual([b["id"] for b in self.web.get("/api/minha-area").json["favoritos"]], [1])
        self.web.delete("/api/favoritos/1")
        self.assertEqual(self.web.post("/api/alertas", json={"edicao_id": 2, "loja_id": 1}).status_code, 201)
        self.web.post("/api/estoque/reposicao", json={"edicao_id": 2, "loja_id": 1})
        notificacoes = self.web.get("/api/minha-area").json["notificacoes"]
        self.assertIn("reposicao", [n["tipo"] for n in notificacoes])
        self.assertEqual(self.web.post("/api/compras", json={"edicao_id": 2, "loja_id": 1}).status_code, 201)
        self.assertEqual(self.web.get("/api/minha-area").json["historico"]["pontos"], 75)
        resposta = self.web.post("/api/compras", json={"edicao_id": 2, "loja_id": 1})
        self.assertEqual((resposta.status_code, resposta.json["erro"]), (400, "Sem estoque nesta unidade/edição."))
        self.assertEqual(self.web.post("/api/compras", json={"edicao_id": "abc"}).json["erro"], "Dados do formulário inválidos.")

    def test_c09_avaliacao(self):
        self.assertEqual(self.web.put("/api/livros/1/avaliacao", json={"nota": 4}).status_code, 401)
        self.entrar()
        resposta = self.web.put("/api/livros/1/avaliacao", json={"nota": "4", "texto": "Gostei"})
        self.assertEqual(resposta.json["mensagem"], "Avaliação registrada. Obrigado!")
        self.assertEqual(self.web.get("/api/livros/1").json["media"], 4.5)
        self.assertIn("nota deve ser", self.web.put("/api/livros/1/avaliacao", json={"nota": 9}).json["erro"])
        self.assertEqual(self.web.put("/api/livros/99/avaliacao", json={"nota": 5}).status_code, 400)

    def test_c10_cupom(self):
        self.entrar()
        resposta = self.web.post("/api/reservas", json={"edicao_id": 1, "loja_id": 2, "cupom": "leitura10"})
        self.assertIn("R$ 36,00 com cupom LEITURA10", resposta.json["mensagem"])
        resposta = self.web.post("/api/compras", json={"edicao_id": 1, "loja_id": 2, "cupom": "LEITURA10"})
        self.assertIn("já utilizado", resposta.json["erro"])
        resposta = self.web.post("/api/compras", json={"edicao_id": 1, "loja_id": 2, "cupom": ""})
        self.assertIn("R$ 40,00 (sem cobrança real)", resposta.json["mensagem"])

    def test_sessao_de_cliente_inexistente_vira_401(self):
        with self.web.session_transaction() as sessao:
            sessao["cliente_id"] = 999
        self.assertEqual(self.web.put("/api/livros/1/avaliacao", json={"nota": 5}).status_code, 401)
        self.assertEqual(self.web.get("/api/sessao").json, {"cliente": None})

    def test_dados_compartilhados_entre_instancias(self):
        """Simula dois workers do gunicorn lendo a mesma pasta de dados."""
        self.entrar()
        self.web.post("/api/reservas", json={"edicao_id": 1, "loja_id": 1})
        outro = criar_app(self.tmp.name).test_client()
        self.assertEqual(outro.get("/api/livros/1").json["edicoes"][0]["estoques"][0]["quantidade"], 0)


if __name__ == "__main__":
    unittest.main()
