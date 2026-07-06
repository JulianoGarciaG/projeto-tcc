# 04 — Regras de Negócio
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Status do Imóvel (Automático via Signal)

O status do imóvel é **gerenciado automaticamente** pelo sistema, nunca manualmente pelo usuário.

**Lógica:**
- Se o imóvel possui **ao menos um contrato com `status = 'ativo'`** → `status = 'ocupado'`
- Se o imóvel **não possui contratos ativos** → `status = 'vago'`

**Gatilhos:**
- `post_save` no modelo `Contrato` → atualiza o imóvel vinculado
- `post_delete` no modelo `Contrato` → atualiza o imóvel vinculado

**Exceção:**
- O status `'manutencao'` não é gerenciado por signal — deve ser definido manualmente pelo usuário.

---

## 2. Distrato — Encerramento Automático do Contrato

Ao salvar um `Distrato`, o sistema **encerra automaticamente o contrato vinculado**.

**Lógica (método `save` do modelo `Distrato`):**
```
distrato.save() → contrato.status = 'encerrado' → contrato.save()
```

**Consequência:** após o distrato, o signal de status do imóvel é acionado e o imóvel passa para `'vago'` (se não houver outro contrato ativo).

---

## 3. Unicidade de Renovação e Distrato

| Entidade | Regra |
|---|---|
| `RenovacaoContrato` | Apenas **uma** renovação por contrato (OneToOneField) |
| `Distrato` | Apenas **um** distrato por contrato (OneToOneField) |

**Comportamento na view:**
- Se o contrato já possui renovação → exibe aviso e redireciona para o detalhe do contrato, sem criar nova.
- Se o contrato já possui distrato → exibe aviso e redireciona para o detalhe do contrato, sem criar novo.

---

## 4. Campos Condicionais por Categoria do Imóvel

Os campos do imóvel variam conforme a `categoria`:

| Categoria | Campos exclusivos |
|---|---|
| `urbano` | `cadastro_prefeitura`, `planta_projeto` |
| `rural` | `nirf`, `incra`, `car` |

**Comportamento na interface:**
- O formulário exibe/oculta os campos dinamicamente via JavaScript conforme a categoria selecionada.
- Campos da categoria não selecionada ficam ocultos e não devem ser preenchidos.

---

## 5. Campos Condicionais por Tipo de Contrato

Os documentos do contrato variam conforme o `tipo_contrato`:

| Tipo | Campo exclusivo |
|---|---|
| `PF` (Pessoa Física) | `comprovante_renda` |
| `PJ` (Pessoa Jurídica) | `contrato_social` |

**Comportamento na interface:**
- Esses campos (e `recibo_chaves`, `comprovante_anual`) **não fazem parte** do formulário de criação/edição de contrato (`ContratoForm`) — são anexados individualmente na tela de detalhe do contrato via `contrato_anexar_documento` (mesmo padrão do anexo de laudo assinado).

---

## 6. Laudo de Vistoria Vinculado ao Distrato

- O `Distrato` pode referenciar um `LaudoVistoria` do tipo `saida` como laudo de saída.
- O vínculo é **opcional** (`null=True`, `blank=True`).
- Na view de distrato, o queryset de laudos é filtrado para exibir **somente os laudos do imóvel vinculado ao contrato**.

---

## 7. Proteção Contra Exclusão de Registros Vinculados

