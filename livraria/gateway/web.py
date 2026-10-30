import os
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.texto import nota_media, reais


def create_app(bff):
    app = Flask(__name__)
    app.secret_key = os.environ.get("LIVRARIA_SECRET", "chave-local-apenas-demonstracao")
    app.json.ensure_ascii = False
    app.add_template_filter(reais, "reais")
    app.add_template_filter(nota_media, "nota_media")

    @app.errorhandler(RegraInvalida)
    def erro(exc):
        if request.path.startswith("/api/"):
            return jsonify(erro=str(exc)), 404
        flash(str(exc), "erro")
        return redirect(request.referrer or url_for("catalogo"))

    def logado(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("cliente_id"):
                flash("Cadastre-se ou entre para continuar.", "erro")
                return redirect(url_for("area"))
            return fn(*args, **kwargs)
        return wrapper

    @app.context_processor
    def contexto():
        return {"cliente_atual": bff.cliente_atual(session.get("cliente_id"))}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/livros")
    def api_livros():
        return jsonify(bff.api_livros(request.args))

    @app.get("/api/livros/<int:livro_id>")
    def api_livro(livro_id):
        return jsonify(bff.api_livro(livro_id))

    @app.get("/")
    def catalogo():
        return render_template("index.html", **bff.pagina_catalogo(request.args))

    @app.get("/livro/<int:livro_id>")
    def livro(livro_id):
        return render_template("index.html", **bff.pagina_livro(livro_id, session.get("cliente_id")))

    @app.get("/lojas")
    def lojas():
        return render_template("index.html", **bff.pagina_lojas(request.args))

    @app.get("/cliente")
    def area():
        return render_template("index.html", **bff.pagina_cliente(session.get("cliente_id")))

    @app.post("/cadastro")
    def cadastro():
        session["cliente_id"] = bff.cadastrar(request.form)
        flash("Cadastro concluído. Esta é uma sessão local de demonstração.")
        return redirect(url_for("area"))

    @app.post("/entrar")
    def entrar():
        session["cliente_id"] = bff.entrar(request.form)
        return redirect(url_for("area"))

    @app.post("/sair")
    def sair():
        session.clear()
        return redirect(url_for("catalogo"))

    @app.post("/favorito/<int:livro_id>/<acao>")
    @logado
    def favorito(livro_id, acao):
        if acao not in ("adicionar", "remover"):
            abort(404)
        bff.favoritar(session["cliente_id"], livro_id, acao == "adicionar")
        return redirect(url_for("livro", livro_id=livro_id) if acao == "adicionar" else url_for("area"))

    @app.post("/reservar")
    @logado
    def reservar():
        flash(bff.reservar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/comprar")
    @logado
    def comprar():
        flash(bff.comprar(session["cliente_id"], request.form))
        return redirect(url_for("area"))

    @app.post("/reserva/<codigo>/<acao>")
    @logado
    def reserva_acao(codigo, acao):
        if acao == "retirar":
            flash(bff.retirar(session["cliente_id"], codigo))
        elif acao == "cancelar":
            flash(bff.cancelar(session["cliente_id"], codigo))
        else:
            abort(404)
        return redirect(url_for("area"))

    @app.post("/alertar")
    @logado
    def alertar():
        flash(bff.alertar(session["cliente_id"], request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/repor")
    def repor():
        flash(bff.repor(request.form))
        return redirect(request.referrer or url_for("catalogo"))

    @app.post("/avaliar/<int:livro_id>")
    @logado
    def avaliar(livro_id):
        flash(bff.avaliar(session["cliente_id"], livro_id, request.form))
        return redirect(url_for("livro", livro_id=livro_id))

    return app
