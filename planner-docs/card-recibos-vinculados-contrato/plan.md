# Plano: Card de Recibos Vinculados no detalhe do Contrato

## Objetivo

Exibir, na tela de detalhe do contrato, os recibos (`Recibo`, model de
negócio) vinculados àquele contrato via `Recibo.contrato` (FK obrigatória,
`on_delete=PROTECT`, `related_name='recibos'`). Cada linha mostra vencimento,
valor e parcela, linkando para `recibo_detail`. Um botão "Novo Recibo" abre o
formulário de criação com `imovel`/`contrato` pré-selecionados.

**Não confundir** com a central GED (`DocumentoGerado` com `tipo='recibo'`,
versões de PDF geradas) — entidade diferente, fora de escopo.

## Estado atual

- `contrato_detail` (`imoveis/views.py:387-407`) já monta contexto com
  `lancamentos`, `laudos`, `fiadores`, `renovacao`, `distrato`. Não inclui
  recibos.
- `templates/contratos/contrato_detail.html` tem cards com componente visual
  padrão `.section-card` / `.section-card-header` / `.table-responsive` +
  `<table class="table mb-0 small">`, cada um com `empty-state` no `{% empty %}`
  (ver card "Laudos de Vistoria", linha 233-257, usado como referência
  estrutural mais próxima).
- `recibo_create` (`imoveis/views.py:800-806`) **não recebe nenhum parâmetro**
  hoje — `ReciboForm(request.POST or None)`, sem `initial`. `ReciboForm`
  (`imoveis/forms.py:384-423`) tem `imovel`/`contrato` como campos
  obrigatórios (`ImovelChoiceField`/`ContratoChoiceField`), renderizados
  diretamente no template (`{{ form.imovel }}`, `{{ form.contrato }}`) sem
  lógica de pré-seleção.
- Precedente de pré-preenchimento de FK a partir de objeto pai: `notificacao_create`
  (`imoveis/views.py:738-750`) recebe `imovel_pk` como **parâmetro de rota**
  dedicada (`imoveis/<int:imovel_pk>/notificacoes/nova/`) e faz
  `form.fields['imovel'].initial = imovel`. Não há precedente de querystring
  (`?contrato=<pk>`) em nenhuma view do projeto.
- `Recibo.parcela_atual`/`parcela_total` são `PositiveSmallIntegerField(null=True,
  blank=True)` (`imoveis/models.py:556-557`). `quantia` também é opcional.
  `Meta.ordering` do model já ordena por `-criado_em` (herdado de
  `IdentificavelMixin`/definição do model — `contrato.recibos.all()` já vem
  na ordem certa, sem necessidade de `.order_by()` explícito).

## Decisão de arquitetura: mecanismo de pré-preenchimento

**Escolhido: nova rota dedicada** `contratos/<int:contrato_pk>/recibos/novo/`
→ view nova `recibo_create_from_contrato(request, contrato_pk)`, seguindo
exatamente o padrão já estabelecido por `notificacao_create`. Motivos:

1. É o único precedente real no projeto para "criar filho pré-vinculado ao
   pai" — reaproveitar convenção existente reduz risco e diverge menos do
   restante do código.
2. Querystring (`?contrato=<pk>`) não tem nenhum precedente no projeto; forçaria
   inventar um padrão novo (parsing de `request.GET`, tratamento de pk
   inválido/ausente) só para este caso.
3. A view genérica `recibo_create` (sem contrato) continua existindo
   inalterada, usada pelo botão "+ Novo" da tela `recibo_list` — comportamento
   atual não muda.

A nova view: busca `Contrato` por `contrato_pk` (404 se não existir), seta
`form.fields['imovel'].initial = contrato.imovel` e
`form.fields['contrato'].initial = contrato`, reaproveita o template
`recibos/recibo_form.html` existente (sem alterações nele). No sucesso,
redireciona para `recibo_detail` do recibo criado (mesmo comportamento de
`recibo_create` hoje — não redireciona de volta ao contrato).

## Resumo dos módulos

| # | Módulo | Responsabilidade |
|---|---|---|
| 1 | `view-e-url-recibo-from-contrato` | View `recibo_create_from_contrato` + rota nova |
| 2 | `card-recibos-contrato-detail` | Contexto de `contrato_detail` + card no template |

## Ordem de implementação

1 → 2

Módulo 2 depende do módulo 1 (o botão "Novo Recibo" do card linka para a URL
criada no módulo 1).

## Afinidade de cache

- Módulo 1 toca `imoveis/views.py` e `imoveis/urls.py`.
- Módulo 2 toca `imoveis/views.py` (adiciona 1 linha ao contexto de
  `contrato_detail`, já presente no mesmo arquivo do módulo 1) e
  `templates/contratos/contrato_detail.html`.
- Ambos tocam `imoveis/views.py`, mas em funções diferentes e distantes no
  arquivo (`recibo_create_from_contrato` fica perto de `recibo_create`,
  linha ~800; `contrato_detail` fica na linha ~387). Ganho de cache é baixo;
  pode-se implementar em janelas separadas sem custo relevante, mas também é
  seguro fazer ambos na mesma janela em sequência se preferir.

## Observações gerais

- Nenhuma migration necessária — `Recibo.contrato` já existe.
- Fora de escopo: alterar `recibo_form.html`, alterar `recibo_create`
  genérica, calcular fallback de `quantia` via `somatorio()`, reordenar
  `contrato.recibos` além do ordering padrão do model, estado de
  lida/paginação na listagem do card.
- Testar o card em ambos os temas (claro/escuro), por convenção do projeto
  (CLAUDE.md).
