# Objetivo

Reskin de `templates/dashboard.html` conforme `DESIGN_BRIEF.md` secao 3.2:
barra de filtros, 5 KPI cards, os 2 graficos Chart.js (donut de ocupacao +
barras recebido/pendente) e a tabela de ultimos lancamentos. Migra as
cores do Chart.js, hoje hardcoded em hex no `<script>`, para leitura das
CSS vars do tema ativo, e adiciona redesenho dos graficos quando o tema
muda (ouvindo o evento disparado por `static/js/theme.js`, modulo 02).
Nao altera a view `dashboard` nem os nomes de contexto usados no template.

---

# Arquivos afetados

- `templates/dashboard.html`

---

## Documentacao relacionada

- docs/07_design_ui_ux.md secao 13 (Graficos)
  Atualizar cores/paleta dos graficos para os tokens novos e documentar o
  redesenho no toggle de tema.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome + evento `shelter:theme-changed` do toggle de tema).

---

# Criterios de aceite

- [ ] Barra de filtros (card) com os campos Imovel (select), Data inicio,
      Data fim (Flatpickr, ja usados via `filtro_form`), Status (select) e
      botoes Filtrar/Limpar -- mesmos campos e nomes de contexto de hoje
      (`imoveis_lista`, `filtro_form`, `filtro_imovel_id`, `status_choices`,
      `filtro_status`), so o visual.
- [ ] 5 KPI cards em grid, cada um com label uppercase + bolinha/icone de
      status colorido, numero 34px/800 e linha auxiliar -- usando os
      mesmos valores de contexto ja existentes (`total_imoveis`,
      `ocupados`, `vagos`, `taxa_vacancia`, `contratos_ativos`,
      `inadimplentes`).
- [ ] 2 graficos Chart.js: donut "Ocupacao dos imoveis" (cutout ~64%,
      legenda embaixo) e barras "Recebimentos vs. Pendencias - ultimos 6
      meses" -- usando os mesmos dados de contexto (`pizza_labels`,
      `pizza_data`, `meses_labels`, `meses_pagos`, `meses_pendentes`).
- [ ] Cores dos dois graficos passam a ser lidas via
      `getComputedStyle(document.documentElement).getPropertyValue(...)`
      nos tokens `--ok`, `--danger`, `--brand`/`--warn`, `--surface` etc.,
      em vez de hex fixo.
- [ ] Ao disparar o evento `shelter:theme-changed` (modulo 02), os dois
      `Chart` instances sao destruidos (`chart.destroy()`) e recriados com
      as cores do novo tema -- sem duplicar canvases nem vazar memoria.
- [ ] Tabela "Ultimos Lancamentos Financeiros" com colunas
      Inquilino/Imovel/Tipo/Vencimento/Valor/Status (badge pill) e header
      com link "Ver todos" para `lancamento_list` -- preservado.
- [ ] Nenhuma mudanca na view `dashboard` (`imoveis/views.py`) nem nos
      nomes de variaveis de contexto.

---

# Riscos

- Recriar os `Chart` a cada troca de tema sem chamar `destroy()` no
  grafico anterior gera vazamento de memoria e sobreposicao visual --
  testar a troca de tema repetidas vezes.
- Se o evento do modulo 02 nao disparar (ex.: nome do evento divergente),
  os graficos ficam com as cores do tema errado apos o toggle -- validar a
  integracao contra o `static/js/theme.js` produzido no modulo 02.
