"""Aplicação (app/servidor): cria o Flask, registra as rotas da API e entrega os arquivos do cliente.

O servidor não gera telas: só responde JSON em /api. A pasta cliente/ é enviada como arquivos estáticos
(HTML, CSS e JS) e, a partir daí, o navegador conversa com o servidor apenas por HTTP/REST.
"""
import os
from pathlib import Path

from flask import Flask, send_from_directory

from livraria.servidor.rotas import criar_rotas

PASTA_CLIENTE = Path(__file__).resolve().parents[2] / "cliente"


def create_app(modulos):
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.environ.get("LIVRARIA_SECRET", "chave-local-apenas-demonstracao")
    app.json.ensure_ascii = False
    app.register_blueprint(criar_rotas(modulos))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def cliente():
        return send_from_directory(PASTA_CLIENTE, "index.html")

    @app.get("/<path:arquivo>")
    def arquivos_do_cliente(arquivo):
        return send_from_directory(PASTA_CLIENTE, arquivo)

    return app
