# Contexto do Projeto: Sistema Integrado de Gestão Imobiliária (GED e BI)

## 1. Visão Geral do Projeto
Este projeto consiste no desenvolvimento de um sistema interno de acompanhamento e armazenamento de documentação e integração, com análise de dados, voltado para uma administradora de bens imóveis. O objetivo principal é solucionar barreiras técnicas relacionadas ao fluxo e armazenamento de dados provenientes de processos manuais, gerando maior eficácia no arquivamento e na análise geral dos dados.

A solução será um website voltado para funcionários e gestores, com integração a um banco de dados. O foco está na automação de fluxos de trabalho, redução de erros inerentes ao trabalho manual e priorização da governança de dados.

---

## 2. Stack Tecnológica
* **Back-end Principal:** Python com framework Django.
* **Banco de Dados:** MySQL (Banco de dados relacional para garantir a integridade das informações e normalização dos dados).
* **APIs e Integração:** FastAPI e arquitetura RESTful (utilizando requisições HTTP como GET, POST, PUT e DELETE) para garantir um fluxo contínuo entre front-end e back-end.
* **Infraestrutura:** Ambiente de hospedagem em nuvem para viabilizar o acesso remoto seguro.

---

## 3. Entidades e Modelagem de Dados
O banco de dados relacional deve ser capaz de armazenar as seguintes informações centrais para operações CRUD (Create, Read, Update, Delete):
* **Imóveis:** Dados cadastrais e status.
* **Inquilinos e Proprietários:** Informações de registro e documentos de identificação.
* **Documentos (GED):** Contratos de locação e laudos de vistoria.
* **Financeiro:** Lançamentos de pagamentos e comprovantes.

---

## 4. Requisitos Funcionais Principais

### 4.1 Gestão Eletrônica de Documentos (GED)
* O sistema deve capturar, armazenar e gerenciar ativos de informação em ambiente digital.
* Deve eliminar a dependência de pastas físicas, centralizando arquivos como contratos, laudos e comprovantes para acesso imediato por gestores ou auditores.

### 4.2 Operações CRUD e Interface Web
* Desenvolver uma interface web funcional, intuitiva e segura para a realização de operações CRUD.
* A aplicação deve ser responsiva, permitindo que gestores e vistoriadores realizem consultas e atualizações (como status de vacância e laudos) diretamente do local do imóvel, via dispositivos móveis.
* A alimentação do banco de dados deve ocorrer em tempo real.

### 4.3 Dashboard e Business Intelligence (BI)
* Construir um dashboard interativo para a visualização de indicadores-chave, auxiliando a gestão estratégica e a tomada de decisões.
* O painel deve conter filtros dinâmicos, incluindo: período, imóvel, situação, tipo de imóvel e vacância.
* Métricas essenciais a serem monitoradas incluem taxas de vacância, status de pagamentos e índices de inadimplência.

---

## 5. Diretrizes de Arquitetura e Integração
* O sistema utilizará recursos nativos do Django, como ORM, sistema de autenticação e painel administrativo, focando a construção na regra de negócio.
* O FastAPI será utilizado para prover serviços adicionais de alta performance e dependências assíncronas caso necessário, integrando-se à base de dados MySQL.
* A aplicação deve garantir que os dados possuam integridade, qualidade e segurança, alinhando-se às diretrizes de governança de dados.