# Livraria: Exercício 8.5 (Arquitetura Cliente-Servidor)

> Branch `exercicio-8-5-cliente-servidor`. A `main` guarda o Exercício 8.3 (monólito modular).

Refatoração do MVP da livraria para a **arquitetura Cliente-Servidor** desenhada no [board do Miro](https://miro.com/app/board/uXjVETAfWIY=/) (diagrama "Arquitetura"):

```
CAMADA CLIENTE (navegador)                         CAMADA SERVIDOR (Python/Flask)
┌──────────────────────────┐                      ┌───────────────────────────────┐
│ View        (telas)      │                      │ Aplicação  (app/servidor)     │
│   ↓                      │    HTTP / REST       │   ↓                           │
│ Controller  (eventos)    │ ───── JSON ────────▶ │ Routes     (rotas/endpoints)  │
│   ↓                      │ ◀─────────────────── │   ↓                           │
│ Model       (estado)     │                      │ Negócios   (regras)           │
└──────────────────────────┘                      │   ↓                           │
                                                  │ Dados      (repositórios)  ◀──┼── Banco de dados
                                                  └───────────────────────────────┘   (livros, usuários, pedidos)
```

Antes (8.3), o servidor montava as páginas HTML. Agora o servidor **só responde JSON** em `/api`, e o cliente é um app JavaScript que roda no navegador e desenha as telas sozinho.

## Do diagrama para o código

| Diagrama | Código | O que faz |
|---|---|---|
| **View** | `cliente/js/view.js` | Gera o HTML das telas a partir dos dados. Não chama o servidor nem trata eventos. |
| **Controller** | `cliente/js/controller.js` | Escuta links e formulários (`data-acao`), chama o Model e manda a View redesenhar. |
| **Model** | `cliente/js/model.js` | Guarda o estado (cliente logado, mensagens) e é o único arquivo que faz requisições HTTP. |
| **HTTP / REST** | `/api/...` em JSON | Contrato entre cliente e servidor (tabela abaixo). |
| **Aplicação** | `app.py` + `livraria/servidor/app.py` | Cria o Flask, registra as rotas e entrega os arquivos do cliente. |
| **Routes** | `livraria/servidor/rotas.py` | Endpoints REST: traduzem JSON para chamadas de negócio e devolvem JSON. |
| **Negócios** | `livraria/modulos/*/api.py` | Regras R01–R08, organizadas nos módulos do 8.3 (catálogo, busca, usuários, estoque, pedidos, pagamentos, notificações). |
| **Dados** | `livraria/modulos/*/dados.py` + `compartilhado/repositorio_txt.py` | Repositórios que leem e gravam os registros. |
| **Banco de dados** | pasta `LIVRARIA_DADOS` (`dados/`) | Um arquivo TXT por módulo (`catalogo.txt`, `usuarios.txt`, `pedidos.txt`...). |

## API REST

| Método e caminho | Uso | Login |
|---|---|---|
| `GET /api/livros?titulo=&autor=&genero=` | busca no catálogo | não |
| `GET /api/livros/<id>` | detalhes, edições, estoque por loja e avaliações | não |
| `GET /api/lojas?bairro=` | lojas por bairro | não |
| `GET /api/sessao` | cliente logado (ou `null`) | não |
| `POST /api/clientes` | cadastro (já entra na sessão) | não |
| `POST /api/sessao` / `DELETE /api/sessao` | entrar pelo email / sair | não |
| `GET /api/minha-area` | histórico, pontos, favoritos, recomendações, notificações e avaliações | sim |
| `PUT` / `DELETE /api/favoritos/<livro_id>` | salvar / remover favorito | sim |
| `POST /api/reservas` | reservar `{edicao_id, loja_id, cupom}` | sim |
| `POST /api/reservas/<codigo>/retirada` | retirar a reserva (vira compra) | sim |
| `POST /api/reservas/<codigo>/cancelamento` | cancelar a reserva | sim |
| `POST /api/compras` | compra direta `{edicao_id, loja_id, cupom}` | sim |
| `POST /api/alertas` | avisar quando repor `{edicao_id, loja_id}` | sim |
| `POST /api/estoque/reposicao` | reposição simulada (+1 unidade) | não |
| `PUT /api/livros/<id>/avaliacao` | avaliar `{nota, texto}` | sim |
| `GET /health` | verificação de saúde (Azure) | não |

Erros de regra voltam como `{"erro": "mensagem"}` com status 400 (404 em consultas). Ação pessoal sem login volta 401. A sessão fica num cookie do Flask, no mesmo domínio do cliente.

## Regras da arquitetura

1. O cliente só fala com o servidor por HTTP/REST, e só o **Model** faz requisições.
2. A **View** não importa Model nem Controller; o **Controller** liga os dois.
3. O servidor não gera telas: só JSON.
4. **Routes** só usam a API pública dos módulos de negócio, nunca as entidades ou os repositórios.
5. **Negócios** não conhecem HTTP (nada de Flask nos módulos).

Todas são verificadas em `tests/test_arquitetura.py`. O teste também confere se cada caminho usado no `model.js` existe no servidor.

As regras de negócio (R01–R08) e os critérios de aceite (C01–C10) continuam os mesmos. Veja `docs/specs/livraria.md`.

## Como rodar

Requer Python 3.10+. O cliente é HTML/CSS/JavaScript puro (módulos ES), sem build.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra http://127.0.0.1:5000/. O servidor entrega o cliente (`cliente/`), e a partir daí o navegador usa só a API. Para usar outra pasta de dados: `LIVRARIA_DADOS=/outra/pasta .venv/bin/python app.py`.

## Testes

```sh
.venv/bin/python -m unittest discover -v
```

- `tests/test_api.py`: C08–C10 pela API REST, sessão, erros 400/401/404 e entrega dos arquivos do cliente.
- `tests/test_modulos.py`: C01–C07, C09, C10 direto na camada de negócios, eventos e saga.
- `tests/test_arquitetura.py`: camadas do cliente (MVC) e do servidor.
- `tests/test_repositorio_txt.py`: camada de dados (formato, persistência e transação).

## Deploy no Azure

O workflow `.github/workflows/main_engsoftwarelab8.yml` publica no Web App `EngSoftwareLab8` a cada push na **`main`**. Esta branch **não** faz deploy sozinha: para publicar o 8.5, faça o merge na `main` (ou rode o workflow manualmente escolhendo esta branch).

As configurações do App Service continuam as mesmas do 8.3:

```sh
az webapp config set -g <grupo> -n <nome-do-app> --startup-file \
  'gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 app:app'
az webapp config appsettings set -g <grupo> -n <nome-do-app> --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true LIVRARIA_DADOS=/home/dados LIVRARIA_SECRET=<uma-chave-aleatoria>
```

Cliente e servidor são publicados juntos no mesmo App Service (o Flask entrega os arquivos de `cliente/`). Como o cliente só usa caminhos `/api`, ele também poderia ir para um Azure Static Web Apps; nesse caso seria preciso configurar CORS e cookies entre domínios no servidor.

O `Dockerfile` continua disponível para App Service com contêiner ou Container Apps.

### Limites conhecidos

- Rode com **1 worker** (e várias threads): a saga de pedidos e o barramento de eventos ficam em memória.
- Cadastro sem senha, pagamento e notificações continuam sendo **simulações** de demonstração.
