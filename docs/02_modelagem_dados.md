# 02 — Modelagem de Dados
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Visão Geral das Entidades

```
Proprietario
    └── Imovel (PROTECT)
            ├── FotoImovel (CASCADE)
            ├── Contrato (PROTECT)
            │       ├── Fiador (CASCADE)
            │       ├── DocumentoContrato (CASCADE) [FK, N por contrato — anexos pessoais]
            │       ├── Lancamento (SET_NULL) [contrato opcional, origem do ganho/despesa]
            │       ├── LaudoVistoria (PROTECT) [contrato obrigatório]
            │       ├── Recibo (PROTECT)
            │       ├── RenovacaoContrato (CASCADE) [FK, N por contrato]
            │       └── Distrato (CASCADE) [OneToOne]
            │               └── LaudoVistoria (SET_NULL) [laudo_saida, opcional]
            ├── LaudoVistoria (CASCADE)
            ├── Notificacao (CASCADE)
            ├── Lancamento (PROTECT) [imovel obrigatório]
            └── Recibo (PROTECT)
                    └── Lancamento (CASCADE) [ganho automático, ver sinal recibo_salvo]

Inquilino
    └── Contrato (PROTECT)

ComodoTemplate (catálogo de vistoria, seed na migração 0004)
    └── ItemVistoriaTemplate (CASCADE)

LaudoVistoria
    ├── ItemVistoria (CASCADE) [snapshot do catálogo no momento da vistoria]
    │       └── FotoItemVistoria (CASCADE) [0..N fotos, visível só no detalhe]
    └── TestemunhaLaudo (CASCADE)

User (auth)
    └── NotificacaoUsuario (CASCADE) [histórico append-only de django.contrib.messages]
```

