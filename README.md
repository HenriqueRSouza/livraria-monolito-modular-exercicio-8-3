# Livraria: Exercício 8.3 (Monólito Modular)

Refatoração do MVP da livraria (exercício 7.4, Arquitetura Clean) para um **monólito modular** baseado na arquitetura de microsserviços desenhada no exercício 8.2 ([diagrama no Miro](https://miro.com/app/board/uXjVETAfWIY=/)).

O sistema continua sendo **um único deploy** (um app Flask), mas está dividido nos mesmos módulos que seriam os microsserviços. Cada módulo tem a própria API pública e os próprios dados, e só fala com os outros pela API ou por eventos. Assim, qualquer módulo pode virar um microsserviço depois sem reescrever o resto.

## Do diagrama para o código

| Diagrama (8.2) | Monólito modular (8.3) |
|---|---|
| App Shell + micro-frontends | `livraria/gateway/templates` (telas server-side) |
| API Gateway / BFF | `livraria/gateway/` (`bff.py` + `web.py`), com REST em `/api/livros` |
| Catálogo Service + Catálogo DB | `modulos/catalogo` + `dados/catalogo.txt` |
| Busca Service + Índice | `modulos/busca` (lê o catálogo, sem dados próprios) |
| Usuários Service + Usuários DB | `modulos/usuarios` + `dados/usuarios.txt` |
| Estoque Service + Estoque DB | `modulos/estoque` + `dados/estoque.txt` |
| Pedidos Service + Pedidos DB | `modulos/pedidos` + `dados/pedidos.txt` |
| Pagamentos Service + Pagamentos DB | `modulos/pagamentos` + `dados/pagamentos.txt` (cupons e pagamento simulado) |
| Notificações Service + Notificações DB | `modulos/notificacoes` + `dados/notificacoes.txt` |
| Message Broker | `compartilhado/eventos.py` (barramento em memória) |
| Carrinho Service | não existe no MVP; a compra é direta ou por reserva |

## Estrutura

```
app.py                      -> ponto de entrada (criar_app)
livraria/
  aplicacao.py              -> raiz de composição: cria os módulos, injeta dependências e liga os eventos
  compartilhado/            -> só utilitários genéricos: erro, texto, eventos, repositório TXT
  gateway/                  -> BFF + rotas Flask + templates (única parte que conhece HTTP)
  modulos/
    <modulo>/
      api.py                -> API pública e eventos do módulo (o único arquivo que os outros podem importar)
      dominio.py            -> entidades e regras internas
      dados.py              -> repositório do módulo (arquivo próprio) e dados de exemplo
tests/
```

## Regras do monólito modular

1. **Fronteiras:** um módulo só importa outro pela `api.py`. `dominio.py` e `dados.py` são privados.
2. **Banco por módulo:** cada módulo grava no seu arquivo e guarda apenas IDs de outros módulos (ex.: a reserva guarda `edicao_id`, não o livro).
3. **Sem ciclos:** `busca → catalogo`, `usuarios → catalogo`, `estoque → usuarios`, `pedidos → usuarios, catalogo, estoque, pagamentos`, `notificacoes → catalogo, estoque`.
4. **Eventos para reações:** quem publica não sabe quem escuta. A ligação fica em `aplicacao.py`:

| Evento | Publicado por | Quem reage |
|---|---|---|
| `ClienteCadastrado` | usuarios | notificacoes: avisos de promoção |
| `EstoqueReposto` | estoque | notificacoes: avisos de reposição |
| `ReservaCancelada` | pedidos | pagamentos: libera o cupom |
| `CompraRegistrada` | pedidos | pagamentos: registra o pagamento simulado |

5. **Saga em vez de transação global:** reservar e comprar usam quatro módulos. O pedido valida tudo antes, debita o estoque e, se gravar falhar, devolve a unidade (compensação).

As regras 1 a 3 são verificadas automaticamente em `tests/test_arquitetura.py`.

As regras de negócio (R01–R08) e os critérios de aceite (C01–C10) são os mesmos do 7.4. Veja `docs/specs/livraria.md`.

## Como rodar

Requer Python 3.10+.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra http://127.0.0.1:5000/. Na primeira execução, a pasta `dados/` é criada com um arquivo por módulo. Para usar outra pasta: `LIVRARIA_DADOS=/outra/pasta .venv/bin/python app.py`.

Endpoints extras: `GET /health`, `GET /api/livros?titulo=&autor=&genero=` e `GET /api/livros/<id>`.

## Testes

```sh
.venv/bin/python -m unittest discover -v
```

- `tests/test_modulos.py`: C01–C07, C09, C10, eventos entre módulos e compensação da saga.
- `tests/test_arquitetura.py`: fronteiras dos módulos e um arquivo de dados por módulo.
- `tests/test_repositorio_txt.py`: formato do arquivo, persistência ao reabrir e transação que não grava pela metade.
- `tests/test_web.py`: navegação pela interface (C08–C10), `/health` e API REST.

## Deploy no Azure

### Opção 1: Azure App Service (Python, sem Docker)

```sh
az login
az group create -n rg-livraria -l brazilsouth
az appservice plan create -g rg-livraria -n plan-livraria --is-linux --sku B1
az webapp create -g rg-livraria -p plan-livraria -n <nome-do-app> --runtime "PYTHON:3.12"

az webapp config set -g rg-livraria -n <nome-do-app> --startup-file \
  'gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 app:app'
az webapp config appsettings set -g rg-livraria -n <nome-do-app> --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  LIVRARIA_DADOS=/home/dados \
  LIVRARIA_SECRET=<uma-chave-aleatoria>
az webapp config set -g rg-livraria -n <nome-do-app> --generic-configurations '{"healthCheckPath": "/health"}'
```

`/home` é o armazenamento persistente do App Service, então os arquivos em `/home/dados` continuam lá após reinícios e novos deploys.

**Deploy automático pelo GitHub Actions** (`.github/workflows/main_engsoftwarelab8.yml`):

O workflow foi gerado pelo **Deployment Center** do App Service (login no Azure por OIDC, com os secrets `AZUREAPPSERVICE_*` criados automaticamente). A cada push na `main` ele roda os testes e, se passarem, publica no Web App `EngSoftwareLab8`. Para outro Web App, configure o Deployment Center dele apontando para este repositório.

Se o site mostrar a página padrão "Your app service is up and running", falta o comando de inicialização acima. O `app.py` também expõe `app`, então o padrão do Azure (`gunicorn app:app`) funciona.

### Opção 2: contêiner (App Service for Containers ou Container Apps)

```sh
az acr create -g rg-livraria -n <registro> --sku Basic
az acr build -r <registro> -t livraria:latest .
az containerapp up -g rg-livraria -n livraria --image <registro>.azurecr.io/livraria:latest \
  --ingress external --target-port 8000 --env-vars LIVRARIA_SECRET=<uma-chave-aleatoria>
```

No Container Apps o disco do contêiner é temporário. Para manter os dados, monte um Azure Files em `/home/dados`.

### Limites conhecidos

- Rode com **1 worker** (e várias threads). Os arquivos TXT têm trava entre processos, mas a saga de pedidos usa uma trava em memória, e o barramento de eventos fica em memória.
- Para escalar horizontalmente, troque o `RepositorioTxt` por um repositório em banco (ex.: Azure Database for PostgreSQL, um schema por módulo) e o barramento por Azure Service Bus. As APIs dos módulos não mudam.
- Cadastro sem senha, pagamento e notificações continuam sendo **simulações** de demonstração.
