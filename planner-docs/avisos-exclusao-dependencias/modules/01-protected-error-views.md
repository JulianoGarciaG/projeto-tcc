# Objetivo

Tratar `ProtectedError` em `imovel_delete`, `proprietario_delete` e
`inquilino_delete`, seguindo exatamente o padrão já usado em
`contrato_delete` (`imoveis/views.py`, linha ~461): capturar a exceção,
mostrar mensagem de erro amigável via `messages.error`, e redirecionar sem
deixar o erro 500 vazar.

---

# Arquivos afetados

- `imoveis/views.py` — três views:
  - `imovel_delete` (linha ~258)
  - `proprietario_delete` (linha ~302)
  - `inquilino_delete` (linha ~345)

---

# Dependências

Nenhuma. `ProtectedError` já está importado em `imoveis/views.py` (linha 5).

---

# Leituras adicionais

Nenhuma.

---

# Detalhamento

`contrato_delete` (já implementado, referência exata a seguir — não copiar
verbatim, adaptar mensagem e redirect por model):

```python
@login_required
def contrato_delete(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este contrato não pode ser excluído: há laudos de vistoria '
                                    'ou recibos vinculados a ele. Exclua-os primeiro.')
            return redirect('contrato_detail', pk=pk)
        messages.success(request, 'Contrato removido.')
    return redirect('contrato_list')
```

Aplicar o mesmo padrão às três views abaixo. Diferença importante: **não
existe `proprietario_detail` nem `inquilino_detail`** — portanto, ao
capturar `ProtectedError`, o redirect de bloqueio (assim como o de sucesso)
é sempre para a própria `_list`. `Imovel` também não tem uma rota melhor de
retorno em caso de bloqueio além de `imovel_list` (o `imovel_detail`
existe, mas mantenha o redirect para `imovel_list` para não introduzir
comportamento divergente do restante do CRUD de imóvel — as demais views
de imóvel já redirecionam para `imovel_list` ou `imovel_detail`
dependendo do caso; aqui, como a exclusão parte da listagem, redirecionar
para `imovel_list` mantém consistência com o fluxo atual).

## `imovel_delete`

```python
@login_required
def imovel_delete(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    if request.method == 'POST':
        try:
            imovel.delete()
        except ProtectedError:
            messages.error(request, 'Este imóvel não pode ser excluído: há contratos '
                                    'ou recibos vinculados a ele. Exclua-os primeiro.')
            return redirect('imovel_list')
        messages.success(request, 'Imóvel removido.')
    return redirect('imovel_list')
```

## `proprietario_delete`

```python
@login_required
def proprietario_delete(request, pk):
    obj = get_object_or_404(Proprietario, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este proprietário não pode ser excluído: possui '
                                    'imóveis vinculados. Exclua-os primeiro.')
            return redirect('proprietario_list')
        messages.success(request, 'Proprietário removido.')
    return redirect('proprietario_list')
```

## `inquilino_delete`

```python
@login_required
def inquilino_delete(request, pk):
    obj = get_object_or_404(Inquilino, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este inquilino não pode ser excluído: possui '
                                    'contratos vinculados. Exclua-os primeiro.')
            return redirect('inquilino_list')
        messages.success(request, 'Inquilino removido.')
    return redirect('inquilino_list')
```

Observação: nas três views, `messages.success` deve ficar **dentro** do
`try/except` do jeito mostrado (após a linha do `.delete()`, mas fora do
bloco `except`), exatamente como em `contrato_delete` — se o `.delete()`
lançar `ProtectedError`, o fluxo já retorna dentro do `except` e a
mensagem de sucesso nunca é atingida.

---

# Critérios de aceite

- [ ] `imovel_delete`, `proprietario_delete`, `inquilino_delete` capturam
      `ProtectedError` e chamam `messages.error` com mensagem específica do
      model antes de redirecionar.
- [ ] Nenhuma das três views deixa `ProtectedError` propagar (sem erro 500).
- [ ] Redirect em caso de bloqueio é para a respectiva `_list` (não existe
      `_detail` para Proprietario/Inquilino; Imovel mantém `imovel_list` por
      consistência).
- [ ] `messages.success` só é exibida quando a exclusão realmente ocorre.
- [ ] `venv/Scripts/python manage.py check` roda sem erros.

---

# Riscos

- Nenhum risco de regressão de schema (mudança é só em views). Risco baixo
  de esquecer alguma das três views ou inverter a ordem
  `try/except`/`messages.success`.
