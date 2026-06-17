# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## Comandos essenciais

Todos os comandos usam o Python do virtualenv em `venv/Scripts/` (Windows).

```bash
# Servidor de desenvolvimento
venv/Scripts/python manage.py runserver

# Migrações
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate

# Verificação de integridade
venv/Scripts/python manage.py check

# Testes
venv/Scripts/python manage.py test imoveis
venv/Scripts/python manage.py test imoveis.tests.NomeDaClasse  # teste único

# Criar superusuário
venv/Scripts/python manage.py createsuperuser
```

---

## Arquitetura

### Stack
- **Backend:** Django 5.2+ com SQLite (dev)
- **Frontend:** Templates Django (Jinja-style) + CSS estático — sem build system separado
- **Uploads:** `Pillow` para imagens, PDFs salvos em `media/`

### Estrutura de diretórios relevante
- `core/` — configuração Django (`settings.py`, `urls.py`, `wsgi.py`)
- `imoveis/` — único app do projeto (models, views, urls, forms, signals, admin)
- `templates/` — templates globais organizados por módulo (`imoveis/`, `contratos/`, `financeiro/`, `ged/`, `laudos/`, `proprietarios/`, `inquilinos/`)
- `static/css/` — estilos globais
- `media/` — uploads de usuário (fotos, PDFs de contratos/laudos)

### Modelos principais (`imoveis/models.py`)
| Modelo | Papel |
|---|---|
| `Proprietario` | Dono do imóvel |
| `Imovel` | Imóvel com status `vago`/`ocupado` (gerenciado por signal) |
| `FotoImovel` | Fotos vinculadas ao imóvel |
| `Inquilino` | Locatário |
| `Contrato` | Contrato de locação (vincula Imovel ↔ Inquilino) |
| `Fiador` | Fiadores do contrato |
| `LaudoVistoria` | Laudo de vistoria com PDF |
| `Lancamento` | Lançamento financeiro genérico |
| `Entrada` / `Saida` | Receitas e despesas |
| `Notificacao` | Notificações de compliance |
| `RenovacaoContrato` | Renovações de contrato |
| `Distrato` | Distratos (rescisões) |

### Signal crítico (`imoveis/signals.py`)
`Imovel.status` é atualizado automaticamente via `post_save`/`post_delete` em `Contrato`. Sempre que um contrato é criado, alterado ou excluído, o sistema verifica se há contratos `ativo` vinculados ao imóvel e define o status como `ocupado` ou `vago`. O signal é registrado em `imoveis/apps.py`.

### Banco de dados
Controlado por variáveis de ambiente no `.env`:
- `DB_ENGINE=django.db.backends.sqlite3` (padrão dev)
- `DB_ENGINE=django.db.backends.mysql` + `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (prod)

### Autenticação
Usa o sistema de autenticação padrão do Django. Todas as views exigem login (`@login_required`). Rotas: `/login/`, `/logout/`. Após login redireciona para `/` (dashboard).

### Dashboard (BI)
A view do dashboard agrega dados de `Entrada`, `Saida` e `Lancamento` para gerar gráficos de barras e pizza, passados como contexto ao template `dashboard.html`.

---

## Documentação do projeto em `/docs/`

| Arquivo | Conteúdo |
|---|---|
| [01_visao_geral.md](docs/01_visao_geral.md) | Descrição do sistema, público-alvo, stack tecnológica, módulos e requisitos funcionais |
| [03_modelagem_dados.md](docs/03_modelagem_dados.md) | Entidades, campos, tipos, relacionamentos e caminhos de upload |
| [04_regras_de_negocio.md](docs/04_regras_de_negocio.md) | Signals, automações, restrições, campos condicionais, GED, dashboard e acesso |
| [07_design_ui_ux.md](docs/07_design_ui_ux.md) | Paleta, tipografia, layout, componentes, responsividade e bibliotecas frontend |
---
