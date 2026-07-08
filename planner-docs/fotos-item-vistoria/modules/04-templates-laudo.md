# Objetivo

Adicionar o input de upload múltiplo em cada linha do formset de itens
(create/edit) e exibir a galeria de fotos agrupada por item no detalhe do
laudo — sem tocar no template do PDF nem na central GED.

---

# Arquivos afetados

- `templates/laudos/laudo_form.html`
- `templates/laudos/laudo_detail.html`

Nenhuma alteração em `templates/documentos/laudo_pdf.html`,
`templates/documentos/base_pdf.html` ou `templates/ged/documentos.html`
(RF4/RF5) — isso é intencional, não um esquecimento.

---

# Dependências

- `02-form-widget-multiplo-arquivo` (campo `fotos` do `ItemVistoriaForm`).
- `03-views-laudo` (fotos prefetchadas em `laudo.itens` no contexto do
  detail).

---

# Leituras adicionais

Nenhuma.

---

# Alterações

## `laudo_form.html`

1. O `<form>` principal (linha 37) **precisa** ganhar
   `enctype="multipart/form-data"` — hoje não tem, porque nenhum campo desse
   form fazia upload:

   ```html
   <form method="post" enctype="multipart/form-data" novalidate>
   ```

2. Na linha do checklist (linhas 72-81), adicionar uma célula com o input de
   `f.fotos`. Como a tabela já tem 4 colunas (Item/Estado/Observação/Del),
   adicionar uma 5ª coluna (cabeçalho na linha 70 também precisa da coluna
   nova):

   ```html
   <tr class="col-head"><th style="width:35%;">Item</th><th style="width:20%;">Estado</th><th>Observação</th><th style="width:15%;">Fotos</th><th style="width:5%;"></th></tr>
   ```

   ```html
   <tr>
     <td>{{ f.item.value }}{{ f.comodo }}{{ f.item }}{{ f.ordem }}{{ f.id }}</td>
     <td><div class="seg-estado-wrap">{{ f.estado }}</div></td>
     <td>{{ f.observacao }}</td>
     <td>{{ f.fotos }}</td>
     <td>
       {% if f.instance.pk %}
       <div class="form-check">{{ f.DELETE }}<label class="form-check-label small text-danger" for="{{ f.DELETE.id_for_label }}">Del</label></div>
       {% endif %}
     </td>
   </tr>
   ```

3. Bloco de erros (linha 128-134) já itera todos os campos de cada `f` no
   `item_formset` (`{% for field in f %}`) — erros do campo `fotos` (ex.
   imagem inválida) já aparecem automaticamente, nenhuma mudança necessária
   ali.

## `laudo_detail.html`

Na tabela de "Cômodos e Itens Vistoriados" (linhas 108-125), adicionar a
galeria de fotos do item logo abaixo da linha existente, só quando houver
fotos:

```html
{% for item in grupo.itens %}
<tr>
  <td>{{ item.item }}</td>
  <td>
    <span class="status-badge {% if item.estado == 'bom' %}badge-ok{% elif item.estado == 'regular' %}badge-warn{% else %}badge-danger{% endif %}">{{ item.get_estado_display }}</span>
  </td>
  <td class="text-muted">{{ item.observacao|default:"—" }}</td>
</tr>
{% if item.fotos.all %}
<tr>
  <td colspan="3" class="pt-0">
    <div class="d-flex flex-wrap gap-2">
      {% for foto in item.fotos.all %}
      <a href="{{ foto.imagem.url }}" target="_blank">
        <img src="{{ foto.imagem.url }}" alt="Foto de {{ item.item }}" class="rounded border" style="width:64px;height:64px;object-fit:cover;">
      </a>
      {% endfor %}
    </div>
  </td>
</tr>
{% endif %}
{% endfor %}
```

`item.fotos.all` usa o `related_name='fotos'` do model `FotoItemVistoria`
(módulo `01`) e reaproveita o prefetch feito em `laudo_detail`
(`itens__fotos`, módulo `03`) — sem consultas extras por item.

---

# Critérios de aceite

- [ ] Formulário de laudo (create e edit) envia arquivos corretamente —
      `enctype="multipart/form-data"` presente.
- [ ] Cada linha do checklist tem um input de arquivo múltiplo funcional
      (`multiple`, `accept="image/*"`).
- [ ] Detalhe do laudo exibe as fotos de cada item, agrupadas visualmente
      logo abaixo da linha do item, só quando existirem.
- [ ] Sem fotos, o layout do detalhe permanece idêntico ao atual (nenhuma
      linha extra vazia).
- [ ] Testado visualmente em tema claro **e** escuro (convenção do
      CLAUDE.md) — usar apenas classes/tokens já usados no restante do
      template (`rounded`, `border`, sem hex fixo).
- [ ] `templates/documentos/laudo_pdf.html` e `templates/ged/documentos.html`
      permanecem sem nenhuma referência a `FotoItemVistoria`/`fotos`.

---

# Riscos

- Adicionar uma coluna na tabela do formulário pode apertar o layout em
  telas pequenas — a tabela já está dentro de `.table-responsive`
  (`laudo_form.html:64`), então terá scroll horizontal no mobile; aceitável,
  mesmo padrão já usado nas outras tabelas do sistema.
- Miniaturas grandes ou em excesso (sem paginação/lightbox) podem poluir o
  detalhe se um item tiver muitas fotos — aceitável nesta rodada (sem
  limite de quantidade, conforme suposição validada no objetivo da
  feature); registrar como possível ajuste futuro de UX, não bloqueador.