> O módulo financeiro **não possui** mais os models `Entrada`/`Saida` (removidos na Rodada 2) — o único model financeiro é `Lancamento`, indexado por `Imovel` (obrigatório) com `natureza` (`ganho`/`despesa`); `Contrato` é opcional, preenchido quando o lançamento se origina de um contrato/recibo.

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
Contrato de locação entre inquilino e imóvel. Os quatro campos de documento fixos (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) e os anexos pessoais múltiplos (`DocumentoContrato`, ver 2.5.1) são anexados individualmente pela tela de detalhe (ver Regras de Negócio, seção 5).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | PROTECT |
| `inquilino` | ForeignKey → Inquilino | ✓ | PROTECT |
| `tipo_contrato` | CharField (2) | — | Default `PF`; `PF` / `PJ` |
| `finalidade` | CharField (12) | — | Default `residencial`; `residencial` / `comercial` — usada no PDF jurídico (cláusulas VI/preâmbulo) |
| `status` | CharField (20) | — | Default `ativo`; Choices abaixo |
| `data_inicio` | DateField | ✓ | — |
| `data_fim` | DateField | ✓ | — |
| `valor_mensal` | DecimalField (10,2) | ✓ | Valor contratual original; nunca alterado pelo reajuste; sempre exibido no PDF jurídico |
| `valor_vigente` | DecimalField (10,2) | — | Valor de cobrança após reajuste; `valor_cobranca` devolve este quando preenchido, senão `valor_mensal` |
| `data_ultimo_reajuste` | DateField | — | Data do último reajuste (carimbada pela view `contrato_reajuste`); usada para suprimir o aviso de aniversário do ciclo atual — ver [regras §14](03_regras_de_negocio.md#14-indicador-de-atenção-e-reajuste-de-valor) |
| `dia_vencimento` | PositiveSmallIntegerField | — | Default: 10; `MinValueValidator(1)`/`MaxValueValidator(31)` |
| `comprovante_renda` | FileField | — | `comprovantes_renda/` — somente PF; anexado via `contrato_anexar_documento` |
| `contrato_social` | FileField | — | `contratos_sociais/` — somente PJ; anexado via `contrato_anexar_documento` |
| `recibo_chaves` | FileField | — | `contratos/recibo_chaves/`; anexado via `contrato_anexar_documento` |
| `comprovante_anual` | FileField | — | `contratos/comprovante_anual/`; anexado via `contrato_anexar_documento` |
| `documento_gerado` | FileField | — | `contratos/gerados/` — PDF do contrato gerado pelo sistema (botão "Regerar PDF"); cada geração **sobrescreve** o arquivo anterior (sem histórico de versões) |
| `observacoes` | TextField | — | — |
| `local_assinatura` | CharField (200) | — | Cidade da assinatura, usada no PDF jurídico |
| `data_assinatura` | DateField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

> Não possui campo `arquivo` (removido na Rodada 2 — substituído por `documento_gerado`, preenchido apenas pela geração de PDF).

**Choices — status:**
`ativo`, `encerrado`, `rescindido`

**Ordenação:** `-data_inicio`

---

### 2.5.1 DocumentoContrato
Anexo pessoal avulso do contrato — documentação diversa do inquilino/fiador (RG, CPF, comprovantes etc.). Diferente dos quatro campos de documento fixos do `Contrato` (um `FileField` cada), permite **múltiplos arquivos por contrato**: uma linha por arquivo, formatos variados. Anexado (upload múltiplo, input `multiple`) e removido **individualmente** pela tela de detalhe (views `contrato_documento_pessoal_upload` / `contrato_documento_pessoal_delete`) — nunca pelo form de create/edit. Remover uma linha apaga só aquele arquivo (físico + registro), sem afetar os demais.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE, `related_name='documentos_pessoais'` |
| `arquivo` | FileField | ✓ | `contratos/documentos_pessoais/` |
| `nome_original` | CharField (255) | — | Nome do arquivo enviado (rótulo exibido na lista) |
| `criado_em` | DateTimeField | — | Auto now add |

**Ordenação:** `criado_em`, `pk`

---

### 2.6 Fiador
Fiador vinculado a um contrato.

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE |
| `nome` | CharField (200) | ✓ | — |
| `qualificacao` | CharField (300) | — | Estado civil, profissão, nacionalidade |
| `rg_cpf` | CharField (20) | ✓ | Campo legado de texto livre; `validate_rg_cpf` — 11 dígitos numéricos validam como CPF (dígitos verificadores), senão valida formato de RG |
| `rg` | CharField (20) | — | `validate_rg` — RG discreto (usado no PDF jurídico do contrato) |
| `cpf` | CharField (14) | — | `validate_cpf` — CPF discreto (usado no PDF jurídico do contrato) |
| `endereco` | CharField (300) | — | Endereço completo do fiador (qualificação no PDF jurídico) |
| `conjuge_nome` | CharField (200) | — | — |
| `conjuge_rg` | CharField (20) | — | `validate_rg` |
| `conjuge_cpf` | CharField (14) | — | `validate_cpf` |
| `certidao_onus` | FileField | — | `certidoes/` |
| `garantia` | CharField (200) | — | Ex: imóvel próprio, caução |

> `rg_cpf` é o campo legado original (texto único, mantido por compatibilidade); `rg`/`cpf` são campos discretos adicionados para a qualificação completa do fiador no contrato jurídico (`contrato-juridico-completo`) — ambos opcionais, preenchidos conforme o documento do fiador disponível.

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
| `documento_gerado` | FileField | — | `laudos/gerados/` — PDF do laudo gerado pelo sistema; cada geração **sobrescreve** o arquivo anterior (sem histórico de versões) |
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
Único model do módulo financeiro — ganho ou despesa indexado por `Imovel` (o `Contrato` é opcional, preenchido quando o lançamento se origina de um contrato/recibo).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `imovel` | ForeignKey → Imovel | ✓ | PROTECT |
| `contrato` | ForeignKey → Contrato | — | SET_NULL; preenchido quando originado de contrato/recibo |
| `recibo` | ForeignKey → Recibo | — | CASCADE; só nos ganhos criados automaticamente (ver §3, sinal `recibo_salvo`) |
| `natureza` | CharField (10) | ✓ | Choices abaixo |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `status` | CharField (20) | condicional | Só se aplica a `natureza='ganho'`; `null` em despesas (CheckConstraint) |
| `valor` | DecimalField (10,2) | ✓ | — |
| `data_vencimento` | DateField | ✓ | — |
| `data_pagamento` | DateField | — | — |
| `comprovante` | FileField | — | `comprovantes/` |
| `observacoes` | TextField | — | — |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — natureza:**
`ganho`, `despesa`

**Choices — tipo:**
`aluguel`, `condominio`, `iptu`, `manutencao`, `multa`, `outros`

**Choices — status (apenas ganho):**
`pendente`, `efetivado`

**Ordenação:** `-data_vencimento`

**Property `vencido`:** `natureza='ganho' and status='pendente' and data_vencimento < hoje` — calculado em runtime, não gravado (inadimplência do dashboard usa esse critério).

> Os models `Entrada` e `Saida` (vinculados diretamente ao `Imovel`) foram removidos na Rodada 2 e a distinção ganho/despesa foi reintroduzida nesta rodada como o campo `Lancamento.natureza` — não recriar `Entrada`/`Saida` como models separados.

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
Renovação de contrato. **Múltiplas por contrato** (ForeignKey) — o contrato acumula um histórico de renovações. Registro permitido apenas enquanto o contrato está **ativo** (validado na view). O valor monetário não é campo desta entidade: reajuste de valor é tratado por `Contrato.valor_vigente` (feature de reajuste). Ordenação padrão: mais recente primeiro (`-data_renovacao`).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `contrato` | ForeignKey → Contrato | ✓ | CASCADE, `related_name='renovacoes'` |
| `tipo` | CharField (20) | ✓ | Choices abaixo |
| `data_renovacao` | DateField | ✓ | — |
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
| `arquivo` | FileField | — | `recibos/` — PDF do recibo gerado pelo sistema; cada geração **sobrescreve** o arquivo anterior (sem histórico de versões) |
| `criado_em` | DateTimeField | — | Auto now add |

> Não possui campo `proveniente_sitio` (removido na Rodada 2).

**Método:** `somatorio()` — soma das parcelas preenchidas (`valor_aluguel` + `valor_impostos` + `valor_seguros` + `valor_condominio`).

**Ordenação:** `-criado_em`

---

### 2.17 NotificacaoUsuario
Histórico persistido, por usuário, das mensagens que o sistema já emite via `django.contrib.messages` (sucesso de CRUD, geração de PDF, erros, avisos). Espelho **append-only** do texto e nível (tag) da mensagem exibida — sem estado de lida/não lida, sem FK genérica para o objeto de origem. Não confundir com o model de negócio `Notificacao` (avisos de órgãos públicos sobre um imóvel).

| Campo | Tipo | Obrigatório | Observações |
|---|---|---|---|
| `id` | BigAutoField | — | PK automática |
| `usuario` | ForeignKey → User | ✓ | CASCADE; `related_name='notificacoes'` |
| `mensagem` | TextField | ✓ | Texto da mensagem exibida |
| `nivel` | CharField (10) | ✓ | Choices espelhando as tags do Django messages |
| `criado_em` | DateTimeField | — | Auto now add |

**Choices — nivel:**
`success`, `error`, `warning`, `info`

**Ordenação:** `-criado_em`, `-pk`

> Criado exclusivamente pelo storage backend customizado de `django.contrib.messages` (`imoveis/message_storage.py`) — nunca instanciado manualmente em views.

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
| DocumentoContrato | `arquivo` | `contratos/documentos_pessoais/` |
| Fiador | `certidao_onus` | `certidoes/` |
| LaudoVistoria | `arquivo` | `laudos/` |
| LaudoVistoria | `documento_gerado` | `laudos/gerados/` |
| Lancamento | `comprovante` | `comprovantes/` |
| Notificacao | `arquivo` | `notificacoes/` |
| Distrato | `recibo_chaves` | `distratos/recibos/` |
| Recibo | `arquivo` | `recibos/` |

> Todos os `FileField` usam o storage `default` do `STORAGES` (Django 4.2+), plugável via `STORAGE_BACKEND` no `.env` (`filesystem` default; `s3` preparado, mas não ativado). Não há mais versionamento de PDFs gerados: cada geração sobrescreve o arquivo anterior no campo legado (`Contrato.documento_gerado`, `LaudoVistoria.documento_gerado`, `Recibo.arquivo`), tanto no banco quanto no storage físico.
