# 05 — GED e Documentos Versionados
> Sistema Integrado de Gestão Imobiliária (GED e BI)

Documento dedicado ao **GED versionado** — o model `DocumentoGerado`, o storage plugável e as regras de negócio da central de documentos (`/documentos/`). Extraído de `docs/02_modelagem_dados.md` e `docs/03_regras_de_negocio.md` por densidade temática (Rodada 4).

---

## 1. Modelo `DocumentoGerado`

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

> Os campos legados `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado` e `Recibo.arquivo` são **mantidos**, mas deixam de ser fonte de verdade: passam a ser espelhos automáticos da última versão, sincronizados por `imoveis.pdf.gerar_e_anexar()`. Ver seção 3 abaixo.

**Caminho de upload:** `DocumentoGerado.arquivo` → `ged/{tipo}/{origem_pk}/v{numero_versao}/` (ver tabela completa de uploads em [docs/02_modelagem_dados.md](02_modelagem_dados.md#3-caminhos-de-upload-media_root)).

---

## 2. GED — Gestão Eletrônica de Documentos (central `/documentos/`)

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

---

## 3. Versionamento de PDFs (regras de negócio, Rodada 4)

- Cada geração de PDF de Contrato, Laudo ou Recibo cria **uma nova versão imutável** em `DocumentoGerado`. O modelo é a **fonte de verdade** dos documentos gerados pelo sistema.
- **Numeração sequencial por origem:** `numero_versao` começa em 1 e incrementa **independentemente por origem** (calculado via `Max('numero_versao')` filtrado pela FK da origem, em `imoveis/pdf.py:registrar_documento_gerado`). Contratos, laudos e recibos têm sequências próprias.
- **Imutabilidade:** o `save()` do model só permite inserção; qualquer tentativa de update levanta `ValueError`. Não se edita uma versão — gera-se outra.
- **Integridade:** cada versão guarda o `sha256` do arquivo e a autoria (`gerado_por`).
- **Autoria:** as views `contrato_gerar_pdf`, `laudo_gerar_pdf` e `recibo_gerar_pdf` passam `request.user` para `gerar_e_anexar()`, que o repassa a `registrar_documento_gerado()` (usuário não autenticado → `gerado_por` fica nulo).
- **Campos legados como espelho:** `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado` e `Recibo.arquivo` continuam existindo, porém deixam de ser fonte de verdade — `gerar_e_anexar()` os sincroniza automaticamente com a **última** versão via `save_pdf_to_field()`. Servem apenas como atalho para o PDF mais recente.
- **Nome de arquivo determinístico:** `gerar_e_anexar()` calcula o filename via `imoveis/identidade.py:nome_arquivo(instance, versao=n)` (padrão `{Tipo}_{codigo}_..._v{n}.pdf`) e retorna `(pdf_bytes, filename)` — o mesmo nome vai para a versão do GED, para o campo legado e para o download (`Content-Disposition`). Documentos gerados antes desta convenção mantêm o nome antigo (`contrato_3.pdf` etc.); não há reprocessamento retroativo.
- **Convenção mantida da Rodada 2:** o PDF continua sendo gerado **somente** pelas views `*_gerar_pdf` (botão "Regerar PDF") — nunca ao salvar create/edit. Cada clique gera uma nova versão.
- **Migração retroativa:** a migração `0010_documentogerado_retroativo` registra os PDFs pré-existentes (nos campos legados) como versão 1 de `DocumentoGerado`, sem copiar o arquivo (apenas referenciando o nome já no storage; hash calculado se o arquivo for legível, senão fica vazio).
- **Admin:** `DocumentoGeradoAdmin` é somente leitura (`has_add_permission`/`has_change_permission` retornam `False`) — o registro só nasce pela geração de PDF.

---

## 4. Storage plugável (`STORAGE_BACKEND`)

- O armazenamento de arquivos usa a config `STORAGES` do Django 4.2+ (`core/settings.py`), controlada pela variável de ambiente `STORAGE_BACKEND`, seguindo o **mesmo padrão** já usado para `DB_ENGINE`:
  - `filesystem` (default) → `FileSystemStorage`.
  - `s3` → preparado, mas **não ativado** nesta rodada. Setar `STORAGE_BACKEND=s3` sem as libs instaladas levanta `ImproperlyConfigured` explicitamente (mesmo comportamento de `DB_ENGINE=mysql` sem `mysqlclient`).
- `boto3`/`django-storages` **não** foram adicionados ao projeto — apenas a arquitetura está pronta. Todos os `FileField` usam o storage `default`, então a troca para S3 não exige mudança no código de aplicação. O `upload_to` determinístico de `DocumentoGerado` já serve como key de objeto S3.
