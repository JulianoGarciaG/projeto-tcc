# Plano — Fotos por item do checklist de vistoria (`ItemVistoria`)

## Objetivo

Permitir anexar 0..N fotos a cada `ItemVistoria` de um `LaudoVistoria`, enviadas
no mesmo formset de criação/edição do laudo (`item_formset`, prefixo `itens`).
As fotos aparecem apenas no detalhe do laudo (agrupadas por item) — nunca no
PDF do laudo (`documentos/laudo_pdf.html`) nem na central GED (`/documentos/`,
view `documentos`). Exclusão individual de foto fica fora de escopo — vira
trabalho futuro (RF6).

## Estado atual (investigado)

- `ItemVistoria` (`imoveis/models.py:341`) é um snapshot do catálogo,
  `FK laudo CASCADE`, sem qualquer campo de mídia hoje.
- O formset de itens (`imoveis/forms.py:246` `item_vistoria_formset_factory`)
  é um `inlineformset_factory(LaudoVistoria, ItemVistoria, form=ItemVistoriaForm)`.
  Em `laudo_create` (`imoveis/views.py:543`) o `extra` **precisa** ser
  `len(catalogo)` (armadilha já documentada no CLAUDE.md); em `laudo_edit`
  (`imoveis/views.py:573`) usa-se `ItemVistoriaFormSet` (extra=0), pois os
  itens já existem.
- **Comportamento de "linha vazia é ignorada"**: em `laudo_create`, todas as
  linhas do formset nascem como forms "extra" com `initial` vindo do catálogo
  (`comodo`/`item`/`ordem` ocultos) e `empty_permitted=True`. Uma linha só é
  validada/salva se `form.has_changed()` for `True` — o que hoje só acontece
  quando o usuário escolhe um `estado`. Isso é usado deliberadamente (ver
  `imoveis/tests.py:542` `test_laudo_create_salva_apenas_itens_com_estado`).
  **Anexar foto vai contar como mudança do form** (o novo campo não-model
  `fotos` terá `initial` vazio), então uma linha com foto mas sem `estado`
  passará a exigir `estado` (campo obrigatório do model) — ver riscos no
  módulo de views.
- O `<form>` de `laudo_form.html` **não tem** `enctype="multipart/form-data"`
  hoje (nenhum upload acontece nesse form — o anexo do laudo assinado é em
  formulário separado, `laudo_anexar_arquivo`). Precisa ganhar o atributo.
- `laudo_detail.html` (linha 104-128) renderiza `grupos` (lista de
  `{comodo, itens}`, montada por `_itens_agrupados()` em `imoveis/views.py:40`)
  em uma tabela simples, sem qualquer referência a mídia.
- A central GED (view `documentos`, `imoveis/views.py:805`) só lê
  `DocumentoGerado` e campos de arquivo específicos de `Contrato`/
  `Lancamento`/`LaudoVistoria` — nenhuma referência a `ItemVistoria`. Não
  precisa de nenhuma alteração para cumprir RF5; o módulo de testes apenas
  confirma isso com um teste de regressão.
- O PDF do laudo (`documentos/laudo_pdf.html`, gerado por
  `_gerar_pdf_laudo`/`imoveis/views.py:50`) usa o mesmo `grupos` do detail,
  mas o template PDF não itera nada além do que já existe hoje — não precisa
  de alteração para cumprir RF4; também coberto por teste de regressão.

## Resumo dos módulos

| Módulo | Arquivo(s) | Responsabilidade |
|---|---|---|
| `01-model-foto-item-vistoria` | `imoveis/models.py`, migration nova | Model `FotoItemVistoria` + migração |
| `02-form-widget-multiplo-arquivo` | `imoveis/forms.py` | Campo/widget de upload múltiplo + `ItemVistoriaForm.fotos` |
| `03-views-laudo` | `imoveis/views.py` | Salvar fotos após o formset de itens (create/edit) + prefetch no detail |
| `04-templates-laudo` | `templates/laudos/laudo_form.html`, `templates/laudos/laudo_detail.html` | Input de upload por linha + galeria agrupada por item |
| `05-tests` | `imoveis/tests.py` | Cobertura funcional + regressão de PDF/GED |

## Ordem de implementação

1. `01-model-foto-item-vistoria`
2. `02-form-widget-multiplo-arquivo`
3. `03-views-laudo` (depende de 01 e 02)
4. `04-templates-laudo` (depende de 02 e 03)
5. `05-tests` (depende de 01–04)

## Dependências entre módulos

- `03` depende de `01` (precisa do model `FotoItemVistoria`) e de `02`
  (precisa do campo `fotos` em `ItemVistoriaForm`/`cleaned_data`).
- `04` depende de `02` (nome do campo `fotos` a renderizar no form) e de `03`
  (contexto do `laudo_detail` com fotos prefetchadas).
- `05` depende de todos os anteriores estarem implementados.

## Afinidade de cache

Nenhum módulo compartilha arquivo-fonte com outro (cada um mexe em um arquivo
distinto: `models.py`, `forms.py`, `views.py`, os dois templates de laudo, e
`tests.py`). Não há ganho de cache em agrupar módulos na mesma janela — pode
implementar cada um em janela nova sem perda.

## Observações gerais

- Nenhuma migration é criada por este plano — o módulo `01` apenas descreve o
  model; quem implementa roda `makemigrations`/`migrate`.
- Convenção de upload: `itens_vistoria/{item_id}/{filename}` (usa
  `instance.item_id`, sem precisar carregar o objeto relacionado nem o
  `laudo_id`) — desvio deliberado da sugestão inicial
  (`itens_vistoria/{laudo_id}/`), documentado no módulo `01`.
- Trabalho futuro (fora de escopo, apenas registrar em algum lugar visível ao
  final — ex. comentário no template de detalhe ou nota em
  `docs/historico_entregas.md` quando a rodada for fechada): exclusão
  individual de foto (endpoint + botão no detail, provavelmente
  `POST /laudos/<pk>/itens/<item_pk>/fotos/<foto_pk>/excluir/`).