| Entidade protegida | Protege contra exclusão de |
|---|---|
| `Proprietario` | Não pode ser excluído se possui imóveis (`PROTECT`) |
| `Imovel` | Não pode ser excluído se possui contratos ou recibos (`PROTECT`) |
| `Inquilino` | Não pode ser excluído se possui contratos (`PROTECT`) |
| `Contrato` | Não pode ser excluído se possui laudos de vistoria ou recibos vinculados (`PROTECT`); a view `contrato_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |

---

## 8. GED — Gestão Eletrônica de Documentos

- Todos os documentos do sistema são armazenados digitalmente, eliminando a dependência de pastas físicas.
- A central GED (`/documentos/`) agrega os documentos agrupados por tipo (view `documentos` em `imoveis/views.py`). Há duas naturezas de documento:
  - **PDFs gerados pelo sistema (versionados)** — consultados em `DocumentoGerado` (**todas** as versões, não só a última), filtrando por `tipo`:
    - Contratos gerados (`tipo='contrato'`)
    - Laudos gerados (`tipo='laudo'`)
    - Recibos gerados (`tipo='recibo'`)
  - **Anexos manuais (não versionados)** — vêm direto dos campos legados dos models de negócio:
    - Laudos de vistoria com anexo assinado (`LaudoVistoria.arquivo`)
    - Comprovantes de pagamento (`Lancamento.comprovante`)
    - Recibos de entrega de chaves do contrato (`Contrato.recibo_chaves`)
    - Comprovantes anuais de pagamento do contrato (`Contrato.comprovante_anual`)
- Um anexo manual só aparece na central GED se o campo de arquivo **não estiver vazio**.

Ver a seção 14 para as regras do GED versionado (`DocumentoGerado`).

---

## 9. Dashboard — Filtros e Métricas

O dashboard suporta filtros combinados aplicados simultaneamente:

| Filtro | Campo filtrado |
|---|---|
| Imóvel | `contrato__imovel_id` |
| Data início | `data_vencimento__gte` |
| Data fim | `data_vencimento__lte` |
| Status do lançamento | `status` |

O filtro de período (data início/fim) é validado e limpo por `DashboardFiltroForm` (`imoveis/forms.py`), um `forms.Form` com os campos opcionais `data_inicio`/`data_fim`, ambos com widget Flatpickr (formato dd/mm/aaaa).

**Métricas calculadas:**
- Total de imóveis, ocupados e vagos (com base no filtro de imóvel)
- Taxa de vacância: `(vagos / total) * 100`
- Contratos ativos (global, sem filtro)
- Inadimplentes: lançamentos com `status = 'atrasado'` (com filtros aplicados)
- Gráfico de barras: soma de valores pagos e pendentes/atrasados nos últimos 6 meses

---

## 10. Autenticação e Controle de Acesso

- Todas as views exigem autenticação (`@login_required`).
- Usuários não autenticados são redirecionados para `/login/`.
- O painel administrativo Django (`/admin/`) é restrito a usuários com `is_staff = True`.
- Após login bem-sucedido, o usuário é redirecionado para `/` (dashboard).
- Após logout, o usuário é redirecionado para `/login/`.

---

## 11. Alimentação em Tempo Real

- Todas as operações CRUD (criação, edição, exclusão) refletem imediatamente no banco de dados.
- O status do imóvel é recalculado a cada alteração de contrato (via signal), sem necessidade de ação manual.

---

## 12. Validações de Documentos e Campos (`imoveis/validators.py`)

Todos os validadores customizados aceitam o valor com ou sem máscara e removem os não-dígitos antes de validar.

| Validador | Campos que o utilizam | Regra |
|---|---|---|
| `validate_cpf` | `Inquilino.cpf`, `TestemunhaLaudo.cpf`, `Recibo.assinante_cpf` | 11 dígitos + dígitos verificadores válidos |
| `validate_cnpj` | `Inquilino.cnpj` | 14 dígitos + dígitos verificadores válidos |
| `validate_cpf_cnpj` | `Proprietario.cpf_cnpj` | 11 dígitos → valida como CPF; 14 dígitos → valida como CNPJ; caso contrário, erro |
| `validate_rg` | `Inquilino.rg` | Aceita apenas letras, números, "." e "-" (sem dígito verificador nacional) |
| `validate_rg_cpf` | `Fiador.rg_cpf` | Se restarem exatamente 11 dígitos numéricos, valida como CPF (dígitos verificadores); caso contrário, valida o formato como RG |
| `validate_telefone` | `Proprietario.telefone`, `Inquilino.telefone` | Exige 10 dígitos (fixo com DDD) ou 11 dígitos (celular com DDD), com ou sem máscara |

**Dia de vencimento do contrato:** `Contrato.dia_vencimento` usa `MinValueValidator(1)` e `MaxValueValidator(31)` (django.core.validators), restringindo o valor ao intervalo de 1 a 31.

---

## 13. Acesso Mobile (Vistoriadores em Campo)

- A interface é responsiva e permite que vistoriadores realizem consultas e atualizações diretamente do local do imóvel via dispositivos móveis.
- A sidebar é ocultada no mobile e acessada via toggle hamburger.

---

## 14. GED Versionado e Storage Plugável (Rodada 4)

### Versionamento de PDFs (`DocumentoGerado`)

- Cada geração de PDF de Contrato, Laudo ou Recibo cria **uma nova versão imutável** em `DocumentoGerado`. O modelo é a **fonte de verdade** dos documentos gerados pelo sistema.
- **Numeração sequencial por origem:** `numero_versao` começa em 1 e incrementa **independentemente por origem** (calculado via `Max('numero_versao')` filtrado pela FK da origem, em `imoveis/pdf.py:registrar_documento_gerado`). Contratos, laudos e recibos têm sequências próprias.
- **Imutabilidade:** o `save()` do model só permite inserção; qualquer tentativa de update levanta `ValueError`. Não se edita uma versão — gera-se outra.
- **Integridade:** cada versão guarda o `sha256` do arquivo e a autoria (`gerado_por`).
- **Autoria:** as views `contrato_gerar_pdf`, `laudo_gerar_pdf` e `recibo_gerar_pdf` passam `request.user` para `gerar_e_anexar()`, que o repassa a `registrar_documento_gerado()` (usuário não autenticado → `gerado_por` fica nulo).
- **Campos legados como espelho:** `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado` e `Recibo.arquivo` continuam existindo, porém deixam de ser fonte de verdade — `gerar_e_anexar()` os sincroniza automaticamente com a **última** versão via `save_pdf_to_field()`. Servem apenas como atalho para o PDF mais recente.
- **Convenção mantida da Rodada 2:** o PDF continua sendo gerado **somente** pelas views `*_gerar_pdf` (botão "Regerar PDF") — nunca ao salvar create/edit. Cada clique gera uma nova versão.
- **Migração retroativa:** a migração `0010_documentogerado_retroativo` registra os PDFs pré-existentes (nos campos legados) como versão 1 de `DocumentoGerado`, sem copiar o arquivo (apenas referenciando o nome já no storage; hash calculado se o arquivo for legível, senão fica vazio).
- **Admin:** `DocumentoGeradoAdmin` é somente leitura (`has_add_permission`/`has_change_permission` retornam `False`) — o registro só nasce pela geração de PDF.

### Storage plugável (`STORAGE_BACKEND`)

- O armazenamento de arquivos usa a config `STORAGES` do Django 4.2+ (`core/settings.py`), controlada pela variável de ambiente `STORAGE_BACKEND`, seguindo o **mesmo padrão** já usado para `DB_ENGINE`:
  - `filesystem` (default) → `FileSystemStorage`.
  - `s3` → preparado, mas **não ativado** nesta rodada. Setar `STORAGE_BACKEND=s3` sem as libs instaladas levanta `ImproperlyConfigured` explicitamente (mesmo comportamento de `DB_ENGINE=mysql` sem `mysqlclient`).
- `boto3`/`django-storages` **não** foram adicionados ao projeto — apenas a arquitetura está pronta. Todos os `FileField` usam o storage `default`, então a troca para S3 não exige mudança no código de aplicação. O `upload_to` determinístico de `DocumentoGerado` já serve como key de objeto S3.
