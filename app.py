"""Ponto de entrada: monta os módulos (cada um com seu arquivo em LIVRARIA_DADOS) e expõe o gateway Flask.

Local:   python app.py
Azure:   gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 app:app
"""
import os

from livraria.aplicacao import montar_modulos
from livraria.gateway.bff import LivrariaBFF
from livraria.gateway.web import create_app


def criar_app(pasta_dados=None):
    modulos = montar_modulos(pasta_dados or os.environ.get("LIVRARIA_DADOS", "dados"))
    return create_app(LivrariaBFF(modulos))


def __getattr__(nome):
    """`app:app` (padrão do Azure App Service) cria o app só quando o gunicorn pede, não ao importar nos testes."""
    if nome == "app":
        globals()["app"] = criar_app()
        return globals()["app"]
    raise AttributeError(nome)


if __name__ == "__main__":
    criar_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
