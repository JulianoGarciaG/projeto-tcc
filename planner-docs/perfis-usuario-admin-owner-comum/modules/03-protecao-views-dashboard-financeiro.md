# Objetivo

Proteger as 5 views que compoem as duas telas restritas (Dashboard e
Financeiro) com permission_required, para que o bloqueio exista mesmo por
acesso direto via URL - nunca depender so de esconder o link na sidebar
(isso e responsabilidade do modulo 4, complementar, nao substituto).

---

# Arquivos afetados

- imoveis/views.py - adicionar decorator em 5 views:
  - dashboard (linha ~91) -> pode_acessar_dashboard
  - lancamento_list, lancamento_create, lancamento_edit, lancamento_delete
    (linhas ~677-733) -> pode_acessar_financeiro

---

# Dependencias

Depende do modulo 01-modelo-permissao-host (os codenames
'imoveis.pode_acessar_dashboard' e 'imoveis.pode_acessar_financeiro' precisam
existir no banco - criados pela migration do modulo 1 + populados pela
migration de dados do modulo 2, ou pelo signal post_migrate padrao do
Django caso a migration do modulo 2 ainda nao tenha rodado em algum
ambiente).

---

# Leituras adicionais

Nenhuma.

---

# Implementacao

Importar o decorator:

```python
from django.contrib.auth.decorators import login_required, permission_required
```

Em cada uma das 5 views, empilhar os decorators nesta ordem exata (login_required
por fora, permission_required por dentro):

```python
@login_required
@permission_required('imoveis.pode_acessar_dashboard', raise_exception=True)
def dashboard(request):
    ...
```

```python
@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_list(request):
    ...

@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_create(request):
    ...

@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_edit(request, pk):
    ...

@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_delete(request, pk):
    ...
```

**Por que essa ordem de decorators**: com login_required por fora,
requisicoes anonimas continuam sendo redirecionadas para /login/ (LOGIN_URL,
comportamento ja existente, preservado). So depois de confirmar que o
usuario esta autenticado e que permission_required roda; com
raise_exception=True, um usuario autenticado sem a permissao recebe
PermissionDenied (403) em vez de ser redirecionado para /login/ (que seria o
comportamento padrao de permission_required sem raise_exception, e faria
pouco sentido para quem ja esta logado).

Superusers (Admin) sempre passam em qualquer permission_required,
independente de Group - comportamento nativo do
django.contrib.auth.backends.ModelBackend.has_perm().

---

# Criterios de aceite

- [ ] As 5 views listadas tem os dois decorators, na ordem especificada.
- [ ] Usuario anonimo acessando qualquer uma das 5 URLs e redirecionado
      para /login/ (nao muda em relacao ao comportamento atual).
- [ ] Usuario autenticado sem a permissao correspondente recebe 403 (nao
      um redirect, nao um 500) - validar manualmente ou via teste (modulo 5
      cobre isso formalmente).
- [ ] Usuario com a permissao (Owner ou superuser) acessa normalmente.
- [ ] `venv/Scripts/python manage.py check` sem erros.
- [ ] Suite de testes existente (`venv/Scripts/python manage.py test
      imoveis`) continua passando - testes que exercitam dashboard/
      lancamento_* hoje provavelmente usam um usuario comum sem permissoes
      especiais; se algum teste existente comecar a falhar com 403, o
      setUp desse teste precisa conceder a permissao/Group necessaria (nao
      remover o decorator para "consertar" o teste).

---

# Riscos

- Testes existentes que fazem POST/GET direto em dashboard ou
  financeiro/* com um usuario sem Group vao passar a receber 403 apos este
  modulo - varrer `imoveis/tests.py` por chamadas a `reverse('dashboard')`,
  `reverse('lancamento_list'|'lancamento_create'|'lancamento_edit'|'lancamento_delete')`
  e ajustar o setUp desses testes especificos para conceder a permissao
  (via `self.user.user_permissions.add(...)` ou adicionando o usuario ao
  Group Owner) - isso e responsabilidade deste modulo, nao pode ficar para
  o modulo 5 quebrar silenciosamente.
- **Caso concreto ja identificado** (nao e hipotetico): `DashboardFiltroTests`
  em imoveis/tests.py (~linha 949) cria um usuario comum sem nenhuma
  permissao no setUp e faz `self.client.get(reverse('dashboard'))` esperando
  200 em 3 testes. Apos este modulo, esses 3 testes vao falhar com 403 se
  nao ajustados. Corrigir concedendo a permissao no setUp dessa classe, por
  exemplo adicionando o usuario ao Group Owner ou usando
  `self.user.user_permissions.add(Permission.objects.get(codename='pode_acessar_dashboard'))`
  (import `from django.contrib.auth.models import Permission`).
