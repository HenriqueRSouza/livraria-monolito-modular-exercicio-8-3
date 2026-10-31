"""Ponto de entrada do servidor: monta a camada de negócios (módulos com dados em LIVRARIA_DADOS) e a API Flask.

Local:   python app.py
Azure:   gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 app:app
"""
import os

from livraria.aplicacao import montar_modulos
from livraria.servidor.app import create_app


def criar_app(pasta_dados=None):
    return create_app(montar_modulos(pasta_dados or os.environ.get("LIVRARIA_DADOS", "dados")))


def __getattr__(nome):
    """`app:app` (padrão do Azure App Service) cria o app só quando o gunicorn pede, não ao importar nos testes."""
    if nome == "app":
        globals()["app"] = criar_app()
        return globals()["app"]
    raise AttributeError(nome)


if __name__ == "__main__":
    criar_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
