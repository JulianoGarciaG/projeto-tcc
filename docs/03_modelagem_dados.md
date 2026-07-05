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
            │       ├── LaudoVistoria (PROTECT) [contrato obrigatório]
            │       ├── Recibo (PROTECT)
            │       ├── RenovacaoContrato (CASCADE) [OneToOne]
            │       └── Distrato (CASCADE) [OneToOne]
            │               └── LaudoVistoria (SET_NULL) [laudo_saida, opcional]
            ├── LaudoVistoria (CASCADE)
            ├── Notificacao (CASCADE)
            └── Recibo (PROTECT)

Inquilino
    └── Contrato (PROTECT)

ComodoTemplate (catálogo de vistoria, seed na migração 0004)
    └── ItemVistoriaTemplate (CASCADE)

LaudoVistoria
    ├── ItemVistoria (CASCADE) [snapshot do catálogo no momento da vistoria]
    └── TestemunhaLaudo (CASCADE)
```

> O módulo financeiro **não possui** mais os models `Entrada`/`Saida` (removidos na Rodada 2) — o único model financeiro é `Lancamento`, vinculado ao `Contrato` (não diretamente ao `Imovel`).

---

## 2. Entidades

### 2.1 Proprietario
Dados cadastrais do proprietário do imóvel.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `nome` | CharField (200) | ✓ | — |
| `cpf_cnpj` | CharField (20) | ✓ | Único; `validate_cpf_cnpj` |
| `email` | EmailField | — | — |
| `telefone` | CharField (20) | — | `validate_telefone` — 10 ou 11 dígitos (DDD + fixo/celular), com ou sem máscara |
| `criado_em` | DateTimeField | — | Auto now add |

> Não possui campo `endereco` (removido na Rodada 2 — endereço do proprietário não é modelado).

**Ordenação:** `nome`

---

### 2.2 Imovel
Dados cadastrais do imóvel. Campos exclusivos variam conforme `categoria`. **Não possui** campo de valor de aluguel — o valor vigente é o `valor_mensal` do contrato ativo (`Imovel.contratos.filter(status='ativo')`).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `proprietario` | ForeignKey → Proprietario | ✓ | PROTECT |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `status` | CharField (20) | ✓ | Default `vago`; Choices abaixo — atualizado via signal (exceto `manutencao`) |
| `categoria` | CharField (10) | — | Default `urbano`; `urbano` / `rural` |
| `endereco` | CharField (300) | ✓ | — |
| `numero` | CharField (20) | — | Número do imóvel |
| `complemento` | CharField (100) | — | Apto, bloco, sala etc. |
| `bairro` | CharField (100) | — | — |
| `cidade` | CharField (100) | — | Default `''` |
| `area_m2` | DecimalField (8,2) | — | — |
| `descricao` | TextField | — | — |
| `matricula` | CharField (100) | — | Comum a urbano e rural |
| `data_aquisicao` | DateField | — | Comum a urbano e rural |
| `valor_aquisicao` | DecimalField (14,2) | — | Comum a urbano e rural |
| `cadastro_prefeitura` | CharField (100) | — | Somente urbano |
| `planta_projeto` | FileField | — | Somente urbano — `plantas/`; exibida (preview de imagem ou link) na tela de detalhe do imóvel |
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
| `cpf` | CharField (14) | ✓ | Único; `validate_cpf` |
| `cnpj` | CharField (18) | — | Para PJ; `validate_cnpj` |
| `email` | EmailField | — | — |
| `telefone` | CharField (20) | — | `validate_telefone` — 10 ou 11 dígitos (DDD + fixo/celular), com ou sem máscara |
| `rg` | CharField (20) | — | `validate_rg` |
| `qualificacao` | CharField (300) | — | Estado civil, profissão, nacionalidade |
| `profissao` | CharField (100) | — | — |
| `faixa_renda` | CharField (20) | — | Choices abaixo — faixas em **R$**, não mais em salários mínimos |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — faixa_renda:**
`ate_2k` (< R$ 2k), `2_4k` (R$ 2k–3,9k), `4_7k` (R$ 4k–6,9k), `7_10k` (R$ 7k–9,9k), `10_16k` (R$ 10k–15,9k), `acima_16k` (R$ 16k+)

> Não possui campo `renda_mensal` (nunca existiu como `DecimalField`; a renda é categorizada por `faixa_renda`).

**Ordenação:** `nome`

---

### 2.5 Contrato
Contrato de locação entre inquilino e imóvel. Campos de documentos são anexados individualmente pela tela de detalhe (ver Regras de Negócio, seção 5).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | PROTECT |
| `inquilino` | ForeignKey → Inquilino | ✓ | PROTECT |
| `tipo_contrato` | CharField (2) | — | Default `PF`; `PF` / `PJ` |
| `status` | CharField (20) | — | Default `ativo`; Choices abaixo |
| `data_inicio` | DateField | ✓ | — |
| `data_fim` | DateField | ✓ | — |
| `valor_mensal` | DecimalField (10,2) | ✓ | Valor de aluguel vigente do imóvel |
| `dia_vencimento` | PositiveSmallIntegerField | — | Default: 10; `MinValueValidator(1)`/`MaxValueValidator(31)` |
| `comprovante_renda` | FileField | — | `comprovantes_renda/` — somente PF; anexado via `contrato_anexar_documento` |
| `contrato_social` | FileField | — | `contratos_sociais/` — somente PJ; anexado via `contrato_anexar_documento` |
| `recibo_chaves` | FileField | — | `contratos/recibo_chaves/`; anexado via `contrato_anexar_documento` |
| `comprovante_anual` | FileField | — | `contratos/comprovante_anual/`; anexado via `contrato_anexar_documento` |
| `documento_gerado` | FileField | — | `contratos/gerados/` — PDF do contrato gerado pelo sistema (botão "Regerar PDF") |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

> Não possui campo `arquivo` (removido na Rodada 2 — substituído por `documento_gerado`, preenchido apenas pela geração de PDF).

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
| `rg_cpf` | CharField (20) | ✓ | `validate_rg_cpf` — 11 dígitos numéricos validam como CPF (dígitos verificadores), senão valida formato de RG |
| `certidao_onus` | FileField | — | `certidoes/` |
| `garantia` | CharField (200) | — | Ex: imóvel próprio, caução |

---

### 2.7 LaudoVistoria
Laudo de vistoria vinculado a um imóvel e a um contrato (ambos obrigatórios).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | CASCADE |
| `contrato` | ForeignKey → Contrato | ✓ | **PROTECT** — não é mais opcional; o select de contrato no formulário é dependente do imóvel escolhido (endpoint `contratos_por_imovel_json`) |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `data` | DateField | ✓ | — |
| `responsavel` | CharField (200) | ✓ | — |
| `observacoes` | TextField | — | — |
| `local_assinatura` | CharField (200) | — | Cidade da assinatura, usada no PDF |
| `data_assinatura` | DateField | — | — |
| `arquivo` | FileField | — | `laudos/` — anexo do laudo assinado (upload só na tela de detalhe, via `laudo_anexar_arquivo`) |
| `documento_gerado` | FileField | — | `laudos/gerados/` — PDF do laudo gerado pelo sistema |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`entrada`, `saida`

> O tipo `periodica` foi removido na Rodada 2. Não recriar.

**Ordenação:** `-data`

**Métodos:** `resumo_vistoria()` (contagem de itens por estado — calculado, nunca digitado), `locador_nome()`, `locatario_nome()`.

---

### 2.8 ComodoTemplate
Catálogo configurável de cômodos padrão da vistoria (editável no admin; seed de 5 cômodos na migração 0004).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `nome` | CharField (100) | ✓ | — |
| `ordem` | PositiveSmallIntegerField | — | Default 0 |

**Ordenação:** `ordem`, `nome`

---

### 2.9 ItemVistoriaTemplate
Item avaliável de um cômodo do catálogo (seed de 32 itens na migração 0004).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `comodo` | ForeignKey → ComodoTemplate | ✓ | CASCADE |
| `nome` | CharField (150) | ✓ | — |
| `ordem` | PositiveSmallIntegerField | — | Default 0 |

**Ordenação:** `comodo__ordem`, `ordem`, `nome`

---

### 2.10 ItemVistoria
Item avaliado em um laudo — snapshot do catálogo na data da vistoria (não referencia `ItemVistoriaTemplate` por FK).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `laudo` | ForeignKey → LaudoVistoria | ✓ | CASCADE |
| `comodo` | CharField (100) | ✓ | — |
| `item` | CharField (150) | ✓ | — |
| `estado` | CharField (10) | ✓ | Choices abaixo |
| `observacao` | CharField (300) | — | — |
| `ordem` | PositiveSmallIntegerField | — | Default 0 |

**Choices — estado:**
`bom`, `regular`, `ruim`

**Ordenação:** `ordem`, `pk`

---

### 2.11 TestemunhaLaudo
Testemunha do laudo de vistoria.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `laudo` | ForeignKey → LaudoVistoria | ✓ | CASCADE |
| `nome` | CharField (200) | ✓ | — |
| `cpf` | CharField (14) | — | `validate_cpf` |

---

### 2.12 Lancamento
Único model do módulo financeiro — lançamento vinculado a um contrato (não diretamente ao imóvel).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `status` | CharField (20) | — | Default `pendente`; Choices abaixo |
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

> Os models `Entrada` e `Saida` (vinculados diretamente ao `Imovel`) foram **removidos na Rodada 2**. Não recriar.

---

### 2.13 Notificacao
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
| `status` | CharField (20) | — | Default `pendente`; Choices abaixo |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`prefeitura`, `receita_federal`, `bombeiros`, `outro`

**Choices — status:**
`pendente`, `respondida`, `arquivada`

**Ordenação:** `-data_recebimento`

---

### 2.14 RenovacaoContrato
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

### 2.15 Distrato
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

### 2.16 Recibo
Recibo de pagamento. `imovel`/`contrato` obrigatórios (PROTECT); demais campos opcionais — no PDF só aparecem os campos preenchidos.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | PROTECT |
| `contrato` | ForeignKey → Contrato | ✓ | PROTECT |
| `parcela_atual` | PositiveSmallIntegerField | — | — |
| `parcela_total` | PositiveSmallIntegerField | — | — |
| `valor_aluguel` | DecimalField (10,2) | — | Parcela que compõe `quantia` |
| `valor_impostos` | DecimalField (10,2) | — | Parcela que compõe `quantia` |
| `valor_seguros` | DecimalField (10,2) | — | Parcela que compõe `quantia` |
| `valor_condominio` | DecimalField (10,2) | — | Parcela que compõe `quantia` |
| `quem_pagou` | CharField (200) | — | — |
| `periodo_inicio` | DateField | — | Início do período coberto pelo recibo |
| `periodo_fim` | DateField | — | Fim do período coberto pelo recibo |
| `vencido_em` | DateField | — | — |
| `quantia` | DecimalField (10,2) | — | Valor total recebido |
| `assinante_nome` | CharField (200) | — | — |
| `assinante_cpf` | CharField (14) | — | `validate_cpf` |
| `data_assinatura` | DateField | — | — |
| `arquivo` | FileField | — | `recibos/` — PDF do recibo gerado pelo sistema |
| `criado_em` | DateTimeField | — | Auto now add |

> Não possui campo `proveniente_sitio` (removido na Rodada 2).

**Método:** `somatorio()` — soma das parcelas preenchidas (`valor_aluguel` + `valor_impostos` + `valor_seguros` + `valor_condominio`).

**Ordenação:** `-criado_em`

---

## 3. Caminhos de Upload (MEDIA_ROOT)

| Entidade | Campo | Caminho |
|---|---|---|
| Imovel | `planta_projeto` | `plantas/` |
| FotoImovel | `imagem` | `fotos_imoveis/` |
| Contrato | `comprovante_renda` | `comprovantes_renda/` |
| Contrato | `contrato_social` | `contratos_sociais/` |
| Contrato | `recibo_chaves` | `contratos/recibo_chaves/` |
| Contrato | `comprovante_anual` | `contratos/comprovante_anual/` |
| Contrato | `documento_gerado` | `contratos/gerados/` |
| Fiador | `certidao_onus` | `certidoes/` |
| LaudoVistoria | `arquivo` | `laudos/` |
| LaudoVistoria | `documento_gerado` | `laudos/gerados/` |
| Lancamento | `comprovante` | `comprovantes/` |
| Notificacao | `arquivo` | `notificacoes/` |
| Distrato | `recibo_chaves` | `distratos/recibos/` |
| Recibo | `arquivo` | `recibos/` |
