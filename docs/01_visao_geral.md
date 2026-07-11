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
| Back-end principal | Python + Django |
| Banco de dados (produção) | PostgreSQL |
| Banco de dados (desenvolvimento) | SQLite |
| Storage de uploads (produção) | Cloudflare R2 (compatível S3, via django-storages) |
| APIs complementares | FastAPI (serviços assíncronos de alta performance) |
| Arquitetura de API | RESTful (GET, POST, PUT, DELETE) |
| Infraestrutura | Render (web service + PostgreSQL gerenciado) |

### Dependências principais
```
django>=5.2,<7.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

---

## 6. Arquitetura e Integração

- O sistema utiliza recursos nativos do Django: **ORM**, **sistema de autenticação** e **painel administrativo**, com foco na regra de negócio.
- O **FastAPI** é utilizado para prover serviços adicionais de alta performance e dependências assíncronas quando necessário, integrando-se à base de dados MySQL.
- A aplicação garante **integridade, qualidade e segurança dos dados**, alinhando-se às diretrizes de governança de dados.
- O banco de dados relacional MySQL garante **normalização dos dados** e integridade referencial.

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