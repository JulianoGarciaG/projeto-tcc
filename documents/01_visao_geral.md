# 01 — Visão Geral do Projeto
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Identidade da Empresa

Nome: Shelter
logo:

---

## 2. Descrição do Sistema

Sistema interno de acompanhamento, armazenamento de documentação e análise de dados voltado para uma **administradora de bens imóveis**.

A solução é um único website, acessível por funcionários e gestores, integrado a um banco de dados relacional. O foco está na automação de fluxos de trabalho, redução de erros inerentes a processos manuais e priorização da governança de dados.

---

## 3. Objetivo Principal

Solucionar barreiras técnicas relacionadas ao fluxo e armazenamento de dados provenientes de processos manuais, gerando maior eficácia no arquivamento e na análise geral dos dados.

---

## 4. Público-Alvo

| Perfil | Acesso |
|---|---|
| Funcionários | Interface web completa (CRUD, GED) |
| Gestores | Dashboard, BI, filtros e indicadores |
| Vistoriadores | Acesso mobile para consultas e atualizações em campo |
| Auditores | Acesso a documentos centralizados via GED |
| Administradores (`is_staff`) | Painel admin Django |

---

## 5. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Back-end principal | Python + Django |
| Banco de dados | SQLite |
| APIs complementares | FastAPI (serviços assíncronos de alta performance) |
| Arquitetura de API | RESTful (GET, POST, PUT, DELETE) |
| Infraestrutura | Hospedagem em nuvem (acesso remoto seguro) |

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
| **Imóveis** | Cadastro, status, fotos, notificações, entradas e saídas |
| **Proprietários** | Cadastro e identificação dos proprietários |
| **Inquilinos** | Cadastro e documentação dos locatários |
| **Contratos** | Gestão de contratos, fiadores, renovações e distratos |
| **Laudos de Vistoria** | Registro e arquivo de vistorias de entrada, saída e periódicas |
| **Financeiro** | Lançamentos de pagamentos, comprovantes e inadimplência |
| **GED** | Central de documentos digitais (contratos, laudos, comprovantes) |
| **Dashboard / BI** | Indicadores, gráficos e filtros dinâmicos para gestão estratégica |

---

## 8. Requisitos Funcionais Principais

### 8.1 Gestão Eletrônica de Documentos (GED)
- Capturar, armazenar e gerenciar ativos de informação em ambiente digital.
- Eliminar a dependência de pastas físicas, centralizando arquivos como contratos, laudos e comprovantes para acesso imediato por gestores ou auditores.

### 8.2 Operações CRUD e Interface Web
- Interface web funcional, intuitiva e segura para a realização de operações CRUD.
- Aplicação responsiva — gestores e vistoriadores realizam consultas e atualizações diretamente do local do imóvel via dispositivos móveis.
- Alimentação do banco de dados em tempo real.

### 8.3 Dashboard e Business Intelligence (BI)
- Dashboard interativo com indicadores-chave para apoio à tomada de decisões.
- Filtros dinâmicos: período, imóvel, situação, tipo de imóvel e vacância.
- Métricas monitoradas: taxas de vacância, status de pagamentos e índices de inadimplência.
