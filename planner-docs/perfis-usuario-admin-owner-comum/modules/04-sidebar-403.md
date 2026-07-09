# Objetivo

Refletir os 3 perfis na interface: ocultar os itens de sidebar Dashboard e
Financeiro para quem nao tem a permissao correspondente, atualizar o label
de perfil na topbar (hoje binario is_staff), e tratar acesso negado (403)
com uma pagina amigavel em vez de stack trace.

---

# Arquivos afetados

- templates/base.html - guardas na sidebar (itens Dashboard e Financeiro) e
  no label `user-role` da topbar.
- core/urls.py - registrar `handler403`.
- imoveis/views.py - nova view `erro_403`.
- templates/403.html - novo template.

---

# Dependencias

Depende do modulo 01-modelo-permissao-host (usa os codenames
pode_acessar_dashboard/pode_acessar_financeiro via `perms` nos templates).
Nao depende tecnicamente dos modulos 2 e 3, mas validacao manual completa
(ver a sidebar realmente ocultando Financeiro para um usuario Comum real)
fica mais facil com eles ja prontos.

---

# Leituras adicionais

Nenhuma.

---

# Sidebar (templates/base.html)

O item Dashboard (hoje linhas 42-45) e o item Financeiro (hoje linhas
77-81) ganham guarda `{% if perms.imoveis.<codename> %}`. `perms` ja esta
disponivel globalmente (context processor
django.contrib.auth.context_processors.auth ja ativo) - nao precisa de
context processor novo. Superusers sempre passam em qualquer `perms.*`
(bypass nativo do ModelBackend), entao Admin ve os dois itens
automaticamente sem tratamento especial.

```html
{% if perms.imoveis.pode_acessar_dashboard %}
<li class="nav-item">
  <a class="nav-link {% block nav_dashboard %}{% endblock %}" href="{% url 'dashboard' %}" title="Dashboard">
    <i class="bi bi-grid-1x2"></i> <span class="nav-text">Dashboard</span>
  </a>
</li>
{% endif %}
```

```html
{% if perms.imoveis.pode_acessar_financeiro %}
<li class="nav-item">
  <a class="nav-link {% block nav_financeiro %}{% endblock %}" href="{% url 'lancamento_list' %}" title="Financeiro">
    <i class="bi bi-graph-up-arrow"></i> <span class="nav-text">Financeiro</span>
  </a>
</li>
{% endif %}
```

A secao "Administracao" (`{% if user.is_staff %}`, linhas 96-103) **nao
muda** - Owner ja fica de fora por ter is_staff=False.

---

# Label de perfil na topbar (templates/base.html linha ~148)

Trocar a logica binaria atual:

```html
<div class="user-role">{% if user.is_staff %}Administrador{% else %}Usuario{% endif %}</div>
```

pela logica de 3 perfis, reaproveitando o mesmo `perms` ja usado na
sidebar (evita nova query/logica no backend):

```html
<div class="user-role">{% if user.is_superuser %}Administrador{% elif perms.imoveis.pode_acessar_dashboard %}Owner{% else %}Comum{% endif %}</div>
```

Um usuario sem Group e sem superuser cai no `{% else %}` (Comum) - reflete
o caso de borda descrito em plan.md sem precisar de membership explicita no
Group Comum para ser exibido corretamente.

---

# Handler 403

`PermissionDenied` levantado pelo `permission_required(raise_exception=True)`
(modulo 3) e roteado pelo handler403 do projeto - **nao e afetado por
DEBUG=True** (diferente de Http404, que so ganha pagina tecnica em DEBUG).

Em `imoveis/views.py`, adicionar:

```python
def erro_403(request, exception=None):
    return render(request, '403.html', status=403)
```

Em `core/urls.py`, registrar (nivel de modulo, fora de `urlpatterns`):

```python
handler403 = 'imoveis.views.erro_403'
```

---

# Template templates/403.html

Estender `base.html` (o usuario esta autenticado quando cai em 403 - so
falta a permissao de tela - entao sidebar/topbar continuam fazendo sentido).
Reaproveitar a classe `.empty-state` ja usada em varias listagens do
projeto (ex.: templates/imoveis/imovel_list.html) para o conteudo central,
mantendo consistencia visual sem CSS novo:

```html
{% extends 'base.html' %}
{% block title %}Acesso negado - Shelter{% endblock %}
{% block page_title %}Acesso negado{% endblock %}
{% block content %}
<div class="section-card">
  <div class="empty-state">
    <i class="bi bi-shield-lock"></i>
    Voce nao tem permissao para acessar esta pagina.
  </div>
</div>
{% endblock %}
```

Verificar se `.section-card` e a classe correta de wrapper usada pelas
outras telas do sistema antes de finalizar (conferir em qualquer template
de lista, ex.: imovel_list.html, ja lido durante o planejamento).

---

# Criterios de aceite

- [ ] Sidebar oculta Dashboard para quem nao tem pode_acessar_dashboard.
- [ ] Sidebar oculta Financeiro para quem nao tem pode_acessar_financeiro.
- [ ] Admin (superuser) ve os dois itens.
- [ ] Label de perfil na topbar mostra Administrador/Owner/Comum
      corretamente nos 3 casos.
- [ ] Acesso direto via URL sem permissao (ex.: usuario Comum acessando
      /financeiro/ diretamente) retorna HTTP 403 com o template
      templates/403.html renderizado - nunca stack trace, mesmo com
      DEBUG=True.
- [ ] `venv/Scripts/python manage.py check` sem erros.

---

# Riscos

- Se `handler403` for registrado com o nome errado de funcao/modulo, Django
  falha silenciosamente ao tentar resolver o handler so no momento em que um
  403 realmente acontece (nao no `check` nem no startup) - testar
  manualmente pelo menos uma vez o fluxo de 403 (nao so confiar no
  `manage.py check`).
- `erro_403` precisa aceitar o parametro `exception` (Django sempre passa
  esse argumento para handlers 403/404/500) mesmo que nao seja usado.
