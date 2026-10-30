"""RepositorioTxt: implementa RepositorioModulo guardando os registros de UM módulo em um arquivo texto.

Cada módulo recebe o seu próprio arquivo (catalogo.txt, estoque.txt, ...), como o "banco por serviço" do diagrama.
Formato: uma linha por registro, "<tipo><TAB><json>", por exemplo:
    livro	{"autor": "L. Andrade", "genero": "Ficção", "id": 1, ...}
"""
import copy
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from livraria.compartilhado.repositorio import RepositorioModulo

try:
    import fcntl  # trava entre processos (vários workers do gunicorn no Linux/Azure)
except ImportError:  # Windows
    fcntl = None

CABECALHO = "# {modulo} — uma linha por registro: <tipo><TAB><json>"


class RepositorioTxt(RepositorioModulo):
    def __init__(self, caminho, tipos, chaves=None, dados_iniciais=()):
        """tipos: entidades do módulo; chaves: campos que identificam registros sem "id"."""
        self.caminho = Path(caminho)
        self.tipos = {classe.__name__.lower(): classe for classe in tipos}
        self.chaves = chaves or {}
        self.trava = threading.RLock()
        self.aberta = None  # dados da transação em andamento
        with self.transacao():
            if not any(self.aberta.values()):
                for registro in dados_iniciais:
                    self.salvar(registro)

    def listar(self, tipo):
        with self.trava:
            dados = self.aberta if self.aberta is not None else self._ler()
            return [copy.deepcopy(r) for r in dados.get(tipo.__name__.lower(), [])]

    def salvar(self, registro):
        with self.transacao():
            lista = self.aberta.setdefault(type(registro).__name__.lower(), [])
            campos = self.chaves.get(type(registro), ("id",))
            if campos == ("id",) and registro.id == 0:
                registro.id = max((r.id for r in lista), default=0) + 1
            chave = tuple(getattr(registro, c) for c in campos)
            for i, atual in enumerate(lista):
                if tuple(getattr(atual, c) for c in campos) == chave:
                    lista[i] = copy.deepcopy(registro)
                    break
            else:
                lista.append(copy.deepcopy(registro))
            return registro

    def remover(self, registro):
        with self.transacao():
            lista = self.aberta.get(type(registro).__name__.lower(), [])
            campos = self.chaves.get(type(registro), ("id",))
            chave = tuple(getattr(registro, c) for c in campos)
            lista[:] = [r for r in lista if tuple(getattr(r, c) for c in campos) != chave]

    @contextmanager
    def transacao(self):
        with self.trava:
            if self.aberta is not None:  # já dentro de uma transação
                yield
                return
            with self._trava_arquivo():
                self.aberta = self._ler()
                try:
                    yield
                    self._gravar(self.aberta)
                finally:
                    self.aberta = None  # em caso de erro nada é gravado

    @contextmanager
    def _trava_arquivo(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        if fcntl is None:
            yield
            return
        with open(self.caminho.with_suffix(".lock"), "w") as trava:
            fcntl.flock(trava, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(trava, fcntl.LOCK_UN)

    def _ler(self):
        dados = {tipo: [] for tipo in self.tipos}
        if self.caminho.exists():
            for linha in self.caminho.read_text(encoding="utf-8").splitlines():
                if linha and not linha.startswith("#"):
                    tipo, conteudo = linha.split("\t", 1)
                    dados[tipo].append(self.tipos[tipo](**json.loads(conteudo)))
        return dados

    def _gravar(self, dados):
        linhas = [CABECALHO.format(modulo=self.caminho.stem)] + [
            f"{tipo}\t{json.dumps(asdict(r), ensure_ascii=False, sort_keys=True)}"
            for tipo, registros in dados.items() for r in registros]
        descritor, temporario = tempfile.mkstemp(dir=self.caminho.parent, suffix=".tmp")
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
        os.replace(temporario, self.caminho)  # troca atômica: o arquivo nunca fica pela metade
