<div align="center">
  <img src="static/assets/Shelter_LOGO.svg" alt="Shelter" width="220">

  # Shelter — Sistema Integrado de Gestão Imobiliária

  **GED · CRUD · Business Intelligence** para administradoras de bens imóveis.

  ![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-prod-4169E1?logo=postgresql&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-dev-003B57?logo=sqlite&logoColor=white)
  ![License](https://img.shields.io/badge/uso-acadêmico%20(TCC)-lightgrey)
</div>

---

## Sobre o projeto

O **Shelter** é um sistema web interno para uma **administradora de bens imóveis**. Ele centraliza o
acompanhamento, o armazenamento de documentação (**GED — Gestão Eletrônica de Documentos**) e a
análise de dados (**BI**) que hoje vivem em pastas físicas e planilhas manuais.

O objetivo é reduzir erros de processos manuais, dar acesso imediato aos documentos e apoiar a
tomada de decisão com indicadores em tempo real — tudo em uma aplicação responsiva, utilizável
inclusive em campo (celular/tablet, no local do imóvel).

> Projeto desenvolvido como **Trabalho de Conclusão de Curso (TCC)**.

---

## Principais funcionalidades

| Módulo | O que faz |
|---|---|
| **Imóveis** | Cadastro, fotos, status `vago`/`ocupado` (automático) e notificações de órgãos públicos (IPTU, DMAE/DME etc.) |
| **Proprietários** | Cadastro e identificação dos proprietários |
| **Inquilinos** | Cadastro, documentação e faixa de renda dos locatários |
| **Contratos** | Contratos de locação, fiadores, reajuste, renovação, distrato e geração de PDF jurídico |
| **Laudos de Vistoria** | Checklist de vistoria (entrada/saída) com catálogo de cômodos e itens, testemunhas e PDF |
| **Recibos** | Emissão de recibos de pagamento por período, com valor por extenso e PDF |
| **Financeiro** | Lançamentos de entradas/saídas, comprovantes e **indicadores (KPIs + gráficos)** embutidos na listagem |
| **GED** | Central de documentos digitais (contratos, laudos, comprovantes, recibos) |
| **Dashboard Imobiliário** | Ocupação/vacância dos imóveis com filtros, em gráficos Chart.js |

---

## Stack

- **Backend:** Django 6.0 (ORM, auth e admin nativos)
- **Banco:** SQLite (desenvolvimento) · PostgreSQL (produção, Render)
- **Frontend:** Templates Django + CSS estático — **sem build system**. Libs via CDN: Bootstrap 5.3,
  Bootstrap Icons, Flatpickr (datas dd/mm/yyyy), IMask (máscaras), Chart.js (gráficos).
- **PDF:** `xhtml2pdf` renderizando templates HTML (+ `num2words` para valores por extenso)
- **Uploads:** `Pillow`; storage plugável via `STORAGES` — disco local (dev) ou Cloudflare R2 / S3 (prod)
- **Deploy:** Render (web service + PostgreSQL gerenciado), estáticos via WhiteNoise

---

## Como rodar localmente

> No Windows, todos os comandos usam o Python do virtualenv em `venv/Scripts/`.
> Em Linux/macOS, ative o venv e use `python` diretamente.

### 1. Clonar e criar o ambiente

```bash
git clone <url-do-repositorio>
cd projeto-tcc

python -m venv venv
venv/Scripts/pip install -r requirements.txt      # Windows
# source venv/bin/activate && pip install -r requirements.txt   # Linux/macOS
```

### 2. Configurar variáveis de ambiente

Copie o exemplo e ajuste conforme necessário:

```bash
cp .env.example .env
```

Para **desenvolvimento local**, o mínimo é definir uma `SECRET_KEY` e deixar `DB_ENGINE` e
`STORAGE_BACKEND` **em branco** (usa SQLite + disco local automaticamente):

```env
SECRET_KEY=uma-chave-secreta-qualquer
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 3. Migrar o banco e criar um superusuário

```bash
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py createsuperuser
```

> O repositório já inclui um `db.sqlite3` versionado com dados de exemplo para o time do TCC.
> Ainda assim, rode `migrate` para garantir que o schema está atualizado.

### 4. Subir o servidor

```bash
venv/Scripts/python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**. O login redireciona para a landing (`/`), com atalhos de cadastro
rápido. O painel admin do Django fica em `/admin/`.

---

## Comandos úteis

```bash
venv/Scripts/python manage.py runserver          # servidor de desenvolvimento
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py check              # verifica integridade do projeto
venv/Scripts/python manage.py test imoveis       # suíte de testes completa
venv/Scripts/python manage.py test imoveis.tests.NomeDaClasse   # teste único
venv/Scripts/python manage.py createsuperuser
```

---

## Perfis de acesso

Grupos do Django atribuídos **somente via `/admin/`**:

| Perfil | Como é identificado | Acesso |
|---|---|---|
| **Admin** | `is_superuser=True` + `is_staff=True` | Irrestrito, incluindo `/admin/` |
| **Owner** | Group "Owner" | Todas as telas, exceto `/admin/` |
| **Comum** | Group "Comum" (ou nenhum group) | Todas as telas, exceto Dashboard, Financeiro e `/admin/` |

Todas as views exigem login (`@login_required`).

---

## Estrutura do projeto

```
projeto-tcc/
├── core/                 # Configuração Django (settings, urls, wsgi)
├── imoveis/              # App único: models, views, urls, forms, validators, signals, admin, pdf
│   └── migrations/       # 25 migrações (inclui seed do catálogo de vistoria)
├── templates/            # Templates por módulo + documentos/ (PDFs) + base.html/login.html
├── static/
│   ├── css/shelter.css   # Estilo global (dark mode incluso) — único CSS
│   ├── js/               # masks.js, theme.js, imovel-view-toggle.js
│   └── assets/           # Logo e imagens
├── media/                # Uploads (fotos, PDFs gerados/anexados) — não versionado
├── docs/                 # Documentação viva (visão, modelagem, regras, UI/UX)
├── planner-docs/         # Planos por rodada de entrega
├── requirements.txt
├── Procfile · build.sh · runtime.txt   # Deploy (Render)
└── CLAUDE.md             # Guia de convenções do repositório
```

### Entidades principais (`imoveis/models.py`)

`Proprietario`, `Inquilino`, `Fiador`, `Imovel`, `FotoImovel`, `Contrato`, `DocumentoContrato`,
`LaudoVistoria`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`,
`Recibo`, `Lancamento`, `Notificacao`, `RenovacaoContrato`, `Distrato`.

**Detalhes importantes:**

- O **status do imóvel** (`vago`/`ocupado`) é recalculado por *signal* a partir dos contratos ativos — não é editado à mão.
- O **valor do aluguel** vem do contrato ativo, não do imóvel.
- **PDFs nunca são gerados ao salvar** — só pelas rotas `*_gerar_pdf`. Cada geração sobrescreve a versão anterior (sem histórico).
- **Financeiro** usa apenas o modelo `Lancamento`.

---

## Configuração de ambiente (`.env`)

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django (obrigatória) |
| `DEBUG` | `True` em dev, `False` em produção |
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` | Hosts/origens permitidos (separados por vírgula) |
| `DB_ENGINE` | Em branco → SQLite. `django.db.backends.postgresql` → Postgres (requer `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`) |
| `STORAGE_BACKEND` | Em branco → disco local. `s3` → Cloudflare R2 (requer credenciais `AWS_*`) |

Veja `.env.example` para o conjunto completo.

---

## Deploy (Render)

- **`build.sh`** — instala dependências e roda `collectstatic`.
- **`Procfile`** — `release:` roda `migrate`; `web:` sobe o `gunicorn`.
- **`runtime.txt`** — fixa o Python em `3.12.7`.
- Estáticos servidos por **WhiteNoise**; uploads no **Cloudflare R2** (S3-compatível).
- Variáveis de ambiente configuradas no painel do serviço (não em arquivo).

---

## Documentação

Referência viva do sistema em [`/docs`](docs/):

| Arquivo | Conteúdo |
|---|---|
| [01_visao_geral.md](docs/01_visao_geral.md) | Sistema, público-alvo, stack, módulos, requisitos funcionais |
| [02_modelagem_dados.md](docs/02_modelagem_dados.md) | Entidades, campos, relacionamentos, caminhos de upload |
| [03_regras_de_negocio.md](docs/03_regras_de_negocio.md) | Signals, automações, restrições, dashboard, acesso |
| [04_design_ui_ux.md](docs/04_design_ui_ux.md) | Paleta/tokens, tipografia, layout, componentes, dark mode, PDFs |
| [historico_entregas.md](docs/historico_entregas.md) | Histórico e o "porquê" de cada rodada de entrega |

Convenções de código e armadilhas do repositório estão em [`CLAUDE.md`](CLAUDE.md).

---

<div align="center">
  <sub>Projeto acadêmico (TCC) — Sistema Integrado de Gestão Imobiliária "Shelter".</sub>
</div>
