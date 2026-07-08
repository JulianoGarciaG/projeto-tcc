# Plano: Camada de identidade/nomenclatura (código, rótulos, nomes de arquivo)

## Objetivo

Hoje o sistema identifica Imóvel/Contrato/Recibo/Laudo de forma improvisada:
dropdowns e listas mostram `Contrato #17` (sem inquilino/imóvel visíveis sem
abrir o registro) e os PDFs baixam como `contrato_3.pdf`, `laudo_5.pdf`,
`recibo_9.pdf` — indistinguíveis entre si numa pasta de Downloads com 20
arquivos. Esta rodada cria uma camada única de identidade (`imoveis/identidade.py`)
que resolve os dois sintomas ao mesmo tempo:

- **Código de negócio derivado do PK** — sem migração, sem campo novo:
  `f'{PREFIXO}-{pk:04d}'` (`IMV`, `CTR`, `REC`, `LAU`).
- **Rótulos legíveis** (`rotulo_curto` para dropdown/chip, `rotulo_longo` para
  cabeçalho de detalhe) usados em selects (`label_from_instance`) e templates.
- **Nome de arquivo determinístico** (`nome_arquivo()`) usado tanto na versão
  imutável do GED (`DocumentoGerado`) quanto no download do PDF.

## Estado atual (investigado)

- `imoveis/models.py`: `Imovel.__str__` (linha 75-76), `Contrato.__str__`
  (178-179), `LaudoVistoria.__str__` (252-253), `Recibo.__str__` (480-481) —
  todos com `#pk` cru ou pouco contexto. **Não serão alterados** (usados em
  admin/PDFs/shell) — a nova camada é aditiva (`codigo`/`rotulo_curto`/`rotulo_longo`),
  não substitui `__str__`.
- `imoveis/pdf.py`: `gerar_e_anexar()` (linha 100) recebe `filename` já pronto
  do chamador; `registrar_documento_gerado()` (69) calcula `numero_versao`
  internamente (`Max('numero_versao') + 1`) — essa é a única fonte hoje da
  próxima versão.
- `imoveis/views.py`: `_gerar_pdf_contrato` (29), `_gerar_pdf_laudo` (52),
  `_gerar_pdf_recibo` (65) montam `filename = f'contrato_{pk}.pdf'` etc. — só
  essas 3 funções (chamadas por `contrato_gerar_pdf`/`laudo_gerar_pdf`/
  `recibo_gerar_pdf`) geram PDF, conforme convenção "PDF nunca é gerado ao
  salvar". `contratos_por_imovel_json` (621) monta o label do select
  dependente manualmente: `f'Contrato #{c.pk} — {c.inquilino.nome} ({...})'`.
- `imoveis/forms.py`: nenhum `ModelChoiceField` hoje sobrescreve
  `label_from_instance` — todos usam o default (`str(obj)`). FKs para as 4
  entidades aparecem em: `ContratoForm.imovel` (133), `LaudoVistoriaForm.imovel`
  e `.contrato` (186-187, com queryset dinâmico no `__init__` — 194-208),
  `ReciboForm.imovel`/`.contrato` (339-340), `LancamentoForm.contrato` (261),
  `NotificacaoForm.imovel` (280), `DistratoForm.laudo_saida` (316).
- Templates com identificação crua: `contrato_detail.html` (3-4, `Contrato
  #{{ contrato.pk }}`), `renovacao_form.html` (18), `recibo_detail.html`
  (3-4, 24), `recibo_list.html` (39, 51), `laudo_detail.html` (2-3),
  `ged/documentos.html` (listas de laudos/comprovantes/gerados sem código),
  `imovel_detail.html` (título usa `{{ imovel }}`, i.e. `__str__`).
- Sem "select dependente" de Recibo (só o de Laudo→Contrato existe,
  `contratos_por_imovel_json`); `ReciboForm.imovel`/`.contrato` são selects
  simples.

## Resumo dos módulos

| Módulo | Objetivo | Arquivos principais |
|---|---|---|
| `01-identidade-core` | Criar `imoveis/identidade.py` (mixin + `nome_arquivo`) e aplicar aos 4 models | `imoveis/identidade.py` (novo), `imoveis/models.py` |
| `02-forms-labels-select` | `ModelChoiceField` com `label_from_instance` = `rotulo_curto` nos selects das 4 entidades + label do JSON de laudo | `imoveis/forms.py`, `imoveis/views.py` (só `contratos_por_imovel_json`) |
| `03-pdf-nomes-arquivo` | Nomes de arquivo determinísticos no GED e no download | `imoveis/pdf.py`, `imoveis/views.py` (só `_gerar_pdf_*`) |
| `04-templates-listas-detalhe` | Trocar `#pk` cru por `codigo`/`rotulo_longo` nas listas/detalhes | templates de `imoveis/contratos/recibos/laudos/ged` |
| `05-testes-identidade` | Cobertura de `codigo`, `nome_arquivo`, labels de select e filename dos PDFs | `imoveis/tests.py` |

## Ordem de implementação

1. `01-identidade-core` (base — todos os outros dependem dela)
2. `02-forms-labels-select` (depende de 01)
3. `03-pdf-nomes-arquivo` (depende de 01; independente de 02)
4. `04-templates-listas-detalhe` (depende de 01; independente de 02/03)
5. `05-testes-identidade` (depende de 01, 02, 03 e 04 já implementados)

Módulos 02, 03 e 04 são independentes entre si e podem ser feitos em qualquer
ordem relativa, desde que 01 já esteja pronto.

## Afinidade de cache entre módulos

- **02 e 03 tocam `imoveis/views.py`** (funções diferentes: 02 mexe só em
  `contratos_por_imovel_json`; 03 mexe só em `_gerar_pdf_*`). Se o usuário
  quiser aproveitar o cache quente de `views.py`, pode implementar 02 e 03 na
  mesma janela, nessa ordem.
- **01 é a única que toca `models.py`** — isolada por natureza.
- **04 só toca templates** — isolada.
- **05 só toca `tests.py`**, mas precisa dos 4 anteriores já implementados no
  código para escrever testes que passem.

## Observações gerais

- Nenhuma migration é necessária (código de negócio é derivado do PK em
  runtime, não persistido).
- `__str__` dos 4 models permanece intocado nesta rodada — `codigo`,
  `rotulo_curto` e `rotulo_longo` são propriedades novas e aditivas.
- Documentos já gerados antes desta mudança mantêm seus nomes de arquivo
  antigos (`contrato_3.pdf` etc.) — não há reprocessamento retroativo; a nova
  convenção vale só para gerações futuras.
- Encoding no Windows: qualquer edição de template (`.html`) deve usar a
  ferramenta Edit, nunca `Get-Content`/`Set-Content` do PowerShell (corrompe
  UTF-8 — já registrado em CLAUDE.md e na memória do projeto).
