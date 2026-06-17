# 03 — Modelagem de Dados
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Visão Geral das Entidades

```
Proprietario
    └── Imovel (PROTECT)
            ├── FotoImovel (CASCADE)
            ├── Contrato (PROTECT)
            │       ├── Fiador (CASCADE)
            │       ├── Lancamento (CASCADE)
            │       ├── LaudoVistoria (SET_NULL)
            │       ├── RenovacaoContrato (CASCADE) [OneToOne]
            │       └── Distrato (CASCADE) [OneToOne]
            │               └── LaudoVistoria (SET_NULL)
            ├── LaudoVistoria (CASCADE)
            ├── Notificacao (CASCADE)
            ├── Saida (CASCADE)
            └── Entrada (CASCADE)

Inquilino
    └── Contrato (PROTECT)
```

---

## 2. Entidades

### 2.1 Proprietario
Dados cadastrais do proprietário do imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `nome` | CharField (200) | ✓ | — |
| `cpf_cnpj` | CharField (20) | ✓ | Único |
| `email` | EmailField | — | — |
| `telefone` | CharField (20) | — | — |
| `endereco` | CharField (300) | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Ordenação:** `nome`

---

### 2.2 Imovel
Dados cadastrais do imóvel. Campos variam conforme `categoria`.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `proprietario` | ForeignKey → Proprietario | ✓ | PROTECT |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `status` | CharField (20) | ✓ | Choices abaixo — atualizado via signal |
| `categoria` | CharField (10) | ✓ | `urbano` / `rural` |
| `endereco` | CharField (300) | ✓ | — |
| `bairro` | CharField (100) | — | — |
| `cidade` | CharField (100) | ✓ | — |
| `valor_aluguel` | DecimalField (10,2) | ✓ | — |
| `area_m2` | DecimalField (8,2) | — | — |
| `descricao` | TextField | — | — |
| `matricula` | CharField (100) | — | Comum a urbano e rural |
| `data_aquisicao` | DateField | — | Comum a urbano e rural |
| `valor_aquisicao` | DecimalField (14,2) | — | Comum a urbano e rural |
| `cadastro_prefeitura` | CharField (100) | — | Somente urbano |
| `planta_projeto` | FileField | — | Somente urbano — `plantas/` |
| `nirf` | CharField (50) | — | Somente rural |
| `incra` | CharField (50) | — | Somente rural |
| `car` | CharField (100) | — | Somente rural |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`apartamento`, `casa`, `comercial`, `terreno`, `galpao`

**Choices — status:**
`ocupado`, `vago`, `manutencao`

**Ordenação:** `endereco`

---

### 2.3 FotoImovel
Fotos vinculadas a um imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `imagem` | ImageField | ✓ | `fotos_imoveis/` |
| `legenda` | CharField (200) | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Ordenação:** `criado_em`

---

### 2.4 Inquilino
Dados cadastrais do locatário.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `nome` | CharField (200) | ✓ | — |
| `cpf` | CharField (14) | ✓ | Único |
| `cnpj` | CharField (18) | — | Para PJ |
| `rg` | CharField (20) | — | — |
| `qualificacao` | CharField (300) | — | Estado civil, profissão, nacionalidade |
| `email` | EmailField | — | — |
| `telefone` | CharField (20) | — | — |
| `profissao` | CharField (100) | — | — |
| `renda_mensal` | DecimalField (10,2) | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Ordenação:** `nome`

---

### 2.5 Contrato
Contrato de locação entre inquilino e imóvel. Campos de documentos variam conforme `tipo_contrato`.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | PROTECT |
| `inquilino` | ForeignKey → Inquilino | ✓ | PROTECT |
| `tipo_contrato` | CharField (2) | ✓ | `PF` / `PJ` |
| `status` | CharField (20) | ✓ | Choices abaixo |
| `data_inicio` | DateField | ✓ | — |
| `data_fim` | DateField | ✓ | — |
| `valor_mensal` | DecimalField (10,2) | ✓ | — |
| `dia_vencimento` | PositiveSmallIntegerField | ✓ | Default: 10 |
| `arquivo` | FileField | — | `contratos/` |
| `comprovante_renda` | FileField | — | `comprovantes_renda/` — somente PF |
| `contrato_social` | FileField | — | `contratos_sociais/` — somente PJ |
| `recibo_chaves` | FileField | — | `contratos/recibo_chaves/` |
| `comprovante_anual` | FileField | — | `contratos/comprovante_anual/` |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — status:**
`ativo`, `encerrado`, `rescindido`

**Ordenação:** `-data_inicio`

---

### 2.6 Fiador
Fiador vinculado a um contrato.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE |
| `nome` | CharField (200) | ✓ | — |
| `qualificacao` | CharField (300) | — | Estado civil, profissão, nacionalidade |
| `rg_cpf` | CharField (20) | ✓ | — |
| `certidao_onus` | FileField | — | `certidoes/` |
| `garantia` | CharField (200) | — | Ex: imóvel próprio, caução |

