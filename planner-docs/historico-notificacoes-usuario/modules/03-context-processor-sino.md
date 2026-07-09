# Objetivo

Disponibilizar as últimas N notificações do usuário logado em todo template
que estende `base.html`, via context processor, para alimentar o dropdown do
sino (implementado no módulo 4).

---

# Arquivos afetados

- `imoveis/context_processors.py` (novo arquivo).
- `core/settings.py` — registrar o context processor em
  `TEMPLATES[0]['OPTIONS']['context_processors']`.

---

# Dependências

Depende do módulo `01-modelo-notificacao-usuario` (faz a query em
`NotificacaoUsuario`).

---

# Leituras adicionais

Nenhuma.

---

# Implementação

`N = 8`, seguindo o precedente de `ultimos_lancamentos` no dashboard
(`imoveis/views.py:124`, slicing simples, sem `Paginator`).

```python
# imoveis/context_processors.py
LIMITE_NOTIFICACOES_TOPBAR = 8


def notificacoes_usuario(request):
    """Últimas notificações do usuário logado, para o dropdown do sino na
    topbar (templates/base.html). Sem paginação, sem estado lida/não lida.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    ultimas = user.notificacoes.all()[:LIMITE_NOTIFICACOES_TOPBAR]
    return {'ultimas_notificacoes_usuario': ultimas}
```

Em `core/settings.py`, dentro de `TEMPLATES[0]['OPTIONS']['context_processors']`,
adicionar `'imoveis.context_processors.notificacoes_usuario'` à lista já
existente (os 3 padrões do Django).

---

# Critérios de aceite

- [ ] `imoveis/context_processors.py` criado com `notificacoes_usuario`.
- [ ] Registrado em `TEMPLATES` de `core/settings.py`.
- [ ] Variável `ultimas_notificacoes_usuario` disponível em qualquer template
      renderizado com `RequestContext` (todas as views do projeto usam
      `render()`, então isso cobre o app inteiro).
- [ ] Usuário anônimo (ex: tela de login) não quebra — context processor
      retorna dict vazio nesse caso.
- [ ] `venv/Scripts/python manage.py check` sem erros.

---

# Riscos

- `related_name='notificacoes'` definido no módulo 1 — se o nome for
  alterado lá, ajustar `user.notificacoes.all()` aqui. Conferir antes de
  implementar.
- Rodar em toda request tem custo de 1 query extra por página — aceitável
  dado o volume esperado do sistema (uso interno, poucos usuários
  simultâneos); não otimizar prematuramente (ex: cache) fora de escopo.
