# Objetivo

Cobrir com testes automatizados o fluxo de persistência do histórico de
notificações: criação automática ao disparar `messages.*`, isolamento por
usuário, e limite de "últimas N" no context processor.

---

# Arquivos afetados

- `imoveis/tests.py` — nova classe de testes.

---

# Dependências

Depende de `01-modelo-notificacao-usuario`, `02-storage-captura-mensagens` e
`03-context-processor-sino` já implementados.

---

# Leituras adicionais

Nenhuma.

---

# Implementação

Seguir o padrão de `FluxoViewTests` (`imoveis/tests.py:403+`) — usa
`self.client` autenticado, dispara uma ação real de view (ex: criar um
Proprietário, que já emite `messages.success`) e valida o efeito colateral.

Casos a cobrir:

1. **Ação de CRUD existente cria `NotificacaoUsuario`** — ex: POST em
   `proprietario_create` (ou outra view simples já coberta por
   `FluxoViewTests`) e assertar que
   `NotificacaoUsuario.objects.filter(usuario=self.user).exists()` é
   `True`, com `nivel='success'` e `mensagem` não vazia.
2. **Isolamento por usuário** — criar `NotificacaoUsuario` para dois
   usuários distintos e assertar que a query de "últimas N" de um usuário
   não retorna registros do outro (testar diretamente
   `imoveis.context_processors.notificacoes_usuario` chamando a função com
   um `request` fake/`RequestFactory`, ou via `self.client.get()` em uma
   página qualquer e inspecionando `response.context`).
3. **Limite de N** — criar mais de `LIMITE_NOTIFICACOES_TOPBAR` registros
   para um usuário e assertar que `ultimas_notificacoes_usuario` no
   contexto tem exatamente `LIMITE_NOTIFICACOES_TOPBAR` itens, ordenados do
   mais recente para o mais antigo.
4. **Usuário anônimo não quebra** — `self.client.get()` sem login (ou
   `Client()` novo sem autenticar) em uma página pública (se houver) ou
   validar diretamente que a função do context processor retorna `{}` para
   `request.user` anônimo (usar `AnonymousUser` do
   `django.contrib.auth.models`).

Usar `RequestFactory` (`django.test.RequestFactory`) para os casos 2 e 4 se
for mais simples do que inspecionar `response.context`, seguindo o que já é
mais idiomático dado o restante da suíte (`self.client` é o padrão
predominante em `imoveis/tests.py` — preferir esse estilo quando possível).

---

# Critérios de aceite

- [ ] Teste cobrindo criação automática de `NotificacaoUsuario` a partir de
      uma chamada real de `messages.success` já existente em `views.py`.
- [ ] Teste cobrindo isolamento por usuário.
- [ ] Teste cobrindo limite de N no context processor.
- [ ] Teste cobrindo usuário anônimo sem erro.
- [ ] `venv/Scripts/python manage.py test imoveis` passa 100% (suíte
      completa, não só a classe nova — módulo 2 pode ter efeitos colaterais
      em testes existentes, confirmar que nada quebrou).

---

# Riscos

- Testes existentes em `FluxoViewTests` que já validam `messages` via
  `response.context['messages']` ou `get_messages()` não devem ser afetados
  — o storage novo é aditivo. Se algum teste falhar após o módulo 2, é sinal
  de premissa incorreta no plano (avisar o usuário, conforme instrução do
  prompt de implementação).