---

### 2.7 LaudoVistoria
Laudo de vistoria vinculado a um imóvel e opcionalmente a um contrato.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `contrato` | ForeignKey → Contrato | — | SET_NULL |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `data` | DateField | ✓ | — |
| `responsavel` | CharField (200) | ✓ | — |
| `observacoes` | TextField | — | — |
| `arquivo` | FileField | — | `laudos/` |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`entrada`, `saida`, `periodica`

**Ordenação:** `-data`

---

### 2.8 Lancamento
Lançamento financeiro vinculado a um contrato.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `status` | CharField (20) | ✓ | Choices abaixo |
| `valor` | DecimalField (10,2) | ✓ | — |
| `data_vencimento` | DateField | ✓ | — |
| `data_pagamento` | DateField | — | — |
| `comprovante` | FileField | — | `comprovantes/` |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`aluguel`, `condominio`, `iptu`, `manutencao`, `multa`, `outros`

**Choices — status:**
`pago`, `pendente`, `atrasado`

**Ordenação:** `-data_vencimento`

---

### 2.9 Notificacao
Notificação de órgão público vinculada a um imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `titulo` | CharField (200) | ✓ | — |
| `data_recebimento` | DateField | ✓ | — |
| `data_resposta` | DateField | — | — |
| `arquivo` | FileField | — | `notificacoes/` |
| `observacoes` | TextField | — | — |
| `status` | CharField (20) | ✓ | Choices abaixo |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`prefeitura`, `receita_federal`, `bombeiros`, `outro`

**Choices — status:**
`pendente`, `respondida`, `arquivada`

**Ordenação:** `-data_recebimento`

---

### 2.10 RenovacaoContrato
Renovação de contrato. Apenas uma por contrato (OneToOne).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | OneToOneField → Contrato | ✓ | CASCADE |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `data_renovacao` | DateField | ✓ | — |
| `novo_valor_mensal` | DecimalField (10,2) | — | Deixar em branco mantém valor atual |
| `observacoes` | TextField | — | — |

**Choices — tipo:**
`12_12` (12/12 meses), `12_30` (12/30 meses), `12_indeterminado` (12/Indeterminado)

---

### 2.11 Distrato
Distrato de contrato. Apenas um por contrato (OneToOne). Ao salvar, encerra o contrato automaticamente.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | OneToOneField → Contrato | ✓ | CASCADE |
| `tipo` | CharField (10) | ✓ | Choices abaixo |
| `data_distrato` | DateField | ✓ | — |
| `recibo_chaves` | FileField | — | `distratos/recibos/` |
| `laudo_saida` | ForeignKey → LaudoVistoria | — | SET_NULL |
| `observacoes` | TextField | — | — |

**Choices — tipo:**
`amigavel`, `judicial`

---

### 2.12 Saida
Despesas/saídas financeiras vinculadas a um imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `tipo` | CharField (30) | ✓ | Choices abaixo |
| `descricao` | CharField (300) | — | — |
| `valor` | DecimalField (10,2) | ✓ | — |
| `data` | DateField | ✓ | — |
| `pago_por` | CharField (15) | ✓ | `inquilino` / `administradora` |
| `comprovante` | FileField | — | `saidas/` |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`tributos`, `reforma`, `construcao_inicial`, `consumos`, `despesas_juridicas`, `previsao_despesas`

**Ordenação:** `-data`

---

### 2.13 Entrada
Receitas/entradas financeiras vinculadas a um imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `descricao` | CharField (300) | — | — |
| `valor` | DecimalField (10,2) | ✓ | — |
| `data` | DateField | ✓ | — |
| `comprovante` | FileField | — | `entradas/` |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`recibo_imovel`, `recibo_periodo`, `previsao_mes`, `previsao_ano`

**Ordenação:** `-data`

---

## 3. Caminhos de Upload (MEDIA_ROOT)

| Entidade | Campo | Caminho |
|---|---|---|
| Imovel | `planta_projeto` | `plantas/` |
| FotoImovel | `imagem` | `fotos_imoveis/` |
| Contrato | `arquivo` | `contratos/` |
| Contrato | `comprovante_renda` | `comprovantes_renda/` |
| Contrato | `contrato_social` | `contratos_sociais/` |
| Contrato | `recibo_chaves` | `contratos/recibo_chaves/` |
| Contrato | `comprovante_anual` | `contratos/comprovante_anual/` |
| Fiador | `certidao_onus` | `certidoes/` |
| LaudoVistoria | `arquivo` | `laudos/` |
| Lancamento | `comprovante` | `comprovantes/` |
| Notificacao | `arquivo` | `notificacoes/` |
| Distrato | `recibo_chaves` | `distratos/recibos/` |
| Saida | `comprovante` | `saidas/` |
| Entrada | `comprovante` | `entradas/` |
