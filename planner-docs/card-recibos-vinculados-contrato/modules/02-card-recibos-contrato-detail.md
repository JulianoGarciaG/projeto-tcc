# Objetivo

Adicionar o card "Recibos Vinculados" na tela de detalhe do contrato,
listando os recibos do contrato (vencimento, valor, parcela) com link para
`recibo_detail`, e um botão "Novo Recibo" que abre o formulário pré-preenchido
(via `recibo_create_from_contrato`, criado no módulo 1).

# Arquivos afetados

- `imoveis/views.py` — view `contrato_detail` (linhas 387-407): adicionar
  `recibos = contrato.recibos.all()` ao contexto.
- `templates/contratos/contrato_detail.html` — novo card `.section-card`,
  inserido na sequência dos cards existentes (recomendado: logo após o card
  "Laudos de Vistoria", linhas 233-257, mesma coluna/`<div class="row g-3">`).

# Dependências

Módulo 1 (`view-e-url-recibo-from-contrato`) — o botão "Novo Recibo" usa
`{% url 'recibo_create_from_contrato' contrato.pk %}`.

# Leituras adicionais

Nenhuma — o trecho do card "Laudos de Vistoria" (referência estrutural) e o
contexto de `contrato_detail` já estão descritos em `plan.md`.

# Implementação

**View** — em `contrato_detail`, adicionar ao contexto (mesmo padrão de
`laudos`/`fiadores`, sem `.order_by()` explícito pois o `Meta.ordering` do
model `Recibo` já é `-criado_em`):

```python
recibos = contrato.recibos.all()
```

E incluir `'recibos': recibos,` no dicionário de contexto retornado.

**Template** — novo card, seguindo o componente `.section-card` já usado
pelo card de Laudos. Colunas: Vencimento, Valor, Parcela, e uma coluna final
com link/ícone para o detalhe do recibo. Regras de exibição (todas via
`{% if %}`, sem calcular fallback):

- `r.vencido_em` vazio → "—" (usar `{{ r.vencido_em|date:"d/m/Y"|default:"—" }}`
  ou `{% if %}`/`{% else %}` explícito).
- `r.quantia` vazio → "—" (não somar `valor_aluguel`/`valor_impostos`/
  `valor_seguros`/`valor_condominio`, mesmo que preenchidos).
- `r.parcela_atual`/`r.parcela_total` vazios → "—" cada um, independentemente
  (não exigir que os dois estejam preenchidos juntos para exibir um deles).

```html
<div class="section-card">
  <div class="section-card-header">
    <i class="bi bi-receipt me-1"></i> Recibos Vinculados
    <a href="{% url 'recibo_create_from_contrato' contrato.pk %}" class="btn btn-outline-primary btn-sm ms-auto">+ Novo Recibo</a>
  </div>
  <div class="table-responsive">
    <table class="table mb-0 small">
      <thead>
        <tr><th>Vencimento</th><th>Valor</th><th>Parcela</th><th></th></tr>
      </thead>
      <tbody>
        {% for r in recibos %}
        <tr>
          <td>{% if r.vencido_em %}{{ r.vencido_em|date:"d/m/Y" }}{% else %}—{% endif %}</td>
          <td>{% if r.quantia %}R$ {{ r.quantia|brl }}{% else %}—{% endif %}</td>
          <td>{% if r.parcela_atual %}{{ r.parcela_atual }}{% else %}—{% endif %}/{% if r.parcela_total %}{{ r.parcela_total }}{% else %}—{% endif %}</td>
          <td><a href="{% url 'recibo_detail' r.pk %}" class="btn btn-sm btn-outline-secondary"><i class="bi bi-eye"></i></a></td>
        </tr>
        {% empty %}
        <tr><td colspan="4" class="border-0"><div class="empty-state"><i class="bi bi-inbox"></i>Nenhum recibo.</div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
```

Nota: `r.quantia` é `DecimalField` — testar explicitamente `{% if r.quantia %}`
(não `is not None`), pois `0` também deve cair no "—" tanto quanto `None`
(mesma convenção usada pelos demais cards do template, ex. `l.comprovante`).
Usar filtro `brl` já registrado em `imoveis/templatetags/imoveis_tags.py`
(mesmo padrão do resto do template, ex. linha 221 `{{ l.valor|brl }}`).

# Critérios de aceite

- [ ] Card "Recibos Vinculados" aparece no detalhe do contrato, seguindo o
      visual `.section-card` (ícone no header, tabela `small`, empty-state).
- [ ] Lista os recibos do contrato ordenados por `-criado_em` (mais recente
      primeiro).
- [ ] `vencido_em`, `quantia`, `parcela_atual`, `parcela_total` vazios exibem
      "—" cada um, independentemente entre si — sem calcular fallback de
      `quantia` via soma de `valor_aluguel`/`valor_impostos`/`valor_seguros`/
      `valor_condominio`.
- [ ] Cada linha linka para `recibo_detail` do recibo correspondente.
- [ ] Botão "Novo Recibo" leva a `recibo_create_from_contrato` com
      `contrato.pk` correto na URL.
- [ ] Contrato sem nenhum recibo mostra o `empty-state` ("Nenhum recibo.").
- [ ] Visual conferido nos temas claro e escuro.
- [ ] `python manage.py check` sem erros.

# Riscos

- Posicionamento do card na coluna certa do layout (`row g-3` com colunas
  `col-md-5`/`col-md-7` ou similar) — conferir visualmente para não quebrar
  o grid responsivo existente.
