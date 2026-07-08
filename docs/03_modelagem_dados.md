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
    │       └── FotoItemVistoria (CASCADE) [0..N fotos, visível só no detalhe]
    └── TestemunhaLaudo (CASCADE)

DocumentoGerado (GED versionado — 1 registro imutável por geração de PDF)
    ├── Contrato (CASCADE) [uma das 3 FKs preenchida]
    ├── LaudoVistoria (CASCADE)
    └── Recibo (CASCADE)
```

> O módulo financeiro **não possui** mais os models `Entrada`/`Saida` (removidos na Rodada 2) — o único model financeiro é `Lancamento`, vinculado ao `Contrato` (não diretamente ao `Imovel`).

### Camada de identidade (`imoveis/identidade.py`)

`Imovel`, `Contrato`, `LaudoVistoria` e `Recibo` herdam de `IdentificavelMixin`, que expõe atributos **derivados em runtime** (não persistidos, sem migration):

- `codigo` — código de negócio `{PREFIXO}-{pk:04d}` (`IMV`/`CTR`/`LAU`/`REC`); com `pk=None` retorna `{PREFIXO}-????`.
- `rotulo_curto` / `rotulo_longo` — rótulos legíveis para selects e templates (cada model implementa os seus). Nas telas: listas e tabelas do GED exibem `codigo` (coluna/texto secundário, sem remover o nome/endereço já mostrado); os cabeçalhos de detalhe de Contrato/Recibo/Laudo usam `codigo` e o `<title>` do detalhe de Imóvel usa `rotulo_longo`. A tabela de comprovantes (GED) mostra o `codigo` do contrato de origem, pois `Lancamento` não herda o mixin.

O módulo também fornece `nome_arquivo(instance, versao=None)` (nome determinístico do PDF, via `slugify`) e `mes_ano_abreviado(data)`. Os `__str__` dos models permanecem inalterados — a camada é **aditiva**.

Cobertura em `imoveis/tests.py`: `IdentidadeCodigoTests` (`codigo` das 4 entidades + placeholder sem pk), `IdentidadeRotulosTests` (`rotulo_curto`/`rotulo_longo`), `NomeArquivoTests` (função pura: sem acentos, sufixo `_v{n}`, truncamento) e `LabelSelectTests` (selects exibindo `rotulo_curto`); `GeracaoPdfViewTests` confere o `codigo` e o incremento de versão (`_v1`→`_v2`) no `Content-Disposition`.

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

### 2.10a FotoItemVistoria
Foto anexada a um `ItemVistoria` (0..N). Visível apenas no detalhe do laudo — nunca no PDF nem na central GED.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `item` | ForeignKey → ItemVistoria | ✓ | CASCADE, `related_name='fotos'` |
| `imagem` | ImageField | ✓ | Upload em `itens_vistoria/{item_id}/{filename}` |
| `criado_em` | DateTimeField | — | `auto_now_add` |

**Ordenação:** `criado_em`

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

### 2.17 DocumentoGerado
Versão **imutável** de um PDF gerado pelo sistema (GED versionado). Um registro por geração de PDF — nunca atualizado após criado. O "documento atual" de uma origem é a versão de maior `numero_versao`. Introduzido na Rodada 4 (migração 0009; migração 0010 registra retroativamente os PDFs já existentes como versão 1).

A origem é modelada com **três FKs explícitas** (uma por tipo) + campo `tipo`, em vez de `GenericForeignKey`: o conjunto de origens é fixo (Contrato, Laudo, Recibo), permite `select_related` e constraints reais no banco.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `tipo` | CharField (10) | ✓ | Choices abaixo — identifica a origem |
| `contrato` | ForeignKey → Contrato | — | CASCADE; `related_name='documentos_gerados'` |
| `laudo` | ForeignKey → LaudoVistoria | — | CASCADE; `related_name='documentos_gerados'` |
| `recibo` | ForeignKey → Recibo | — | CASCADE; `related_name='documentos_gerados'` |
| `numero_versao` | PositiveIntegerField | ✓ | Sequencial **por origem** (começa em 1) |
| `arquivo` | FileField | ✓ | `upload_to` determinístico — ver abaixo |
| `sha256` | CharField (64) | ✓ | Hash SHA-256 do arquivo (vazio se ilegível na migração retroativa) |
| `gerado_por` | ForeignKey → User | — | SET_NULL; autor da geração; `related_name='documentos_gerados'` |
| `gerado_em` | DateTimeField | — | Auto now add |

**Choices — tipo:**
`contrato`, `laudo`, `recibo`

**`upload_to` (`documento_gerado_upload_to`):** `ged/{tipo}/{origem_pk}/v{numero_versao}/{filename}` — caminho determinístico que independe de qualquer campo além de tipo, pk da origem e versão (vira a key do objeto quando o storage for trocado para S3).

**Properties:**
- `origem` — retorna o registro de negócio que originou o documento (`contrato or laudo or recibo`).
- `origem_pk` — pk da origem.

**Constraints (`Meta`):**
- `CheckConstraint` `documentogerado_origem_unica` — exatamente **uma** das três FKs preenchida.
- `UniqueConstraint` `documentogerado_versao_unica_{contrato,laudo,recibo}` — `numero_versao` único por origem (condicional à FK correspondente).

**Imutabilidade:** o `save()` levanta `ValueError` se o registro não estiver sendo criado (`not self._state.adding`) — só permite inserção, nunca update. Para "atualizar" um documento, gera-se uma nova versão.

**Ordenação:** `-gerado_em`, `-pk`

> Os campos legados `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado` e `Recibo.arquivo` são **mantidos**, mas deixam de ser fonte de verdade: passam a ser espelhos automáticos da última versão, sincronizados por `imoveis.pdf.gerar_e_anexar()`. Ver Regras de Negócio, seção 14.

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
| DocumentoGerado | `arquivo` | `ged/{tipo}/{origem_pk}/v{numero_versao}/` |

> Todos os `FileField` usam o storage `default` do `STORAGES` (Django 4.2+), plugável via `STORAGE_BACKEND` no `.env` (`filesystem` default; `s3` preparado, mas não ativado — ver Regras de Negócio, seção 14).
