# Objetivo

Salvar as fotos enviadas em cada linha do formset de itens (`item_formset`)
como `FotoItemVistoria`, em `laudo_create` e `laudo_edit`; e prefetchar as
fotos no `laudo_detail` para exibição agrupada por item (módulo `04`).

---

# Arquivos afetados

- `imoveis/views.py`:
  - `laudo_create` (`imoveis/views.py:543-569`)
  - `laudo_edit` (`imoveis/views.py:573-592`)
  - `laudo_detail` (`imoveis/views.py:530-539`)

---

# Dependências

- `01-model-foto-item-vistoria` (usa o model `FotoItemVistoria`).
- `02-form-widget-multiplo-arquivo` (usa `ItemVistoriaForm.cleaned_data['fotos']`).

---

# Leituras adicionais

Nenhuma além do já referenciado em plan.md (trechos de
`imoveis/views.py:40-59` e `521-592` já foram investigados pelo Planner e
estão descritos abaixo).

---

# Especificação

## 1. Import

Adicionar `FotoItemVistoria` ao import de `.models` no topo de
`imoveis/views.py` (mesmo import que já traz `ItemVistoria`).

## 2. Helper de gravação (novo, privado)

Criar uma função auxiliar reaproveitada por `laudo_create` e `laudo_edit`,
próxima a `_itens_agrupados` (`imoveis/views.py:40`):

```python
def _salvar_fotos_itens(item_formset):
    """Roda depois de item_formset.save(): mapeia os arquivos enviados em
    cada linha do formset para o ItemVistoria já persistido (precisa de PK).
    Linhas puladas (extra sem mudança) não têm cleaned_data — ignorar."""
    for f in item_formset.forms:
        cleaned = getattr(f, 'cleaned_data', None)
        if not cleaned or cleaned.get('DELETE'):
            continue
        instance = f.instance
        if not instance.pk:
            continue
        arquivos = cleaned.get('fotos') or []
        if arquivos:
            FotoItemVistoria.objects.bulk_create(
                FotoItemVistoria(item=instance, imagem=arquivo) for arquivo in arquivos
            )
```

## 3. `laudo_create` — passar `request.FILES` e chamar o helper após salvar

Trecho atual (`imoveis/views.py:548-561`):

```python
if request.method == 'POST':
    form = LaudoVistoriaForm(request.POST)
    item_formset = CatalogoFormSet(request.POST, prefix='itens', initial=catalogo)
    testemunha_formset = TestemunhaFormSet(request.POST, prefix='testemunhas')
    if form.is_valid() and item_formset.is_valid() and testemunha_formset.is_valid():
        laudo = form.save()
        item_formset.instance = laudo
        item_formset.save()
        testemunha_formset.instance = laudo
        testemunha_formset.save()
```

Alterar para passar `request.FILES` em `item_formset` (obrigatório — sem
isso o Django ignora os arquivos enviados) e chamar
`_salvar_fotos_itens(item_formset)` **depois** de `item_formset.save()`:

```python
item_formset = CatalogoFormSet(request.POST, request.FILES, prefix='itens', initial=catalogo)
...
    laudo = form.save()
    item_formset.instance = laudo
    item_formset.save()
    _salvar_fotos_itens(item_formset)
    testemunha_formset.instance = laudo
    testemunha_formset.save()
```

## 4. `laudo_edit` — mesma alteração

Trecho atual (`imoveis/views.py:575-582`):

```python
item_formset = ItemVistoriaFormSet(request.POST, instance=obj, prefix='itens')
...
    laudo = form.save()
    item_formset.save()
    testemunha_formset.save()
```

Alterar para:

```python
item_formset = ItemVistoriaFormSet(request.POST, request.FILES, instance=obj, prefix='itens')
...
    laudo = form.save()
    item_formset.save()
    _salvar_fotos_itens(item_formset)
    testemunha_formset.save()
```

## 5. `laudo_detail` — prefetch das fotos

Trecho atual (`imoveis/views.py:531-533`):

```python
laudo = get_object_or_404(
    LaudoVistoria.objects.select_related('imovel__proprietario', 'contrato__inquilino'), pk=pk)
```

Adicionar `.prefetch_related('itens__fotos')` à mesma queryset (evita N+1 ao
renderizar a galeria por item no template do módulo `04`, já que
`_itens_agrupados` chama `laudo.itens.all()` internamente):

```python
laudo = get_object_or_404(
    LaudoVistoria.objects.select_related('imovel__proprietario', 'contrato__inquilino')
    .prefetch_related('itens__fotos'), pk=pk)
```

---

# Critérios de aceite

- [ ] `laudo_create` e `laudo_edit` passam `request.FILES` ao formset de
      itens.
- [ ] `_salvar_fotos_itens` é chamada **depois** de `item_formset.save()`
      em ambas as views (create e edit).
- [ ] Enviar 1+ fotos numa linha com `estado` preenchido cria os registros
      `FotoItemVistoria` corretos (uma foto por arquivo enviado,
      `item_id` correto).
- [ ] Enviar fotos numa linha do laudo **novo** sem selecionar `estado`
      produz erro de validação (`estado` obrigatório) e **não** salva o
      laudo nem as fotos — comportamento esperado, não é bug (ver riscos).
- [ ] `laudo_detail` renderiza sem N+1 perceptível (prefetch aplicado).
- [ ] Nenhuma foto é anexada a `DocumentoGerado`, nem passa por
      `imoveis/pdf.py:gerar_e_anexar` — este módulo não toca `pdf.py`.

---

# Riscos

- **Interação com a regra "linha vazia é ignorada" (L4).** Anexar foto a uma
  linha nova (create) sem escolher `estado` faz `ItemVistoriaForm.has_changed()`
  retornar `True` (o campo `fotos` mudou em relação ao `initial` vazio), o
  que tira a linha do modo "ignorada" e força a validação normal do
  `ModelForm` — que exige `estado` (campo obrigatório do model
  `ItemVistoria`). Resultado: o usuário recebe um erro de validação pedindo
  o `estado` daquela linha, e o POST inteiro falha (nada é salvo, nem o
  laudo, nem os itens, nem as fotos) — mesmo comportamento que já existe
  hoje para qualquer outro erro de formset. **Não implementar nenhum
  contorno para isso** — é a extensão natural da regra de negócio existente
  (só é vistoriado, e portanto só ganha foto, o item que tem estado). Deixar
  explícito no teste (`05-tests`).
- Erro ao salvar uma imagem inválida (arquivo corrompido) em
  `FotoItemVistoria.objects.bulk_create` só seria pego na gravação no banco,
  não antes — `bulk_create` não roda `full_clean()`. Se isso for um problema
  em produção, é trabalho futuro adicionar validação de imagem antes do
  `bulk_create` (ex. `Image.open(...).verify()`); não bloquear esta rodada
  por isso, mas registrar a limitação.
- `bulk_create` não dispara `save()` por instância — se no futuro
  `FotoItemVistoria` ganhar lógica em `save()` (ex. redimensionar imagem),
  trocar para loop de `.save()` individual.
