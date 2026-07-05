# Objetivo

Substituir os dois campos de data do filtro do Dashboard (hoje `<input type="date">` nativo do navegador, fora do padrao do projeto) por inputs Flatpickr no formato dd/mm/aaaa, consistentes com todo o restante do sistema, sem alterar o comportamento dos demais filtros (imovel e status).

---

# Arquivos afetados

- `imoveis/forms.py`
  - Adicionar nova classe `DashboardFiltroForm(forms.Form)` (final do arquivo), com apenas dois campos: `data_inicio` e `data_fim`, ambos `forms.DateField(required=False, input_formats=["%d/%m/%Y"])`.
  - No `__init__`, sobrescrever o widget dos dois campos com `_date_widget()` (mesma funcao ja usada por todos os outros forms do arquivo).
  - Nao incluir `imovel_id`/`status` neste form — esses dois filtros continuam como estao hoje (selects renderizados manualmente no template), para minimizar a superficie de mudanca.

- `imoveis/views.py`
  - `dashboard()` (linhas 68-146): substituir a leitura manual de `data_inicio = request.GET.get("data_inicio", "")` / `data_fim = ...` (linhas 73-74) por `filtro_form = DashboardFiltroForm(request.GET or None)`, `filtro_form.is_valid()` e `filtro_form.cleaned_data.get("data_inicio")` / `.get("data_fim")` (objetos `date`, nao mais strings). Os filtros `lancamentos_qs.filter(data_vencimento__gte=...)`/`__lte=...` (linhas 84-86) continuam iguais, agora recebendo um `date` em vez de uma string ISO.
  - Import: adicionar `DashboardFiltroForm` ao import de `.forms` (topo do arquivo).
  - Contexto (linhas 124-146): substituir as chaves `filtro_data_inicio`/`filtro_data_fim` (usadas so para reexibir o valor no `value=` do input antigo) por `filtro_form` (o template renderiza o form ja populado quando houver GET).

- `templates/dashboard.html`
  - Linhas 31-38: trocar os dois blocos `<input type="date" ...>` por `{{ filtro_form.data_inicio }}` e `{{ filtro_form.data_fim }}`, mantendo as mesmas colunas Bootstrap (`col-6 col-md-2`) e `<label>` existentes.
  - Nao mexer nos filtros de imovel/status (linhas 20-30 e 39-47) nem nos graficos/scripts.

- `imoveis/tests.py`
  - Novo teste garantindo que o dashboard aceita e aplica o filtro de data em dd/mm/aaaa (ver Criterios de aceite). Pode ser adicionado a uma classe existente (`FluxoViewTests`) ou a uma nova classe `DashboardFiltroTests`.

---

## Documentacao relacionada

- `docs/04_regras_de_negocio.md`
  Secao 9 ("Dashboard — Filtros e Metricas"): sem mudanca de regra de negocio (os filtros continuam os mesmos), mas pode-se acrescentar uma nota de que as datas sao informadas no formato dd/mm/aaaa via datepicker, para consistencia com o resto do sistema.

- `docs/07_design_ui_ux.md`
  Nao ha secao dedicada a datepickers hoje; sem impacto obrigatorio, mas e a documentacao mais apropriada caso o mantenedor decida registrar formalmente "todo campo de data do sistema usa Flatpickr dd/mm/aaaa" como padrao de UI.

- `docs/03_modelagem_dados.md`
  Sem impacto (o Dashboard nao tem model proprio).

---

# Dependencias

Nenhuma. Modulo independente.

---

# Criterios de aceite

- [ ] Os dois campos de data do filtro do Dashboard sao renderizados com o mesmo Flatpickr (`data-flatpickr`, placeholder `dd/mm/aaaa`) usado em todo o resto do sistema.
- [ ] Submeter o filtro com datas em dd/mm/aaaa filtra corretamente os lancamentos exibidos e os KPIs (mesma logica de antes, so a fonte do valor mudou de string ISO para `date` do form).
- [ ] Nao submeter nenhum filtro (primeira visita ao dashboard) continua funcionando exatamente como hoje (nenhum filtro aplicado, campos vazios).
- [ ] Os filtros de imovel e status continuam funcionando sem nenhuma alteracao de comportamento ou HTML.
- [ ] Novo teste em `imoveis/tests.py` fazendo `GET` em `reverse("dashboard")` com `data_inicio=01/08/2026&data_fim=31/08/2026` (formato dd/mm/aaaa) e verificando que apenas lancamentos dentro do periodo aparecem no contexto (`ultimos_lancamentos`) — usar `criar_base()` e criar 2 `Lancamento` (um dentro, um fora do periodo) para o teste.
- [ ] `python manage.py test imoveis` roda sem falhas.
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Baixo: se alguem tiver um link/bookmark salvo com `?data_inicio=2026-08-01` (formato ISO antigo), o novo `DashboardFiltroForm` (que so aceita `%d/%m/%Y`) vai considerar o campo invalido e ignorar o filtro silenciosamente (comportamento de `is_valid()` retornando `False` so para aquele campo, sem quebrar a pagina) — nao ha bookmarks desse tipo documentados/conhecidos, risco aceitavel.
- Verificar que `masks.js` (carregado globalmente via `base.html`) roda normalmente na pagina do dashboard, ja que ela tambem carrega Chart.js — nenhum conflito esperado, pois sao bibliotecas independentes.
