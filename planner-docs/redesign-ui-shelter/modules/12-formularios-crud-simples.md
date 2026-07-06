# Objetivo

Reskin dos 9 formularios de CRUD simples (um unico card "Dados de ..." com
grid de campos), conforme `DESIGN_BRIEF.md` secao 3.5 (padrao Formulario):
titulo com "Voltar" no topo, card com grid 2 colunas, labels
uppercase/700/muted, asteriscos `*` em vermelho nos campos obrigatorios, e
footer com botoes Cancelar (outline) + Salvar (graphite). Mesma receita
visual aplicada nos 9 arquivos, cada um com seus proprios campos ja
renderizados via `{{ form.campo }}` -- nenhum campo e adicionado, removido
ou reordenado.

---

# Arquivos afetados

- `templates/imoveis/imovel_form.html`
- `templates/imoveis/notificacao_form.html`
- `templates/inquilinos/inquilino_form.html`
- `templates/proprietarios/proprietario_form.html`
- `templates/contratos/contrato_form.html`
- `templates/contratos/renovacao_form.html`
- `templates/contratos/distrato_form.html`
- `templates/recibos/recibo_form.html`
- `templates/financeiro/lancamento_form.html`

---

## Documentacao relacionada

- docs/07_design_ui_ux.md secao 8 (Formularios)
  Atualizar tokens de input/label/focus e o novo padrao de footer sticky
  Cancelar/Salvar.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

Para cada um dos 9 arquivos:
- [ ] Link "Voltar" no topo preservado (mesma url de listagem/detalhe).
- [ ] Card unico "Dados de <Entidade>" com grid de campos identico ao
      layout atual (mesmas colunas/agrupamentos), usando
      `{{ form.campo }}` sem alterar nomes de campo.
- [ ] Labels no padrao uppercase/700/letter-spacing/muted do brief, com
      asterisco `*` em `--danger` nos campos `required`.
- [ ] `imovel_form.html`: preservar o subform de fotos (`FotoImovel`
      inline/formset, se existir) e os campos condicionais urbano/rural
      (cadastro_prefeitura vs. nirf/incra/car) exatamente como hoje.
- [ ] `contrato_form.html`: confirmar que os 4 campos de documento GED
      (comprovante_renda/contrato_social/recibo_chaves/comprovante_anual)
      **nao aparecem** neste form (saíram na Rodada 3 -- ja nao devem
      estar aqui; se ainda estiverem por engano, reportar como bug fora de
      escopo deste modulo, nao remover silenciosamente sem confirmar).
- [ ] Mensagens de erro de validacao (`form.errors`) exibidas com o novo
      estilo de alerta, preservando o texto/campo de cada erro.
- [ ] Footer com botoes "Cancelar" (outline, leva para list/detail) e
      "Salvar" (graphite, submit), preservando o `method="post"` e
      `{% csrf_token %}`.
- [ ] Campos com Flatpickr (`data-flatpickr`) e IMask
      (`data-mask="moeda"`/`"telefone"`) continuam funcionando
      (`static/js/masks.js` nao e alterado).
- [ ] Nenhuma view, url, model ou signal alterada; `imoveis/forms.py` nao
      e tocado.

---

# Riscos

- `imovel_form.html` e o mais complexo do grupo (subform de fotos +
  campos condicionais) -- validar manualmente criacao e edicao de um
  imovel urbano e um rural.
- Datepicker (Flatpickr) e mascara de moeda (IMask) dependem de atributos
  `data-flatpickr`/`data-mask` definidos em `imoveis/forms.py` (fora de
  escopo) -- o reskin nao pode remover ou renomear esses atributos ao
  ajustar o markup ao redor do campo.
