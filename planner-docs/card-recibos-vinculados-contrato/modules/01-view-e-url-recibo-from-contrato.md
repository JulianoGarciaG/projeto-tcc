# Objetivo

Criar uma view nova `recibo_create_from_contrato(request, contrato_pk)` que
abre o formulário de criação de `Recibo` com `imovel` e `contrato`
pré-selecionados a partir de um `Contrato` existente, e a rota correspondente.

Não alterar a view `recibo_create` existente (continua servindo o botão
"+ Novo" genérico de `recibo_list`, sem pré-preenchimento).

# Arquivos afetados

- `imoveis/views.py` — nova view, próxima da seção `# Recibos` (perto de
  `recibo_create`, por volta da linha 800).
- `imoveis/urls.py` — nova rota, na seção `# Recibos` (ou junto da seção
  `# Contratos`, já que o path parameter é `contrato_pk` — usar o padrão de
  `notificacao_create`, que fica na seção do "pai" — aqui, seguir o mesmo
  raciocínio e colocar próximo às rotas de Contratos, com comentário
  `# Recibos por contrato`).

# Dependências

Nenhuma.

# Leituras adicionais

Nenhuma — os trechos relevantes de `imoveis/views.py` (`notificacao_create`,
`recibo_create`), `imoveis/forms.py` (`ReciboForm`) e `imoveis/urls.py` já
estão citados em `plan.md`.

# Implementação

Seguir literalmente o padrão de `notificacao_create`
(`imoveis/views.py:738-750`), adaptado para `Contrato`/`Recibo`:

```python
@login_required
def recibo_create_from_contrato(request, contrato_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    form = ReciboForm(request.POST or None,
                       initial={'imovel': contrato.imovel, 'contrato': contrato})
    form.fields['imovel'].initial = contrato.imovel
    form.fields['contrato'].initial = contrato
    if form.is_valid():
        recibo = form.save()
        messages.success(request, 'Recibo registrado com sucesso. Use "Regerar PDF" para gerar o documento.')
        return redirect('recibo_detail', pk=recibo.pk)
    return render(request, 'recibos/recibo_form.html', {'form': form, 'titulo': 'Novo Recibo'})
```

Note que `ReciboForm.__init__` não sobrescreve os campos `imovel`/`contrato`
(só troca widgets de campos monetários/data — ver `imoveis/forms.py:408-415`),
então o `initial` setado após a instanciação é preservado e o `<select>`
renderiza com a opção correta pré-selecionada, sem tocar em
`recibos/recibo_form.html`.

Rota nova em `imoveis/urls.py`, seguindo o padrão de path parameter dedicado
(mesmo estilo de `notificacao_create`):

```python
path('contratos/<int:contrato_pk>/recibos/novo/', views.recibo_create_from_contrato,
     name='recibo_create_from_contrato'),
```

# Critérios de aceite

- [ ] Acessar a URL `contratos/<pk>/recibos/novo/` com um `contrato_pk`
      válido renderiza `recibo_form.html` com os campos "Imóvel" e "Contrato"
      já selecionados com os valores corretos (visualmente, no `<select>`
      renderizado).
- [ ] `contrato_pk` inválido (contrato inexistente) retorna 404.
- [ ] Submeter o formulário com sucesso cria o `Recibo` normalmente e
      redireciona para `recibo_detail` do recibo criado, com a mensagem de
      sucesso padrão.
- [ ] `recibo_create` (rota `recibos/novo/`, sem contrato) continua
      funcionando sem nenhuma alteração de comportamento.
- [ ] `python manage.py check` sem erros.

# Riscos

- Reaproveitar `ReciboForm` sem alterações depende de `imovel`/`contrato`
  aceitarem `initial` via instância de model (`ImovelChoiceField`/
  `ContratoChoiceField`) — mesmo mecanismo já usado e validado por
  `notificacao_create`/`NotificacaoForm`, risco baixo.
