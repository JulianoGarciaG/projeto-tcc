# 01 — Visão Geral do Projeto
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Identidade da Empresa

**Nome:** Shelter

![Logo Shelter](../static/assets/Shelter_LOGO.svg)

---

## 2. Descrição do Sistema

Sistema interno de acompanhamento, armazenamento de documentação e análise de dados voltado para uma **administradora de bens imóveis**.

A solução é um único website, acessível pela equipe interna da administradora conforme o perfil de cada usuário (ver [Público-Alvo](#4-público-alvo)), integrado a um banco de dados relacional. O foco está na automação de fluxos de trabalho, redução de erros inerentes a processos manuais e priorização da governança de dados.

---

## 3. Objetivo Principal

Solucionar barreiras técnicas relacionadas ao fluxo e armazenamento de dados provenientes de processos manuais, gerando maior eficácia no arquivamento e na análise geral dos dados.

---

## 4. Público-Alvo

Administradora de bens imóveis — equipe interna que opera o sistema via web (inclusive em campo, por dispositivos móveis, para consultas e atualizações no local do imóvel).

Perfis de acesso (Group do Django, atribuídos somente via `/admin/` — ver [docs/03_regras_de_negocio.md §10](03_regras_de_negocio.md)):

| Perfil | Como é identificado | Acesso |
|---|---|---|
| Admin | `is_superuser=True` + `is_staff=True` | Irrestrito, incluindo o painel admin Django (`/admin/`) |
| Owner | Group "Owner" | Todas as telas, exceto `/admin/` |
| Comum | Group "Comum", ou nenhum Group/superuser | Todas as telas, exceto Dashboard, Financeiro e `/admin/` |

---

## 5. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Back-end principal | Python 3.12 + Django 6.0 |
| Banco de dados (produção) | PostgreSQL (Render gerenciado) |
| Banco de dados (desenvolvimento) | SQLite |
| Storage de uploads (produção) | Cloudflare R2 (compatível S3, via django-storages/boto3) |
| Storage de uploads (desenvolvimento) | Disco local (`FileSystemStorage`) |
| Geração de PDF | xhtml2pdf (+ num2words para valores por extenso) |
| Frontend | Templates Django + CSS estático (sem build system); Bootstrap 5.3, Flatpickr, IMask, Chart.js via CDN |
| Infraestrutura | Render (web service + PostgreSQL gerenciado); estáticos via WhiteNoise |

### Dependências principais
```
django>=5.2,<7.0        # Django 6.0 em uso
python-dotenv>=1.0.0
Pillow>=10.0.0
xhtml2pdf>=0.2.16
num2words>=0.5.13

# Produção (Render + Cloudflare R2)
gunicorn>=21.2.0
whitenoise>=6.6.0
psycopg2-binary>=2.9.9
django-storages>=1.14.2
boto3>=1.34.0
```

---

## 6. Arquitetura e Integração

- O sistema utiliza recursos nativos do Django: **ORM**, **sistema de autenticação** e **painel administrativo**, com foco na regra de negócio.
- É uma aplicação Django monolítica de **app único** (`imoveis`), servindo templates renderizados no servidor — sem SPA, sem API externa e sem serviços auxiliares.
- A aplicação garante **integridade, qualidade e segurança dos dados**, alinhando-se às diretrizes de governança de dados.
- O banco de dados relacional (**PostgreSQL** em produção, **SQLite** em desenvolvimento) garante **normalização dos dados** e integridade referencial via constraints e `ForeignKey` (`PROTECT`/`CASCADE`/`SET_NULL`).

---

## 7. Módulos do Sistema

| Módulo | Descrição |
|---|---|
| **Imóveis** | Cadastro, fotos, status (automático) e notificações de órgãos públicos |
| **Proprietários** | Cadastro e identificação dos proprietários |
| **Inquilinos** | Cadastro e documentação dos locatários |
| **Contratos** | Gestão de contratos, fiadores, renovações e distratos |
| **Laudos de Vistoria** | Registro e arquivo de vistorias de entrada e saída |
| **Financeiro** | Lançamentos de pagamentos (`Lancamento`), comprovantes, inadimplência **e indicadores financeiros (KPIs/gráficos) embutidos na própria listagem** |
| **Recibos** | Emissão de recibos de pagamento com geração de PDF |
| **GED** | Central de documentos digitais (contratos, laudos, comprovantes, recibos) |
| **Dashboard Imobiliário** | Indicadores e gráficos de ocupação/vacância dos imóveis, na rota raiz (`/`) |

---

## 8. Requisitos Funcionais Principais

### 8.1 Gestão Eletrônica de Documentos (GED)
- Capturar, armazenar e gerenciar ativos de informação em ambiente digital.
- Eliminar a dependência de pastas físicas, centralizando arquivos como contratos, laudos e comprovantes para acesso imediato pelos perfis Admin e Owner.

### 8.2 Operações CRUD e Interface Web
- Interface web funcional, intuitiva e segura para a realização de operações CRUD.
- Aplicação responsiva — consultas e atualizações podem ser feitas diretamente do local do imóvel via dispositivos móveis.
- Alimentação do banco de dados em tempo real.

### 8.3 Dashboard e Business Intelligence (BI)
- Indicadores-chave divididos em **duas telas** para apoio à tomada de decisões (detalhes em `docs/03_regras_de_negocio.md` §9):
  - **Dashboard Imobiliário** (rota raiz `/`) — ocupação/vacância dos imóveis, com filtros de imóvel/tipo/status.
  - **Indicadores financeiros** — embutidos na própria listagem de Lançamentos (`/financeiro/`), com filtros de imóvel/período de vencimento.
- Métricas monitoradas: taxa de vacância, contratos ativos, ganhos/despesas/saldo do período, ticket médio de aluguel e índice de inadimplência.