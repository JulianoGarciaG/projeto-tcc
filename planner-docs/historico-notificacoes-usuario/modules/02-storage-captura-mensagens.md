# Objetivo

Persistir automaticamente, em `NotificacaoUsuario`, toda mensagem que hoje é
emitida via `django.contrib.messages` (`success`/`error`/`warning`/`info`),
sem editar nenhuma das ~36 chamadas existentes em `imoveis/views.py`. A
captura acontece em um único ponto central: um storage backend customizado do
Django messages framework.

---

# Arquivos afetados

- `imoveis/message_storage.py` (novo arquivo).
- `core/settings.py` — adicionar `MESSAGE_STORAGE`.

---

# Dependências

Depende do módulo `01-modelo-notificacao-usuario` (usa o model
`NotificacaoUsuario`).

---

# Leituras adicionais

Nenhuma.

---

# Contexto técnico (por que este mecanismo)

O Django messages framework não expõe um signal nativo para "mensagem
adicionada". A única forma central de interceptar todas as chamadas
`messages.success/error/warning/info(request, ...)` sem tocar em cada call
site é substituir a classe de storage configurada em `MESSAGE_STORAGE`
(`settings.py`), que por padrão é
`django.contrib.messages.storage.fallback.FallbackStorage`. Toda chamada
`messages.add(...)` (e os atalhos `success`/`error`/etc, que só chamam
`add` com o `level` correspondente) passa pelo método `add()` da instância
de storage retornada por `get_messages_storage_class()`/`request._messages`.

O middleware `django.contrib.messages.middleware.MessageMiddleware` já roda
depois de `AuthenticationMiddleware` (`core/settings.py:25-33`), então
`request.user` está disponível quando o storage é instanciado por request.

---

# Implementação

```python
# imoveis/message_storage.py
from django.contrib.messages import constants
from django.contrib.messages.storage.fallback import FallbackStorage

from imoveis.models import NotificacaoUsuario

_NIVEL_POR_LEVEL = {
    constants.SUCCESS: 'success',
    constants.ERROR: 'error',
    constants.WARNING: 'warning',
    constants.INFO: 'info',
    constants.DEBUG: 'info',
}


class PersistentFallbackStorage(FallbackStorage):
    """FallbackStorage padrão do Django + persistência em NotificacaoUsuario.

    Não altera o comportamento de exibição dos toasts (base.html continua
    consumindo request._messages normalmente) — apenas grava uma cópia
    permanente por usuário autenticado.
    """

    def add(self, level, message, extra_tags=''):
        super().add(level, message, extra_tags=extra_tags)
        user = getattr(self.request, 'user', None)
        if user is not None and user.is_authenticated and message:
            NotificacaoUsuario.objects.create(
                usuario=user,
                mensagem=message,
                nivel=_NIVEL_POR_LEVEL.get(level, 'info'),
            )
```

Em `core/settings.py`, adicionar (próximo a outras configurações de app,
mantendo o estilo do arquivo):

```python
MESSAGE_STORAGE = 'imoveis.message_storage.PersistentFallbackStorage'
```

---

# Critérios de aceite

- [ ] `imoveis/message_storage.py` criado com `PersistentFallbackStorage`.
- [ ] `MESSAGE_STORAGE` configurado em `core/settings.py`.
- [ ] Qualquer `messages.success/error/warning(request, "...")` já existente
      em `imoveis/views.py` passa a criar um `NotificacaoUsuario` quando o
      usuário está autenticado — validar manualmente (ex: cadastrar um
      imóvel e checar `NotificacaoUsuario.objects.last()`), sem editar
      `views.py`.
- [ ] Toasts em `base.html` continuam aparecendo normalmente (comportamento
      de exibição não foi alterado).
- [ ] Mensagens emitidas para usuário anônimo (se houver, ex: fluxo de
      login) não geram erro — `add()` deve lidar com `user.is_authenticated`
      `False` sem quebrar.
- [ ] `venv/Scripts/python manage.py check` sem erros.

---

# Riscos

- Import de `imoveis.models` dentro de `message_storage.py`: como
  `MESSAGE_STORAGE` é resolvido cedo no ciclo de request, garantir que não
  há import circular (o módulo `imoveis/models.py` não importa
  `message_storage.py`, então não há risco real, mas validar com `check`).
- Se `message` vier vazio ou `None` em algum ponto do Django internamente,
  o `if message` evita criar registro vazio.
- Testes existentes que usam `self.client` autenticado e disparam mensagens
  passam a gerar `NotificacaoUsuario` como efeito colateral — não deve
  quebrar nenhum teste existente (storage é aditivo, não substitui o
  comportamento padrão). Rodar a suíte completa ao final para confirmar.
