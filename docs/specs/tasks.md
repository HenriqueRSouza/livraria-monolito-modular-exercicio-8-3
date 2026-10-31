# Tarefas derivadas de livraria.md: Exercícios 8.3 (Monólito Modular) e 8.5 (Cliente-Servidor)

Marcar somente após verificar a tarefa. T01–T17 foram concluídas nos exercícios 6 e 7.4 e são revalidadas na nova arquitetura.

- [x] T18 Atualizar a especificação com a arquitetura de monólito modular derivada do diagrama 8.2.
- [x] T19 Criar o núcleo compartilhado (erro, texto, barramento de eventos, repositório TXT genérico com trava entre processos).
- [x] T20 Separar os módulos catalogo, busca, usuarios, estoque, pedidos, pagamentos e notificacoes, cada um com api/dominio/dados e arquivo próprio (C01–C07, C09, C10).
- [x] T21 Substituir chamadas diretas por eventos onde há reação entre módulos; ligar tudo em `aplicacao.py`.
- [x] T22 Implementar a saga de reserva/compra com compensação de estoque.
- [x] T23 Criar o gateway/BFF (telas + `/health` + `/api/livros`) mantendo as URLs do 7.4 (C08).
- [x] T24 Testes de arquitetura: fronteiras entre módulos e um arquivo de dados por módulo.
- [x] T25 Preparar o deploy no Azure (gunicorn, Dockerfile, workflow do GitHub Actions) e documentar no README.

## Exercício 8.5 (Cliente-Servidor)

- [x] T26 Atualizar a especificação com a arquitetura Cliente-Servidor do diagrama (cliente MVC, servidor Aplicação/Routes/Negócios/Dados).
- [x] T27 Trocar as telas geradas no servidor por uma API REST em JSON (`/api`), com erros 400/401/404 e sessão por cookie.
- [x] T28 Criar o cliente JavaScript separado em Model (estado + HTTP), View (telas) e Controller (eventos/ações).
- [x] T29 Testar a API (C08–C10), as camadas do cliente e do servidor, e o fluxo completo do cliente contra o servidor.
